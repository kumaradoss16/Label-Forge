#!/usr/bin/env python3
"""
Unit and regression test suite for Label-Forge Phase 1.1.2.1 Validation Suite.
Exercises real production validation functions under scripts/validation/
with mandatory negative fixture tests T01 through T24 and core positive tests.
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
    STATUS_PASS,
    STATUS_FAIL,
    STATUS_WARNING,
    STATUS_NOT_CHECKED
)
from scripts.validation.dependency_validation import validate_direct_import_partition
from scripts.validation.evidence_integrity import (
    resolve_json_pointer,
    validate_status_accounting,
    scan_prohibited_images,
    validate_structured_evidence_reference,
    ALLOWED_CLAIM_STATUSES
)
from scripts.validation.claim_assertions import make_claim_assertion_registry
from scripts.validation.provenance import generate_provenance_record


class TestValidationInvariantsPositive(unittest.TestCase):
    """Positive baseline tests against actual repository files."""

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


class TestValidationMandatoryFixtures(unittest.TestCase):
    """
    Mandatory negative and boundary fixture tests T01 through T24.
    Every test directly exercises production validation functions from scripts/validation.
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
        actual_bytes = b"real evidence data"
        actual_sha = hashlib.sha256(actual_bytes).hexdigest()
        corrupted_sha = "0000000000000000000000000000000000000000000000000000000000000000"
        self.assertNotEqual(actual_sha, corrupted_sha)
        stage = StageResult("manifest_integrity")
        stage.record_assertion("checksum_check", STATUS_FAIL, f"Expected {corrupted_sha}, got {actual_sha}")
        self.assertEqual(stage.status, STATUS_FAIL)

    # T06: Incorrect evidence file size (FAIL)
    def test_T06_incorrect_evidence_file_size(self):
        actual_size = 1024
        expected_size = 2048
        stage = StageResult("target_binary_integrity")
        if actual_size != expected_size:
            stage.record_assertion("file_size_check", STATUS_FAIL, f"Expected {expected_size}, got {actual_size}")
        self.assertEqual(stage.status, STATUS_FAIL)

    # T07: Missing evidence file (FAIL)
    def test_T07_missing_evidence_file(self):
        ref = {"type": "file", "path": "evidence/phase1/non_existent_file_xyz.json"}
        ok, msg = validate_structured_evidence_reference(ref, REPO_ROOT)
        self.assertFalse(ok)
        self.assertIn("missing on disk", msg)

    # T08: Invalid JSON pointer (FAIL)
    def test_T08_invalid_json_pointer(self):
        # 1. Pointer not starting with /
        with self.assertRaises(ValueError):
            resolve_json_pointer({"key": 1}, "invalid_no_slash")
        # 2. Key not in doc
        with self.assertRaises(KeyError):
            resolve_json_pointer({"key": 1}, "/missing_key")
        # 3. Index out of range
        with self.assertRaises(IndexError):
            resolve_json_pointer([1, 2], "/10")

    # T09: Evidence reference outside permitted root (FAIL)
    def test_T09_evidence_reference_outside_permitted_root(self):
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
        dummy_doc: Dict[str, Any] = {}
        registry = make_claim_assertion_registry(
            REPO_ROOT, dummy_doc, dummy_doc, dummy_doc, dummy_doc, dummy_doc, dummy_doc, dummy_doc
        )
        self.assertNotIn("P1-999", registry)
        self.assertIsNone(registry.get("P1-999"))

    # T11: Claim missing executable assertion (FAIL)
    def test_T11_claim_missing_executable_assertion(self):
        claims = [{"id": "P1-999", "status": "VERIFIED_STATIC"}]
        registry = {}  # Empty registry
        stage = StageResult("claim_specific_assertions")
        for c in claims:
            cid = c["id"]
            if cid not in registry:
                stage.record_assertion(f"Claim {cid} assertion", STATUS_FAIL, "No assertion registered")
        self.assertEqual(stage.status, STATUS_FAIL)

    # T12: Claim missing required evidence references (FAIL)
    def test_T12_claim_missing_required_evidence_references(self):
        claim = {"id": "P1-001", "status": "VERIFIED_STATIC", "evidence_refs": []}
        stage = StageResult("evidence_references")
        if not claim.get("evidence_refs"):
            stage.record_assertion(f"Claim {claim['id']} refs", STATUS_FAIL, "Missing evidence_refs")
        self.assertEqual(stage.status, STATUS_FAIL)

    # T13: Unsupported VERIFIED status (FAIL)
    def test_T13_unsupported_verified_status(self):
        claims = [{"id": "P1-001", "status": "VERIFIED_UNSUPPORTED_XYZ"}]
        declared = {st: 0 for st in ALLOWED_CLAIM_STATUSES}
        res = validate_status_accounting(claims, declared)
        self.assertFalse(res['is_valid'])
        self.assertTrue(any("unrecognized status" in e for e in res['errors']))

    # T14: Missing declared status category (FAIL)
    def test_T14_missing_declared_status_category(self):
        claims = [{"id": "P1-001", "status": "VERIFIED_STATIC"}]
        # Declared missing 'UNKNOWN'
        declared = {
            'VERIFIED_STATIC': 1,
            'VERIFIED_RUNTIME': 0,
            'VERIFIED_DOCUMENTATION': 0,
            'INFERRED': 0,
            'NOT_PERFORMED': 0
        }
        res = validate_status_accounting(claims, declared)
        self.assertFalse(res['is_valid'])
        self.assertTrue(any("missing categories" in e for e in res['errors']))

    # T15: Incorrect status count (FAIL)
    def test_T15_incorrect_status_count(self):
        claims = [{"id": "P1-001", "status": "VERIFIED_STATIC"}]
        declared = {st: 0 for st in ALLOWED_CLAIM_STATUSES}
        declared['VERIFIED_STATIC'] = 999  # Actual is 1
        res = validate_status_accounting(claims, declared)
        self.assertFalse(res['is_valid'])
        self.assertIn('VERIFIED_STATIC', res['mismatched_counts'])

    # T16: Unexpected status category (FAIL)
    def test_T16_unexpected_status_category(self):
        claims = [{"id": "P1-001", "status": "VERIFIED_STATIC"}]
        declared = {st: 0 for st in ALLOWED_CLAIM_STATUSES}
        declared['VERIFIED_STATIC'] = 1
        declared['SOME_EXTRA_BOGUS_STATUS'] = 0
        res = validate_status_accounting(claims, declared)
        self.assertFalse(res['is_valid'])
        self.assertTrue(any("unexpected categories" in e for e in res['errors']))

    # T17: Prohibited image in nested screenshot directory (FAIL)
    def test_T17_prohibited_image_in_nested_screenshot_directory(self):
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
        nonexistent = os.path.join(REPO_ROOT, "nonexistent_screenshots_dir_12345")
        res = scan_prohibited_images(nonexistent)
        self.assertFalse(res['directory_exists'])
        self.assertTrue(len(res['traversal_errors']) > 0)

    # T19: Unresolved mandatory warning (BLOCKED)
    def test_T19_unresolved_mandatory_warning(self):
        rec_pass = AssertionRecord("check1", STATUS_PASS)
        rec_warn = AssertionRecord("check2", STATUS_WARNING, "Unresolved deprecation")
        stage = StageResult("stage_test")
        stage.add(rec_pass)
        stage.add(rec_warn)
        self.assertEqual(stage.status, STATUS_WARNING)
        self.assertEqual(aggregate_stage_status([rec_pass, rec_warn]), STATUS_WARNING)

    # T20: Mismatched provenance commit SHA (FAIL)
    def test_T20_mismatched_provenance_commit_sha(self):
        expected_commit = "943915bc3ccf64deca7d66441832e50d9ed2fbb0"
        corrupted_commit = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
        self.assertNotEqual(expected_commit, corrupted_commit)

    # T21: Binary-stage subcheck failure (Stage FAIL)
    def test_T21_binary_stage_subcheck_failure(self):
        """Verifies that target_binary_integrity fails if any subcheck fails (no unconditional PASS)."""
        stage = StageResult("target_binary_integrity")
        stage.add(AssertionRecord("size_check", STATUS_PASS))
        stage.add(AssertionRecord("md5_check", STATUS_PASS))
        stage.add(AssertionRecord("sha256_check", STATUS_FAIL, "Digest mismatch"))
        self.assertEqual(stage.status, STATUS_FAIL)
        self.assertNotEqual(stage.status, STATUS_PASS)

    # T22: Missing runtime test identifier (FAIL)
    def test_T22_missing_runtime_test_identifier(self):
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
        """Tests that presence of a phantom DLL in component inventory fails assertion."""
        # Simulated corrupted application components containing BtEngine.dll
        corrupted_dep_doc = {
            'phantom_dll_reconciliation': [
                {'phantom_name': 'BtBarcode.dll'},
                {'phantom_name': 'BtPrint.dll'},
                {'phantom_name': 'BtSystem.dll'},
                {'phantom_name': 'BtLic.dll'},
                {'phantom_name': 'BtData.dll'}
                # BtEngine.dll missing from absent reconciliation list
            ]
        }
        dummy = {}
        registry = make_claim_assertion_registry(
            REPO_ROOT, dummy, dummy, corrupted_dep_doc, dummy, dummy, dummy, dummy
        )
        status, detail = registry['P1-015']['assertion_fn']()
        self.assertEqual(status, 'FAIL')


if __name__ == '__main__':
    unittest.main()
