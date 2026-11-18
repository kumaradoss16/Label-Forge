#!/usr/bin/env python3
"""
Test Suite: Decoupled Independent Auditor Architecture & Invariants
Verifies that scripts/validation/independent_audit.py is 100% decoupled from
production validation helpers and enforces strict fail-closed verification.
"""

import os
import sys
import ast
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.validation.independent_audit import (
    IndependentAuditor,
    independent_resolve_git_commit,
    independent_validate_artifact,
    INDEPENDENT_STAGE_REGISTRY,
    INDEPENDENT_ALLOWED_STATUSES,
)


class TestDecoupledIndependentAuditor(unittest.TestCase):
    """Verifies that the independent auditor has zero coupling with production validation modules."""

    def test_auditor_imports_zero_production_validation_modules(self):
        """AST audit: independent_audit.py must import ONLY Python standard library."""
        audit_script = os.path.join(REPO_ROOT, 'scripts', 'validation', 'independent_audit.py')
        self.assertTrue(os.path.exists(audit_script), f"Missing {audit_script}")

        with open(audit_script, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=audit_script)

        forbidden_prefixes = ('scripts.validation', 'scripts', 'validation')
        imported_modules = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.append(node.module)

        for mod in imported_modules:
            for prefix in forbidden_prefixes:
                self.assertFalse(
                    mod == prefix or mod.startswith(prefix + '.'),
                    f"Forbidden production module import detected in independent auditor: '{mod}'"
                )

    def test_independent_artifact_validation_rejects_traversal(self):
        """Auditor artifact validation rejects parent directory traversal."""
        bad_entry = {
            "path": "../secret_file.txt",
            "sha256": "0" * 64,
            "size_bytes": 10
        }
        ok, msg = independent_validate_artifact(bad_entry, REPO_ROOT)
        self.assertFalse(ok)
        self.assertIn("Invalid artifact path", msg)

    def test_independent_artifact_validation_rejects_absolute_path(self):
        """Auditor artifact validation rejects absolute paths."""
        bad_entry = {
            "path": "C:/Windows/System32/cmd.exe",
            "sha256": "0" * 64,
            "size_bytes": 10
        }
        ok, msg = independent_validate_artifact(bad_entry, REPO_ROOT)
        self.assertFalse(ok)

    def test_independent_artifact_validation_hash_mismatch(self):
        """Auditor artifact validation detects altered file content."""
        with tempfile.NamedTemporaryFile(dir=REPO_ROOT, delete=False) as tf:
            tf.write(b"genuine_content")
            temp_path = tf.name

        try:
            rel_path = os.path.relpath(temp_path, REPO_ROOT).replace('\\', '/')
            entry = {
                "path": rel_path,
                "sha256": "badbeef" * 9 + "0",
                "size_bytes": len(b"genuine_content")
            }
            ok, msg = independent_validate_artifact(entry, REPO_ROOT)
            self.assertFalse(ok)
            self.assertIn("hash mismatch", msg)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_independent_git_resolve_invalid_commit(self):
        """Auditor git resolver safely fails on nonexistent commit."""
        ok, info, msg = independent_resolve_git_commit("deadbeef" * 5, REPO_ROOT)
        self.assertFalse(ok)
        self.assertIsNone(info)

    def test_independent_auditor_stage_registry_completeness(self):
        """Auditor stage registry contains all 10 canonical stages."""
        expected_stages = {
            "target_prerequisites",
            "target_binary_integrity",
            "manifest_integrity",
            "component_inventory",
            "direct_import_partition",
            "status_accounting",
            "evidence_references",
            "claim_specific_assertions",
            "recursive_image_audit",
            "report_consistency",
        }
        self.assertEqual(set(INDEPENDENT_STAGE_REGISTRY), expected_stages)

    def test_independent_auditor_allowed_statuses(self):
        """Auditor allows strictly the 6 standard status tokens."""
        expected_statuses = {"PASS", "FAIL", "WARNING", "BLOCKED", "NOT_CHECKED", "NOT_APPLICABLE"}
        self.assertEqual(set(INDEPENDENT_ALLOWED_STATUSES), expected_statuses)


if __name__ == '__main__':
    unittest.main()
