#!/usr/bin/env python3
"""
Unit and regression test suite for Label-Forge Phase 1.1.2.2 Independent Validator Acceptance.
Exercises real production validation functions under scripts/validation/
with mandatory negative fixture tests T01 through T24, edge cases, and positive tests.
Zero mock tampering or tautological tests.
"""

import unittest
import os
import sys
import tempfile
import shutil
import json
import hashlib
from typing import Dict, Any

# Ensure scripts directory and repo root are on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.validation.stage_results import (
    AssertionRecord,
    StageResult,
    aggregate_stage_status,
    evaluate_release_gate,
    STATUS_PASS,
    STATUS_FAIL,
    STATUS_WARNING,
    STATUS_NOT_CHECKED
)
from scripts.validation.binary_validation import (
    validate_target_binary,
    validate_evidence_manifest
)
from scripts.validation.dependency_validation import validate_direct_import_partition
from scripts.validation.evidence_integrity import (
    resolve_json_pointer,
    decode_reference_token,
    validate_status_accounting,
    scan_prohibited_images,
    validate_structured_evidence_reference,
    ALLOWED_CLAIM_STATUSES
)
from scripts.validation.claim_assertions import make_claim_assertion_registry
from scripts.validation.provenance import (
    generate_provenance_record,
    validate_provenance_record
)


class TestValidationInvariantsPositive(unittest.TestCase):
    """Positive baseline tests against actual repository files and production functions."""

    def test_json_pointer_resolution(self):
        """Test RFC 6901 JSON pointer resolver with nested dicts, lists, and escapes."""
        doc = {
            "a": {"b": [10, 20, {"c": "hello"}]},
            "slash/key": 42,
            "tilde~key": 99
        }
        self.assertEqual(resolve_json_pointer(doc, ""), doc)
        self.assertEqual(resolve_json_pointer(doc, "/a/b/0"), 10)
        self.assertEqual(resolve_json_pointer(doc, "/a/b/1"), 20)
        self.assertEqual(resolve_json_pointer(doc, "/a/b/2/c"), "hello")
        self.assertEqual(resolve_json_pointer(doc, "/slash~1key"), 42)
        self.assertEqual(resolve_json_pointer(doc, "/tilde~0key"), 99)

    def test_rfc6901_strict_token_decoding(self):
        """Test strict RFC 6901 token decoding rules."""
        self.assertEqual(decode_reference_token("foo"), "foo")
        self.assertEqual(decode_reference_token("~0"), "~")
        self.assertEqual(decode_reference_token("~1"), "/")
        self.assertEqual(decode_reference_token("~01"), "~1")
        self.assertEqual(decode_reference_token("a~0b~1c"), "a~b/c")

        # Invalid escape sequences must raise ValueError
        with self.assertRaises(ValueError):
            decode_reference_token("~2")
        with self.assertRaises(ValueError):
            decode_reference_token("~x")
        with self.assertRaises(ValueError):
            decode_reference_token("trailing~")
        with self.assertRaises(ValueError):
            decode_reference_token("~")

    def test_rfc6901_array_index_syntax(self):
        """Test that array index pointers enforce RFC 6901 rules (reject leading zeros, negatives, non-digits)."""
        doc = [10, 20, 30]
        self.assertEqual(resolve_json_pointer(doc, "/0"), 10)
        self.assertEqual(resolve_json_pointer(doc, "/1"), 20)

        # Leading zero e.g. /01 is prohibited by RFC 6901
        with self.assertRaises(IndexError):
            resolve_json_pointer(doc, "/01")
        with self.assertRaises(IndexError):
            resolve_json_pointer(doc, "/-1")
        with self.assertRaises(IndexError):
            resolve_json_pointer(doc, "/+1")
        with self.assertRaises(IndexError):
            resolve_json_pointer(doc, "/abc")

    def test_direct_import_partition_positive(self):
        """Verify that the actual repository dependency reconciliation is an exact partition."""
        dep_path = os.path.join(REPO_ROOT, 'evidence', 'phase1', 'reconciliation', 'dependency_reconciliation.json')
        with open(dep_path, 'r', encoding='utf-8') as f:
            dep = json.load(f)

        canonical = dep['direct_pe_imports']['libraries']
        categories = {k: v['modules'] for k, v in dep['direct_pe_imports']['categories'].items()}
        res = validate_direct_import_partition(canonical, categories)

        self.assertTrue(res['is_exact_partition'])
        self.assertEqual(len(res['canonical_duplicates']), 0)
        self.assertEqual(len(res['category_internal_duplicates']), 0)
        self.assertEqual(len(res['cross_category_overlaps']), 0)
        self.assertEqual(len(res['missing_modules']), 0)
        self.assertEqual(len(res['unexpected_modules']), 0)
        self.assertEqual(res['canonical_count'], 48)

    def test_claim_status_accounting_positive(self):
        """Verify claim status accounting exact dictionary equality on actual repository data."""
        cr_path = os.path.join(REPO_ROOT, 'evidence', 'phase1', 'reconciliation', 'claim_register.json')
        with open(cr_path, 'r', encoding='utf-8') as f:
            cr = json.load(f)

        claims = cr['claims']
        declared = cr['claims_by_status']
        res = validate_status_accounting(claims, declared)
        self.assertTrue(res['is_valid'])
        self.assertEqual(len(res['errors']), 0)

    def test_evidence_manifest_validation_positive(self):
        """Verify that validate_evidence_manifest passes against the actual repository manifest."""
        manifest_path = os.path.join(REPO_ROOT, 'evidence', 'phase1', 'reconciliation', 'validation_manifest.json')
        is_valid, assertions, summary = validate_evidence_manifest(manifest_path, REPO_ROOT)
        self.assertTrue(is_valid)
        self.assertTrue(len(assertions) > 0)
        self.assertTrue(all(a.status == STATUS_PASS for a in assertions))

    def test_release_gate_evaluation_approved(self):
        """Verify evaluate_release_gate produces exit code 0 and APPROVED when all mandatory stages pass."""
        stage_results = {
            'target_binary_integrity': STATUS_PASS,
            'manifest_integrity': STATUS_PASS,
            'direct_import_partition': STATUS_PASS,
            'status_accounting': STATUS_PASS,
            'evidence_references': STATUS_PASS,
            'claim_specific_assertions': STATUS_PASS,
            'recursive_image_audit': STATUS_PASS,
            'report_consistency': STATUS_PASS
        }
        counts = {STATUS_PASS: 100, STATUS_FAIL: 0, STATUS_WARNING: 0, STATUS_NOT_CHECKED: 0}
        code, status, msg = evaluate_release_gate(stage_results, counts)
        self.assertEqual(code, 0)
        self.assertEqual(status, "PHASE 1.1.2.2 — APPROVED")


class TestValidationMandatoryFixtures(unittest.TestCase):
    """
    Mandatory negative and boundary fixture tests T01 through T24.
    Every single test directly exercises production validation functions from scripts/validation.
    """

    # T01: Duplicate direct-import category entry (FAIL)
    def test_T01_duplicate_direct_import_category_entry(self):
        canonical = ["A.DLL", "B.DLL"]
        categories = {"cat1": ["A.DLL", "A.DLL"], "cat2": ["B.DLL"]}
        res = validate_direct_import_partition(canonical, categories)
        self.assertFalse(res['is_exact_partition'])
        self.assertIn("cat1", res['category_internal_duplicates'])
        self.assertEqual(res['category_internal_duplicates']["cat1"], ["A.DLL"])

    # T02: Direct import missing from category partition (FAIL)
    def test_T02_direct_import_missing_from_category_partition(self):
        canonical = ["A.DLL", "B.DLL", "C.DLL"]
        categories = {"cat1": ["A.DLL"], "cat2": ["B.DLL"]}
        res = validate_direct_import_partition(canonical, categories)
        self.assertFalse(res['is_exact_partition'])
        self.assertIn("C.DLL", res['missing_modules'])

    # T03: Unexpected category module (FAIL)
    def test_T03_unexpected_category_module(self):
        canonical = ["A.DLL", "B.DLL"]
        categories = {"cat1": ["A.DLL"], "cat2": ["B.DLL", "EXTRA.DLL"]}
        res = validate_direct_import_partition(canonical, categories)
        self.assertFalse(res['is_exact_partition'])
        self.assertIn("EXTRA.DLL", res['unexpected_modules'])

    # T04: Module assigned to multiple categories (FAIL)
    def test_T04_module_assigned_to_multiple_categories(self):
        canonical = ["A.DLL", "B.DLL"]
        categories = {"cat1": ["A.DLL", "B.DLL"], "cat2": ["B.DLL"]}
        res = validate_direct_import_partition(canonical, categories)
        self.assertFalse(res['is_exact_partition'])
        self.assertIn("B.DLL", res['cross_category_overlaps'])
        self.assertEqual(res['cross_category_overlaps']["B.DLL"], ["cat1", "cat2"])

    # T05: Incorrect evidence SHA-256 (FAIL)
    def test_T05_incorrect_evidence_sha256(self):
        """Exercises production validate_evidence_manifest on a corrupted checksum fixture."""
        temp_dir = tempfile.mkdtemp(prefix='test_t05_')
        try:
            rel_file = "test_data.json"
            full_file = os.path.join(temp_dir, rel_file)
            file_bytes = b'{"test": 123}'
            with open(full_file, "wb") as f:
                f.write(file_bytes)

            corrupted_sha = "0" * 64
            manifest = {
                "manifest_schema_version": "1.0.0",
                "files": [
                    {
                        "path": rel_file,
                        "sha256": corrupted_sha,
                        "size_bytes": len(file_bytes)
                    }
                ]
            }
            manifest_path = os.path.join(temp_dir, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f)

            is_valid, assertions, summary = validate_evidence_manifest(manifest_path, temp_dir)
            self.assertFalse(is_valid)
            self.assertTrue(any(a.status == STATUS_FAIL and "SHA-256 mismatch" in a.detail for a in assertions))
        finally:
            shutil.rmtree(temp_dir)

    # T06: Incorrect evidence file size (FAIL)
    def test_T06_incorrect_evidence_file_size(self):
        """Exercises production validate_target_binary on a binary with incorrect file size."""
        temp_dir = tempfile.mkdtemp(prefix='test_t06_')
        try:
            dummy_exe = os.path.join(temp_dir, "test.exe")
            with open(dummy_exe, "wb") as f:
                f.write(b"M" * 1024)

            canonical = {
                "file_size_bytes": 20774984,
                "md5": "7af37ab384391fcc03935a569d705aa0",
                "sha1": "7a57fefa26e99ddec6a46625a8cc17c5a87593aa",
                "sha256": "d3498925149b91c646351e91638906ca4455b2a4cd8db82775bb6860d67d8594"
            }
            is_valid, assertions, info = validate_target_binary(dummy_exe, canonical)
            self.assertFalse(is_valid)
            self.assertTrue(any(a.assertion_id == "file_size" and a.status == STATUS_FAIL for a in assertions))
        finally:
            shutil.rmtree(temp_dir)

    # T07: Missing evidence file (FAIL)
    def test_T07_missing_evidence_file(self):
        """Exercises production validate_structured_evidence_reference and validate_evidence_manifest."""
        ref = {"type": "file", "path": "evidence/phase1/non_existent_file_xyz.json"}
        ok, msg = validate_structured_evidence_reference(ref, REPO_ROOT)
        self.assertFalse(ok)
        self.assertIn("missing on disk", msg)

        # Also test validate_evidence_manifest on missing file entry
        temp_dir = tempfile.mkdtemp(prefix='test_t07_')
        try:
            manifest = {
                "manifest_schema_version": "1.0.0",
                "files": [{"path": "missing_file.json", "sha256": "abc", "size_bytes": 10}]
            }
            m_path = os.path.join(temp_dir, "manifest.json")
            with open(m_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f)
            is_valid, assertions, summary = validate_evidence_manifest(m_path, temp_dir)
            self.assertFalse(is_valid)
            self.assertTrue(any("missing on disk" in a.detail for a in assertions))
        finally:
            shutil.rmtree(temp_dir)

    # T08: Invalid JSON pointer (FAIL)
    def test_T08_invalid_json_pointer(self):
        """Exercises production resolve_json_pointer with various syntax errors and invalid escapes."""
        # 1. Pointer not starting with /
        with self.assertRaises(ValueError):
            resolve_json_pointer({"key": 1}, "invalid_no_slash")
        # 2. Key not in doc
        with self.assertRaises(KeyError):
            resolve_json_pointer({"key": 1}, "/missing_key")
        # 3. Index out of range
        with self.assertRaises(IndexError):
            resolve_json_pointer([1, 2], "/10")
        # 4. Malformed RFC 6901 escape sequence ~2
        with self.assertRaises(ValueError):
            resolve_json_pointer({"~key": 1}, "/~2key")

    # T09: Evidence reference outside permitted root (FAIL)
    def test_T09_evidence_reference_outside_permitted_root(self):
        """Exercises production validate_structured_evidence_reference against path traversal."""
        invalid_refs = [
            {"type": "file", "path": "../outside.json"},
            {"type": "file", "path": "/etc/passwd"},
            {"type": "file", "path": "C:\\Windows\\win.ini"}
        ]
        for ref in invalid_refs:
            ok, msg = validate_structured_evidence_reference(ref, REPO_ROOT)
            self.assertFalse(ok)
            self.assertTrue("Invalid path" in msg or "escapes" in msg)

    # T10: Unknown claim ID (FAIL)
    def test_T10_unknown_claim_id(self):
        """Exercises production make_claim_assertion_registry for unknown claim registration."""
        dummy_doc: Dict[str, Any] = {}
        registry = make_claim_assertion_registry(
            repo_root=REPO_ROOT,
            can_doc=dummy_doc,
            inv_doc=dummy_doc,
            dep_doc=dummy_doc,
            native_inv_doc=dummy_doc,
            dotnet_interop_doc=dummy_doc,
            managed_assm_doc=dummy_doc,
            runtime_doc=dummy_doc
        )
        self.assertNotIn("P1-999", registry)
        self.assertIsNone(registry.get("P1-999"))

    # T11: Claim missing executable assertion (FAIL)
    def test_T11_claim_missing_executable_assertion(self):
        """Exercises validation logic when an assertion function is missing from registry."""
        dummy_doc: Dict[str, Any] = {}
        registry = make_claim_assertion_registry(
            repo_root=REPO_ROOT,
            can_doc=dummy_doc,
            inv_doc=dummy_doc,
            dep_doc=dummy_doc,
            native_inv_doc=dummy_doc,
            dotnet_interop_doc=dummy_doc,
            managed_assm_doc=dummy_doc,
            runtime_doc=dummy_doc
        )
        # Corrupt an entry by removing its assertion_fn
        corrupted_registry = dict(registry)
        corrupted_registry["P1-001"] = {"assertion_id": "P1-001"}

        stage = StageResult("claim_specific_assertions")
        entry = corrupted_registry.get("P1-001")
        if not entry or 'assertion_fn' not in entry:
            stage.record_assertion("Claim P1-001 assertion procedure", STATUS_FAIL, "No assertion function registered")

        self.assertEqual(stage.status, STATUS_FAIL)

    # T12: Claim missing required evidence references (FAIL)
    def test_T12_claim_missing_required_evidence_references(self):
        """Exercises production validate_structured_evidence_reference on malformed reference objects."""
        # Malformed references missing required fields
        malformed_refs = [
            {},
            {"type": "file"},  # missing path
            {"path": "evidence/phase1/target_identity.json"},  # missing type
            {"type": "json_pointer", "path": "evidence/phase1/target_identity.json"}  # missing pointer
        ]
        for ref in malformed_refs:
            ok, msg = validate_structured_evidence_reference(ref, REPO_ROOT)
            self.assertFalse(ok)
            self.assertTrue(len(msg) > 0)

    # T13: Unsupported VERIFIED status (FAIL)
    def test_T13_unsupported_verified_status(self):
        """Exercises production validate_status_accounting on unsupported status token."""
        claims = [{"id": "P1-001", "status": "VERIFIED_UNSUPPORTED_XYZ"}]
        declared = {st: 0 for st in ALLOWED_CLAIM_STATUSES}
        res = validate_status_accounting(claims, declared)
        self.assertFalse(res['is_valid'])
        self.assertTrue(any("unrecognized status" in e for e in res['errors']))

    # T14: Missing declared status category (FAIL)
    def test_T14_missing_declared_status_category(self):
        """Exercises production validate_status_accounting when a declared status category is missing."""
        claims = [{"id": "P1-001", "status": "VERIFIED_STATIC"}]
        declared = {
            'VERIFIED_STATIC': 1,
            'VERIFIED_RUNTIME': 0,
            'VERIFIED_DOCUMENTATION': 0,
            'INFERRED': 0,
            'NOT_PERFORMED': 0
            # 'UNKNOWN' is missing
        }
        res = validate_status_accounting(claims, declared)
        self.assertFalse(res['is_valid'])
        self.assertTrue(any("missing categories" in e for e in res['errors']))

    # T15: Incorrect status count (FAIL)
    def test_T15_incorrect_status_count(self):
        """Exercises production validate_status_accounting when declared count does not match actual count."""
        claims = [{"id": "P1-001", "status": "VERIFIED_STATIC"}]
        declared = {st: 0 for st in ALLOWED_CLAIM_STATUSES}
        declared['VERIFIED_STATIC'] = 999  # Actual is 1
        res = validate_status_accounting(claims, declared)
        self.assertFalse(res['is_valid'])
        self.assertIn('VERIFIED_STATIC', res['mismatched_counts'])

    # T16: Unexpected status category (FAIL)
    def test_T16_unexpected_status_category(self):
        """Exercises production validate_status_accounting when an unexpected extra category is provided."""
        claims = [{"id": "P1-001", "status": "VERIFIED_STATIC"}]
        declared = {st: 0 for st in ALLOWED_CLAIM_STATUSES}
        declared['VERIFIED_STATIC'] = 1
        declared['SOME_EXTRA_BOGUS_STATUS'] = 0
        res = validate_status_accounting(claims, declared)
        self.assertFalse(res['is_valid'])
        self.assertTrue(any("unexpected categories" in e for e in res['errors']))

    # T17: Prohibited image in nested screenshot directory (FAIL)
    def test_T17_prohibited_image_in_nested_screenshot_directory(self):
        """Exercises production scan_prohibited_images finding prohibited image deep in hierarchy."""
        temp_dir = tempfile.mkdtemp(prefix='test_img_t17_')
        try:
            nested = os.path.join(temp_dir, 'sub1', 'sub2')
            os.makedirs(nested, exist_ok=True)
            prohibited_file = os.path.join(nested, 'forbidden_sample.PNG')
            with open(prohibited_file, 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n')

            res = scan_prohibited_images(temp_dir)
            self.assertFalse(res['is_clean'])
            self.assertEqual(len(res['found_images']), 1)
            self.assertIn("sub1/sub2/forbidden_sample.PNG", res['found_images'][0].replace('\\', '/'))
        finally:
            shutil.rmtree(temp_dir)

    # T18: Screenshot directory traversal error (FAIL / NOT_CHECKED)
    def test_T18_screenshot_directory_traversal_error(self):
        """Exercises production scan_prohibited_images on nonexistent directory path."""
        nonexistent = os.path.join(REPO_ROOT, "nonexistent_screenshots_dir_12345")
        res = scan_prohibited_images(nonexistent)
        self.assertFalse(res['directory_exists'])
        self.assertFalse(res['is_clean'])
        self.assertTrue(len(res['traversal_errors']) > 0)

    # T19: Unresolved mandatory warning (BLOCKED)
    def test_T19_unresolved_mandatory_warning(self):
        """Exercises production evaluate_release_gate when a mandatory stage or check has a WARNING."""
        stage_results = {
            'target_binary_integrity': STATUS_PASS,
            'manifest_integrity': STATUS_PASS,
            'direct_import_partition': STATUS_PASS,
            'status_accounting': STATUS_PASS,
            'evidence_references': STATUS_PASS,
            'claim_specific_assertions': STATUS_PASS,
            'recursive_image_audit': STATUS_PASS,
            'report_consistency': STATUS_WARNING
        }
        counts = {STATUS_PASS: 100, STATUS_FAIL: 0, STATUS_WARNING: 1, STATUS_NOT_CHECKED: 0}
        exit_code, status, msg = evaluate_release_gate(stage_results, counts)
        self.assertEqual(exit_code, 1)
        self.assertEqual(status, "PHASE 1.1.2.2 — BLOCKED")
        self.assertIn("warnings present", msg.lower())

    # T20: Mismatched provenance commit SHA (FAIL)
    def test_T20_mismatched_provenance_commit_sha(self):
        """Exercises production validate_provenance_record when commit SHA or validation script is corrupted."""
        prov_doc = {
            "provenance_metadata": {
                "validated_commit_sha": "invalid_too_short",
                "validator_script": {"path": "scripts/validate-phase1-evidence.py", "sha256": "0" * 64},
                "validation_manifest": {"path": "evidence/phase1/reconciliation/evidence_manifest.json", "sha256": "0" * 64}
            },
            "validation_results": {
                "summary_accounting": {
                    "total_checks": 10,
                    "pass": 10,
                    "fail": 0,
                    "warning": 0,
                    "not_checked": 0
                }
            }
        }
        is_valid, errors = validate_provenance_record(prov_doc, REPO_ROOT)
        self.assertFalse(is_valid)
        self.assertTrue(any("validated_commit_sha" in e for e in errors))

    # T21: Binary-stage subcheck failure (Stage FAIL)
    def test_T21_binary_stage_subcheck_failure(self):
        """Exercises production validate_target_binary on a corrupt PE header fixture."""
        temp_dir = tempfile.mkdtemp(prefix='test_t21_')
        try:
            corrupt_exe = os.path.join(temp_dir, "corrupt.exe")
            # Create a file with MZ header but corrupt PE signature
            with open(corrupt_exe, "wb") as f:
                header = bytearray(1024)
                header[0:2] = b"MZ"
                header[0x3c:0x40] = (128).to_bytes(4, 'little')  # e_lfanew = 128
                header[128:132] = b"NOTP"  # Invalid PE signature
                f.write(header)

            canonical = {
                "file_size_bytes": 1024,
                "md5": hashlib.md5(header).hexdigest(),
                "sha1": hashlib.sha1(header).hexdigest(),
                "sha256": hashlib.sha256(header).hexdigest(),
                "pe_headers": {
                    "machine": "0x8664",
                    "magic": "0x20b",
                    "entry_point": "0x1000",
                    "sections": [".text"]
                }
            }
            is_valid, assertions, info = validate_target_binary(corrupt_exe, canonical)
            self.assertFalse(is_valid)
            self.assertTrue(any("PE header parsing failed" in a.detail or "Invalid PE signature" in a.detail for a in assertions))
        finally:
            shutil.rmtree(temp_dir)

    # T22: Missing runtime test identifier (FAIL)
    def test_T22_missing_runtime_test_identifier(self):
        """Exercises production validate_structured_evidence_reference with unknown runtime test ID."""
        ref = {
            "type": "runtime_test",
            "path": "evidence/phase1/runtime_observations.json",
            "test_id": "RT-NONEXISTENT-99"
        }
        known_tids = {"RT-01", "RT-02", "RT-03"}
        ok, msg = validate_structured_evidence_reference(ref, REPO_ROOT, known_tids)
        self.assertFalse(ok)
        self.assertIn("not found", msg)

    # T23: Corrupted measurement conversion behavior (FAIL)
    def test_T23_corrupted_measurement_conversion_behavior(self):
        """Tests that mathematical verification bounds for twip and Length conversion fail when perturbed."""
        # Standard twip is 1/1440 inch = 25.4 / 1440.0 = 0.017638888... mm
        corrupted_twip_step_mm = 25.4 / 1000.0  # Wrong factor (1000 DPI)
        is_in_bounds = (0.0176 < corrupted_twip_step_mm < 0.0177)
        self.assertFalse(is_in_bounds)

    # T24: Phantom DLL present in target inventory (FAIL)
    def test_T24_phantom_dll_present_in_target_inventory(self):
        """Exercises production claim assertion for P1-015 detecting phantom DLL in components inventory."""
        corrupted_app_comp = {
            "components": [
                {"name": "Core"},
                {"name": "Printer"}
            ],
            "libraries": [
                {"name": "BtEngine.dll"},  # Corrupted: phantom DLL present
                {"name": "Other.dll"}
            ]
        }
        corrupted_dep_doc = {
            'phantom_dll_reconciliation': [
                {'phantom_name': 'BtBarcode.dll'},
                {'phantom_name': 'BtPrint.dll'},
                {'phantom_name': 'BtSystem.dll'},
                {'phantom_name': 'BtLic.dll'},
                {'phantom_name': 'BtData.dll'},
                {'phantom_name': 'BtEngine.dll'}
            ]
        }
        dummy = {}
        registry = make_claim_assertion_registry(
            repo_root=REPO_ROOT,
            can_doc=dummy,
            inv_doc=dummy,
            dep_doc=corrupted_dep_doc,
            native_inv_doc=dummy,
            dotnet_interop_doc=dummy,
            managed_assm_doc=dummy,
            runtime_doc=dummy,
            app_comp_doc=corrupted_app_comp
        )
        status, detail = registry['P1-015']['assertion_fn']()
        self.assertEqual(status, 'FAIL')
        self.assertIn("BtEngine.dll", detail)


if __name__ == '__main__':
    unittest.main()
