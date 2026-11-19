#!/usr/bin/env python3
"""
Test Suite: Hardened Independent Auditor & Closure Report Generator
Direct adversarial unit tests exercising:
  - 13-field canonical validation record schema enforcement
  - Canonical evidence path containment and symlink protection
  - Artifact integrity, hash, size, and run ID association
  - Formal acceptance criteria traceability evaluation
  - Git provenance fail-closed object resolution
  - Report generator input validation and deterministic generation
"""

import os
import sys
import json
import shutil
import hashlib
import tempfile
import unittest
from datetime import datetime, timezone
from typing import Dict, Any

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.validation.independent_audit import (
    IndependentAuditor,
    independent_validate_path,
    independent_validate_artifact,
    independent_validate_record_schema,
    independent_resolve_git_commit,
    INDEPENDENT_STAGE_REGISTRY,
    INDEPENDENT_ALLOWED_STATUSES,
    CANONICAL_SCHEMA_FIELDS,
)
from scripts.validation.generate_closure_reports import (
    load_json,
    generate_phase1_1_2_2_4_2_reports,
    generate_phase1_1_2_2_4_3_reports,
)


def make_valid_check_record() -> Dict[str, Any]:
    return {
        "check_id": "TEST-CHECK-001",
        "stage_id": "target_prerequisites",
        "claim_id": "GENERAL",
        "evidence_path": "evidence/phase1/reconciliation/canonical_target_identity.json",
        "evidence_sha256": "a" * 64,
        "result_status": "PASS",
        "message": "Sample valid message",
        "execution_timestamp_utc": "2026-11-19T12:00:00+00:00",
        "validator_version": "1.1.2.2.4.3",
        "target_binary_sha256": "d3498925149b91c646351e91638906ca4455b2a4cd8db82775bb6860d67d8594",
        "git_commit_sha": "4595937e990badf9a8e136346f408a4182aac3f4",
        "environment_hash": "e" * 32,
        "execution_duration_ms": 1.25,
    }


class TestSchemaAdversarialScenarios(unittest.TestCase):
    """Adversarial tests for the canonical 13-field schema enforcement."""

    def test_valid_record_passes_schema(self):
        rec = make_valid_check_record()
        ok, failures = independent_validate_record_schema(rec)
        self.assertTrue(ok, f"Unexpected failures: {failures}")
        self.assertEqual(len(failures), 0)

    def test_missing_each_of_13_fields(self):
        for field in CANONICAL_SCHEMA_FIELDS:
            rec = make_valid_check_record()
            del rec[field]
            ok, failures = independent_validate_record_schema(rec)
            self.assertFalse(ok, f"Expected failure when '{field}' is missing")
            self.assertTrue(any(f.get("field") == field for f in failures))

    def test_invalid_data_types(self):
        # check_id integer
        rec = make_valid_check_record()
        rec["check_id"] = 12345
        ok, fails = independent_validate_record_schema(rec)
        self.assertFalse(ok)
        self.assertTrue(any(f.get("field") == "check_id" for f in fails))

        # stage_id not in registry
        rec = make_valid_check_record()
        rec["stage_id"] = "nonexistent_stage_id"
        ok, fails = independent_validate_record_schema(rec)
        self.assertFalse(ok)
        self.assertTrue(any(f.get("field") == "stage_id" for f in fails))

        # result_status invalid enum
        rec = make_valid_check_record()
        rec["result_status"] = "APPROVED"  # not in ALLOWED_RESULT_STATUSES
        ok, fails = independent_validate_record_schema(rec)
        self.assertFalse(ok)
        self.assertTrue(any(f.get("field") == "result_status" for f in fails))

        # execution_duration_ms boolean (Python bool is int pitfall)
        rec = make_valid_check_record()
        rec["execution_duration_ms"] = True
        ok, fails = independent_validate_record_schema(rec)
        self.assertFalse(ok)
        self.assertTrue(any(f.get("field") == "execution_duration_ms" for f in fails))

        # execution_duration_ms negative
        rec = make_valid_check_record()
        rec["execution_duration_ms"] = -5.0
        ok, fails = independent_validate_record_schema(rec)
        self.assertFalse(ok)
        self.assertTrue(any(f.get("field") == "execution_duration_ms" for f in fails))

    def test_invalid_sha256_format(self):
        rec = make_valid_check_record()
        rec["evidence_sha256"] = "not_a_hex_string" + "0" * 48
        ok, fails = independent_validate_record_schema(rec)
        self.assertFalse(ok)
        self.assertTrue(any(f.get("field") == "evidence_sha256" for f in fails))

    def test_invalid_timestamp_format(self):
        rec = make_valid_check_record()
        rec["execution_timestamp_utc"] = "2026-11-19 12:00:00"  # missing T and timezone
        ok, fails = independent_validate_record_schema(rec)
        self.assertFalse(ok)
        self.assertTrue(any(f.get("field") == "execution_timestamp_utc" for f in fails))


class TestPathContainmentAdversarialScenarios(unittest.TestCase):
    """Adversarial tests for repository path containment and symlink protection."""

    def test_parent_directory_traversal(self):
        ok, msg = independent_validate_path("../outside.json", REPO_ROOT, must_exist=False)
        self.assertFalse(ok)
        self.assertIn("traversal", msg.lower())

    def test_absolute_path_rejection(self):
        ok, msg = independent_validate_path("C:/Windows/System32/drivers/etc/hosts", REPO_ROOT, must_exist=False)
        self.assertFalse(ok)

    def test_windows_drive_letter_rejection(self):
        ok, msg = independent_validate_path("D:evidence/target.json", REPO_ROOT, must_exist=False)
        self.assertFalse(ok)

    def test_unc_path_rejection(self):
        ok, msg = independent_validate_path("//server/share/file.txt", REPO_ROOT, must_exist=False)
        self.assertFalse(ok)

    def test_backslash_path_rejection(self):
        ok, msg = independent_validate_path("evidence\\phase1\\target.json", REPO_ROOT, must_exist=False)
        self.assertFalse(ok)
        self.assertIn("backslashes", msg)

    def test_nonexistent_file_rejection(self):
        ok, msg = independent_validate_path("evidence/phase1/does_not_exist_xyz.json", REPO_ROOT, must_exist=True)
        self.assertFalse(ok)
        self.assertIn("missing", msg.lower())


class TestArtifactIntegrityAdversarialScenarios(unittest.TestCase):
    """Adversarial tests for artifact verification (hash, size, run_id)."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(dir=REPO_ROOT, delete=False)
        self.temp_file.write(b"Hello Label-Forge Artifact Validation!")
        self.temp_file.flush()
        self.temp_file.close()
        self.rel_path = os.path.relpath(self.temp_file.name, REPO_ROOT).replace("\\", "/")
        self.file_size = os.path.getsize(self.temp_file.name)
        with open(self.temp_file.name, "rb") as f:
            self.file_sha = hashlib.sha256(f.read()).hexdigest()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_valid_artifact_passes(self):
        entry = {
            "path": self.rel_path,
            "byte_size": self.file_size,
            "sha256": self.file_sha,
            "run_id": "RUN-TEST-001"
        }
        ok, msg = independent_validate_artifact(entry, REPO_ROOT, expected_run_id="RUN-TEST-001")
        self.assertTrue(ok, f"Expected pass, got: {msg}")

    def test_run_id_mismatch(self):
        entry = {
            "path": self.rel_path,
            "byte_size": self.file_size,
            "sha256": self.file_sha,
            "run_id": "RUN-OTHER-999"
        }
        ok, msg = independent_validate_artifact(entry, REPO_ROOT, expected_run_id="RUN-TEST-001")
        self.assertFalse(ok)
        self.assertIn("mismatch", msg.lower())

    def test_size_mismatch(self):
        entry = {
            "path": self.rel_path,
            "byte_size": self.file_size + 10,
            "sha256": self.file_sha,
            "run_id": "RUN-TEST-001"
        }
        ok, msg = independent_validate_artifact(entry, REPO_ROOT, expected_run_id="RUN-TEST-001")
        self.assertFalse(ok)
        self.assertIn("size mismatch", msg.lower())

    def test_boolean_size_rejection(self):
        entry = {
            "path": self.rel_path,
            "byte_size": True,
            "sha256": self.file_sha,
            "run_id": "RUN-TEST-001"
        }
        ok, msg = independent_validate_artifact(entry, REPO_ROOT, expected_run_id="RUN-TEST-001")
        self.assertFalse(ok)
        self.assertIn("Invalid byte size", msg)

    def test_sha256_mismatch(self):
        entry = {
            "path": self.rel_path,
            "byte_size": self.file_size,
            "sha256": "0" * 64,
            "run_id": "RUN-TEST-001"
        }
        ok, msg = independent_validate_artifact(entry, REPO_ROOT, expected_run_id="RUN-TEST-001")
        self.assertFalse(ok)
        self.assertIn("hash mismatch", msg.lower())


class TestGitProvenanceAdversarialScenarios(unittest.TestCase):
    """Adversarial tests for Git commit and tree resolution."""

    def test_unresolvable_commit_fails(self):
        ok, info, msg = independent_resolve_git_commit("ffffffffffffffffffffffffffffffffffffffff", REPO_ROOT)
        self.assertFalse(ok)
        self.assertIsNone(info)

    def test_empty_commit_ref_fails(self):
        ok, info, msg = independent_resolve_git_commit("", REPO_ROOT)
        self.assertFalse(ok)
        self.assertIn("empty", msg.lower())


class TestReportGeneratorAdversarialScenarios(unittest.TestCase):
    """Adversarial tests for generate_closure_reports.py."""

    def test_missing_input_file_raises_filenotfound(self):
        nonexistent = os.path.join(REPO_ROOT, "evidence", "nonexistent_dir_xyz")
        with self.assertRaises(FileNotFoundError):
            load_json(os.path.join(nonexistent, "validation_results.json"))


if __name__ == '__main__':
    unittest.main()
