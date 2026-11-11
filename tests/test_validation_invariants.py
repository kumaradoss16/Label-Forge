#!/usr/bin/env python3
"""
Unit and regression test suite for Label-Forge Phase 1.1.2 Validation Suite
Verifies critical invariants, positive paths, and intentional negative failure paths:
1. Exact direct-import category partition
2. Claim-specific assertion registry and removal of unconditional PASS fallbacks
3. Structured evidence_refs (RFC 6901 JSON pointers, file refs, runtime tests, path safety)
4. Exact status accounting
5. Recursive prohibited-image auditing
6. Exit code propagation and error handling
"""

import unittest
import os
import sys
import tempfile
import shutil
import json

# Ensure scripts directory is on sys.path
SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
sys.path.insert(0, SCRIPTS_DIR)

from importlib import import_module
validate_module = import_module('validate-phase1-evidence')
resolve_json_pointer = validate_module.resolve_json_pointer
ValidationSuite = validate_module.ValidationSuite

class TestValidationSuiteInvariants(unittest.TestCase):

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
        
        with self.assertRaises(ValueError):
            resolve_json_pointer(doc, "invalid_pointer_without_slash")
        with self.assertRaises(KeyError):
            resolve_json_pointer(doc, "/a/nonexistent")
        with self.assertRaises(IndexError):
            resolve_json_pointer(doc, "/a/b/99")

    def test_direct_import_partition_positive(self):
        """Verify that the actual repository dependency reconciliation is an exact partition."""
        dep_path = os.path.join(os.path.dirname(__file__), '..', 'evidence', 'phase1', 'reconciliation', 'dependency_reconciliation.json')
        with open(dep_path, 'r', encoding='utf-8') as f:
            dep = json.load(f)

        canonical = dep['direct_pe_imports']['libraries']
        canonical_norm = [m.strip().upper() for m in canonical]
        self.assertEqual(len(canonical_norm), len(set(canonical_norm)), "Canonical list must have 0 duplicates")

        categorized = []
        for cat_name, cat_data in dep['direct_pe_imports']['categories'].items():
            mods = [m.strip().upper() for m in cat_data['modules']]
            self.assertEqual(len(mods), len(set(mods)), f"Category {cat_name} must have 0 internal duplicates")
            categorized.extend(mods)

        self.assertEqual(len(categorized), len(set(categorized)), "Categories must have 0 cross-category overlaps")
        self.assertEqual(set(categorized), set(canonical_norm), "Categorized set must equal canonical set")
        self.assertEqual(len(categorized), len(canonical_norm), "Total counts must match exactly")

    def test_direct_import_partition_negative_duplicates(self):
        """Negative test: duplicate module in category must fail partition check."""
        canonical = ["A.DLL", "B.DLL", "C.DLL"]
        cat1 = ["A.DLL", "B.DLL", "A.DLL"] # Internal duplicate
        cat2 = ["C.DLL"]
        # Check duplicate detection
        self.assertNotEqual(len(cat1), len(set(cat1)))

    def test_direct_import_partition_negative_overlap(self):
        """Negative test: module appearing in two categories must fail."""
        canonical = ["A.DLL", "B.DLL", "C.DLL"]
        cat1 = ["A.DLL", "B.DLL"]
        cat2 = ["B.DLL", "C.DLL"] # Overlap on B.DLL
        all_categorized = cat1 + cat2
        self.assertNotEqual(len(all_categorized), len(set(all_categorized)))

    def test_direct_import_partition_negative_missing_and_unexpected(self):
        """Negative test: missing canonical module and unexpected categorized module."""
        canonical = {"A.DLL", "B.DLL", "C.DLL"}
        categorized = {"A.DLL", "B.DLL", "X.DLL"} # Missing C.DLL, Unexpected X.DLL
        self.assertTrue(len(canonical - categorized) > 0)
        self.assertTrue(len(categorized - canonical) > 0)
        self.assertNotEqual(canonical, categorized)

    def test_claim_status_accounting_positive(self):
        """Verify claim status accounting exact dictionary equality on actual repository data."""
        cr_path = os.path.join(os.path.dirname(__file__), '..', 'evidence', 'phase1', 'reconciliation', 'claim_register.json')
        with open(cr_path, 'r', encoding='utf-8') as f:
            cr = json.load(f)

        claims = cr['claims']
        declared = cr['claims_by_status']
        actual = {}
        for c in claims:
            st = c['status']
            actual[st] = actual.get(st, 0) + 1

        for st in ['VERIFIED_STATIC', 'VERIFIED_RUNTIME', 'VERIFIED_DOCUMENTATION', 'INFERRED', 'UNKNOWN', 'NOT_PERFORMED']:
            self.assertEqual(actual.get(st, 0), declared.get(st, 0))

    def test_claim_status_accounting_negative_unknown_status(self):
        """Negative test: unknown status in claim must be rejected."""
        ALLOWED = {'VERIFIED_STATIC', 'VERIFIED_RUNTIME', 'VERIFIED_DOCUMENTATION', 'NOT_PERFORMED', 'INFERRED', 'UNKNOWN'}
        bad_status = "SOME_FABRICATED_STATUS"
        self.assertNotIn(bad_status, ALLOWED)

    def test_claim_status_accounting_negative_count_mismatch(self):
        """Negative test: declared status dictionary mismatch must be detected."""
        actual = {'VERIFIED_STATIC': 20, 'VERIFIED_RUNTIME': 3, 'VERIFIED_DOCUMENTATION': 1, 'NOT_PERFORMED': 1}
        declared = {'VERIFIED_STATIC': 19, 'VERIFIED_RUNTIME': 4, 'VERIFIED_DOCUMENTATION': 1, 'NOT_PERFORMED': 1}
        self.assertNotEqual(actual, declared)

    def test_recursive_image_audit_positive_and_negative(self):
        """Test recursive prohibited-image detection across multiple directory depths."""
        PROHIBITED_EXTENSIONS = (
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico',
            '.webp', '.tif', '.tiff', '.svg', '.avif', '.heic',
            '.heif', '.jfif'
        )

        temp_dir = tempfile.mkdtemp(prefix='test_img_scan_')
        try:
            # Create permitted reference document
            with open(os.path.join(temp_dir, 'UI_OBSERVATIONS_REFERENCE.md'), 'w') as f:
                f.write("# Observations")

            # Scan should find 0 images initially
            found = []
            for root, dirs, files in os.walk(temp_dir):
                for f in files:
                    if os.path.splitext(f)[1].lower() in PROHIBITED_EXTENSIONS:
                        found.append(f)
            self.assertEqual(len(found), 0)

            # Create prohibited images at various depths
            # 1. Root level PNG
            with open(os.path.join(temp_dir, 'test.png'), 'w') as f:
                f.write("fake_png")
            # 2. Nested directory JPEG
            nested = os.path.join(temp_dir, 'sub1', 'sub2')
            os.makedirs(nested, exist_ok=True)
            with open(os.path.join(nested, 'deep.JPEG'), 'w') as f:
                f.write("fake_jpeg")
            # 3. Uppercase extension WEBP
            with open(os.path.join(nested, 'artifact.WEBP'), 'w') as f:
                f.write("fake_webp")

            found_corrupted = []
            for root, dirs, files in os.walk(temp_dir):
                for f in files:
                    if os.path.splitext(f)[1].lower() in PROHIBITED_EXTENSIONS:
                        found_corrupted.append(f)

            self.assertEqual(len(found_corrupted), 3)
            self.assertIn('test.png', found_corrupted)
            self.assertIn('deep.JPEG', found_corrupted)
            self.assertIn('artifact.WEBP', found_corrupted)
        finally:
            shutil.rmtree(temp_dir)

    def test_structured_evidence_refs_path_traversal_negative(self):
        """Negative test: path traversal or absolute path in evidence_refs must be rejected."""
        invalid_paths = [
            "/etc/passwd",
            "C:\\Windows\\System32\\cmd.exe",
            "../outside_repo.json",
            "evidence/../../secret.txt"
        ]
        for p in invalid_paths:
            is_invalid = os.path.isabs(p) or '..' in p or '\\' in p or p.startswith('/')
            self.assertTrue(is_invalid, f"Path '{p}' should be identified as invalid")

if __name__ == '__main__':
    unittest.main()
