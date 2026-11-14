#!/usr/bin/env python3
"""
Unit and regression test suite for Label-Forge Phase 1.1.2.2 Independent Validator Acceptance.
Exercises real production validation functions under scripts/validation/
with mandatory negative fixture tests T01 through T24 strictly mapped to Phase 1.1.2.2
Master Specification Section 7.3, plus comprehensive positive baseline tests.
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
        self.assertIn("APPROVED", status)

    def test_symlink_path_boundary_protection(self):
        """AC-05: Verify symlink and path traversal boundaries are strictly enforced."""
        invalid_traversal_ref = {
            "type": "file",
            "path": "../../../../../Windows/System32/drivers/etc/hosts"
        }
        ok, msg = validate_structured_evidence_reference(invalid_traversal_ref, REPO_ROOT)
        self.assertFalse(ok)
        self.assertTrue("outside" in msg or "escapes" in msg or "Invalid" in msg)


class TestValidationMandatoryFixtures(unittest.TestCase):
    """
    Mandatory negative and boundary fixture tests T01 through T24.
    Strictly mapped to Section 7.3 of the Master Implementation Specification.
    Every test directly exercises production validation functions from scripts/validation.
    """

    # T01: Missing required evidence file (FAIL)
    def test_T01_missing_required_evidence_file(self):
        """T01: Missing required evidence file rejects manifest in validate_evidence_manifest."""
        temp_dir = tempfile.mkdtemp(prefix='test_t01_')
        try:
            manifest = {
                "manifest_schema_version": "1.0.0",
                "files": [{"path": "missing_evidence_file.json", "sha256": "abc", "size_bytes": 10}]
            }
            m_path = os.path.join(temp_dir, "manifest.json")
            with open(m_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f)
            is_valid, assertions, summary = validate_evidence_manifest(m_path, temp_dir)
            self.assertFalse(is_valid)
            self.assertTrue(any("missing on disk" in a.detail for a in assertions))
        finally:
            shutil.rmtree(temp_dir)

    # T02: Evidence file size mismatch (FAIL)
    def test_T02_evidence_file_size_mismatch(self):
        """T02: Evidence file size mismatch fails validation in validate_evidence_manifest."""
        temp_dir = tempfile.mkdtemp(prefix='test_t02_')
        try:
            sample_file = os.path.join(temp_dir, "sample.json")
            file_bytes = b'{"hello": "world"}'
            with open(sample_file, "wb") as f:
                f.write(file_bytes)

            manifest = {
                "manifest_schema_version": "1.0.0",
                "files": [
                    {
                        "path": "sample.json",
                        "sha256": hashlib.sha256(file_bytes).hexdigest(),
                        "size_bytes": 99999  # Deliberate size mismatch
                    }
                ]
            }
            m_path = os.path.join(temp_dir, "manifest.json")
            with open(m_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f)
            is_valid, assertions, summary = validate_evidence_manifest(m_path, temp_dir)
            self.assertFalse(is_valid)
            self.assertTrue(any("Size mismatch" in a.detail for a in assertions))
        finally:
            shutil.rmtree(temp_dir)

    # T03: Evidence SHA-256 mismatch (FAIL)
    def test_T03_evidence_sha256_mismatch(self):
        """T03: Evidence SHA-256 mismatch fails validation in validate_evidence_manifest."""
        temp_dir = tempfile.mkdtemp(prefix='test_t03_')
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
            m_path = os.path.join(temp_dir, "manifest.json")
            with open(m_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f)

            is_valid, assertions, summary = validate_evidence_manifest(m_path, temp_dir)
            self.assertFalse(is_valid)
            self.assertTrue(any(a.status == STATUS_FAIL and "SHA-256 mismatch" in a.detail for a in assertions))
        finally:
            shutil.rmtree(temp_dir)

    # T04: Invalid manifest reference (FAIL)
    def test_T04_invalid_manifest_reference(self):
        """T04: Invalid manifest reference (path traversal / outside root) fails reference audit."""
        invalid_refs = [
            {"type": "file", "path": "../outside.json"},
            {"type": "file", "path": "/etc/passwd"},
            {"type": "file", "path": "C:\\Windows\\win.ini"}
        ]
        for ref in invalid_refs:
            ok, msg = validate_structured_evidence_reference(ref, REPO_ROOT)
            self.assertFalse(ok)
            self.assertTrue("Invalid path" in msg or "escapes" in msg)

    # T05: Actual binary integrity mismatch (FAIL)
    def test_T05_actual_binary_integrity_mismatch(self):
        """T05: Target binary integrity mismatch fails validate_target_binary."""
        temp_dir = tempfile.mkdtemp(prefix='test_t05_')
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

    # T06: Invalid PE metadata (FAIL)
    def test_T06_invalid_pe_metadata(self):
        """T06: Invalid PE metadata / signature fails validate_target_binary."""
        temp_dir = tempfile.mkdtemp(prefix='test_t06_')
        try:
            corrupt_exe = os.path.join(temp_dir, "corrupt.exe")
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

    # T07: Missing dependency category (FAIL)
    def test_T07_missing_dependency_category(self):
        """T07: Missing direct-import module from category partition fails validate_direct_import_partition."""
        canonical = ["A.DLL", "B.DLL", "C.DLL"]
        categories = {"cat1": ["A.DLL"], "cat2": ["B.DLL"]}
        res = validate_direct_import_partition(canonical, categories)
        self.assertFalse(res['is_exact_partition'])
        self.assertIn("C.DLL", res['missing_modules'])

    # T08: Duplicate dependency classification (FAIL)
    def test_T08_duplicate_dependency_classification(self):
        """T08: Module assigned to multiple categories fails validate_direct_import_partition."""
        canonical = ["A.DLL", "B.DLL"]
        categories = {"cat1": ["A.DLL", "B.DLL"], "cat2": ["B.DLL"]}
        res = validate_direct_import_partition(canonical, categories)
        self.assertFalse(res['is_exact_partition'])
        self.assertIn("B.DLL", res['cross_category_overlaps'])
        self.assertEqual(res['cross_category_overlaps']["B.DLL"], ["cat1", "cat2"])

    # T09: Unexpected direct import (FAIL)
    def test_T09_unexpected_direct_import(self):
        """T09: Undeclared direct import module fails validate_direct_import_partition."""
        canonical = ["A.DLL", "B.DLL"]
        categories = {"cat1": ["A.DLL"], "cat2": ["B.DLL", "EXTRA.DLL"]}
        res = validate_direct_import_partition(canonical, categories)
        self.assertFalse(res['is_exact_partition'])
        self.assertIn("EXTRA.DLL", res['unexpected_modules'])

    # T10: Unknown claim ID (FAIL)
    def test_T10_unknown_claim_id(self):
        """T10: Unknown claim ID returns None from make_claim_assertion_registry."""
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

    # T11: Missing claim evidence reference (FAIL)
    def test_T11_missing_claim_evidence_reference(self):
        """T11: Missing or empty claim evidence_refs fails validation."""
        malformed_refs = [
            {},
            {"type": "file"},  # missing path
            {"path": "evidence/phase1/target_identity.json"}  # missing type
        ]
        for ref in malformed_refs:
            ok, msg = validate_structured_evidence_reference(ref, REPO_ROOT)
            self.assertFalse(ok)
            self.assertTrue(len(msg) > 0)

    # T12: Invalid JSON Pointer (FAIL)
    def test_T12_invalid_json_pointer(self):
        """T12: Invalid JSON Pointer syntax or escape rejects via resolve_json_pointer."""
        # 1. Pointer not starting with /
        with self.assertRaises(ValueError):
            resolve_json_pointer({"key": 1}, "invalid_no_slash")
        # 2. Malformed escape ~2
        with self.assertRaises(ValueError):
            resolve_json_pointer({"~key": 1}, "/~2key")
        # 3. Invalid array index with leading zero
        with self.assertRaises(IndexError):
            resolve_json_pointer([1, 2, 3], "/01")

    # T13: Missing referenced JSON object (FAIL)
    def test_T13_missing_referenced_json_object(self):
        """T13: Missing referenced JSON key or out-of-range index raises KeyError / IndexError."""
        with self.assertRaises(KeyError):
            resolve_json_pointer({"key": 1}, "/missing_key")
        with self.assertRaises(IndexError):
            resolve_json_pointer([1, 2], "/10")

    # T14: Invalid claim status (FAIL)
    def test_T14_invalid_claim_status(self):
        """T14: Invalid or unrecognized claim status token fails validate_status_accounting."""
        claims = [{"id": "P1-001", "status": "VERIFIED_UNSUPPORTED_XYZ"}]
        declared = {st: 0 for st in ALLOWED_CLAIM_STATUSES}
        res = validate_status_accounting(claims, declared)
        self.assertFalse(res['is_valid'])
        self.assertTrue(any("unrecognized status" in e for e in res['errors']))

    # T15: Incorrect claim status totals (FAIL)
    def test_T15_incorrect_claim_status_totals(self):
        """T15: Incorrect claim status count fails validate_status_accounting."""
        claims = [{"id": "P1-001", "status": "VERIFIED_STATIC"}]
        declared = {st: 0 for st in ALLOWED_CLAIM_STATUSES}
        declared['VERIFIED_STATIC'] = 999  # Actual is 1
        res = validate_status_accounting(claims, declared)
        self.assertFalse(res['is_valid'])
        self.assertIn('VERIFIED_STATIC', res['mismatched_counts'])

    # T16: Missing declared status category (FAIL)
    def test_T16_missing_declared_status_category(self):
        """T16: Missing declared status category fails validate_status_accounting."""
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

    # T17: Prohibited image in nested directory (FAIL)
    def test_T17_prohibited_image_in_nested_directory(self):
        """T17: Prohibited image file in nested directory fails scan_prohibited_images."""
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

    # T18: Missing screenshot directory (FAIL)
    def test_T18_missing_screenshot_directory(self):
        """T18: Missing screenshot directory fails scan_prohibited_images."""
        nonexistent = os.path.join(REPO_ROOT, "nonexistent_screenshots_dir_12345")
        res = scan_prohibited_images(nonexistent)
        self.assertFalse(res['directory_exists'])
        self.assertFalse(res['is_clean'])
        self.assertTrue(len(res['traversal_errors']) > 0)

    # T19: Screenshot traversal error (FAIL)
    def test_T19_screenshot_traversal_error(self):
        """T19: Filesystem traversal errors are captured by scan_prohibited_images."""
        temp_dir = tempfile.mkdtemp(prefix='test_img_t19_')
        try:
            file_as_dir = os.path.join(temp_dir, "not_a_dir.txt")
            with open(file_as_dir, "w") as f:
                f.write("test")
            res = scan_prohibited_images(file_as_dir)
            self.assertFalse(res['is_clean'])
            self.assertTrue(len(res['traversal_errors']) > 0)
        finally:
            shutil.rmtree(temp_dir)

    # T20: Source revision/provenance mismatch (FAIL)
    def test_T20_source_revision_provenance_mismatch(self):
        """T20: Provenance document with mismatched or invalid commit SHA fails validate_provenance_record."""
        prov_doc = {
            "provenance_metadata": {
                "validated_commit_sha": "invalid_too_short",
                "validator_script": {"path": "scripts/validate-phase1-evidence.py", "sha256": "0" * 64},
                "validation_manifest": {"path": "evidence/phase1/reconciliation/validation_manifest.json", "sha256": "0" * 64}
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

    # T21: Validator or manifest hash mismatch (FAIL)
    def test_T21_validator_or_manifest_hash_mismatch(self):
        """T21: Validator script or manifest SHA-256 mismatch fails validate_provenance_record."""
        prov_doc = {
            "provenance_metadata": {
                "validated_commit_sha": "a" * 40,
                "validator_script": {"path": "scripts/validate-phase1-evidence.py", "sha256": "0" * 64},
                "validation_manifest": {"path": "evidence/phase1/reconciliation/validation_manifest.json", "sha256": "0" * 64}
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
        self.assertTrue(any("mismatch" in e.lower() for e in errors))

    # T22: Incomplete validation stage (FAIL / BLOCKED)
    def test_T22_incomplete_validation_stage(self):
        """T22: Incomplete or missing mandatory validation stage blocks release gate in evaluate_release_gate."""
        incomplete_stages = {
            'target_binary_integrity': STATUS_PASS,
            'manifest_integrity': STATUS_PASS,
            # 'direct_import_partition' missing
            'status_accounting': STATUS_PASS,
            'evidence_references': STATUS_PASS,
            'claim_specific_assertions': STATUS_PASS,
            'recursive_image_audit': STATUS_PASS,
            'report_consistency': STATUS_PASS
        }
        counts = {STATUS_PASS: 100, STATUS_FAIL: 0, STATUS_WARNING: 0, STATUS_NOT_CHECKED: 0}
        code, status, msg = evaluate_release_gate(incomplete_stages, counts)
        self.assertEqual(code, 1)
        self.assertIn("BLOCKED", status)
        self.assertIn("Missing mandatory validation stages", msg)

    # T23: Failed mandatory check incorrectly treated as PASS (FAIL)
    def test_T23_failed_mandatory_check_incorrectly_treated_as_pass(self):
        """T23: Failed mandatory check prevents PASS and fails release gate in evaluate_release_gate."""
        stages_with_failure = {
            'target_binary_integrity': STATUS_FAIL,
            'manifest_integrity': STATUS_PASS,
            'direct_import_partition': STATUS_PASS,
            'status_accounting': STATUS_PASS,
            'evidence_references': STATUS_PASS,
            'claim_specific_assertions': STATUS_PASS,
            'recursive_image_audit': STATUS_PASS,
            'report_consistency': STATUS_PASS
        }
        counts = {STATUS_PASS: 100, STATUS_FAIL: 1, STATUS_WARNING: 0, STATUS_NOT_CHECKED: 0}
        code, status, msg = evaluate_release_gate(stages_with_failure, counts)
        self.assertEqual(code, 1)
        self.assertIn("FAILED", status)

    # T24: Warning or NOT_CHECKED result incorrectly treated as approval (BLOCKED)
    def test_T24_warning_or_not_checked_result_incorrectly_treated_as_approval(self):
        """T24: Unresolved warning or NOT_CHECKED blocks release gate with exit code 1 or 2."""
        stages_not_checked = {
            'target_binary_integrity': STATUS_NOT_CHECKED,
            'manifest_integrity': STATUS_PASS,
            'direct_import_partition': STATUS_PASS,
            'status_accounting': STATUS_PASS,
            'evidence_references': STATUS_PASS,
            'claim_specific_assertions': STATUS_PASS,
            'recursive_image_audit': STATUS_PASS,
            'report_consistency': STATUS_PASS
        }
        counts_nc = {STATUS_PASS: 100, STATUS_FAIL: 0, STATUS_WARNING: 0, STATUS_NOT_CHECKED: 1}
        code_nc, status_nc, _ = evaluate_release_gate(stages_not_checked, counts_nc)
        self.assertEqual(code_nc, 2)
        self.assertIn("BLOCKED", status_nc)

        stages_warn = {
            'target_binary_integrity': STATUS_PASS,
            'manifest_integrity': STATUS_PASS,
            'direct_import_partition': STATUS_PASS,
            'status_accounting': STATUS_PASS,
            'evidence_references': STATUS_PASS,
            'claim_specific_assertions': STATUS_PASS,
            'recursive_image_audit': STATUS_PASS,
            'report_consistency': STATUS_WARNING
        }
        counts_w = {STATUS_PASS: 100, STATUS_FAIL: 0, STATUS_WARNING: 1, STATUS_NOT_CHECKED: 0}
        code_w, status_w, _ = evaluate_release_gate(stages_warn, counts_w)
        self.assertEqual(code_w, 1)
        self.assertIn("BLOCKED", status_w)


if __name__ == '__main__':
    unittest.main()
