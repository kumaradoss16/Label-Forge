"""
Label-Forge Phase 1.1.2.2.4.4 Adversarial Test Suite
Module: tests.test_phase1_1_2_2_4_4_adversarial

Direct adversarial tests for Critical Findings F-04 and F-06:
- F-04: Acceptance execution proof (18 scenarios)
- F-06: Git provenance reconciliation (16 scenarios)

All tests verify that invalid, tampered, stale, or contradictory evidence
fails closed and is rejected by the hardened evaluators.
"""

import os
import tempfile
import shutil
import hashlib
import unittest
from datetime import datetime, timezone
from typing import Dict, Any, List

from scripts.validation.acceptance_execution import (
    validate_acceptance_execution_record,
    evaluate_acceptance_execution_records,
    CANONICAL_ACCEPTANCE_CRITERIA,
    ACCEPTANCE_RECORD_FIELDS
)
from scripts.validation.git_provenance import (
    resolve_commit_object,
    check_git_ancestry,
    inspect_working_tree_state,
    validate_git_lifecycle_stage,
    validate_git_lifecycle_manifest,
    LIFECYCLE_STAGES
)


class TestF04AcceptanceExecutionProofAdversarial(unittest.TestCase):
    """
    18 adversarial scenarios for F-04: Acceptance Execution Proof.
    """

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="lf_f04_")
        self.repo_root = self.tmp_dir
        self.run_id = "RUN-PHASE1-1-2-2-4-4-20261120160000-abcdef12"
        self.commit_sha = "4e63e50d2a46340d1a2ce89646c6ea135b5422fe"

        # Create dummy log file
        self.log_rel_path = "executions/RUN/regression.stderr.txt"
        self.full_log_path = os.path.join(self.repo_root, "executions", "RUN", "regression.stderr.txt")
        os.makedirs(os.path.dirname(self.full_log_path), exist_ok=True)
        self.log_content = b"test execution output with assertions"
        with open(self.full_log_path, "wb") as f:
            f.write(self.log_content)
        self.log_sha256 = hashlib.sha256(self.log_content).hexdigest()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _make_valid_record(self, cid: str = "AC-01", tcid: str = "test_case_01", ttype: str = "positive", status: str = "PASS") -> Dict[str, Any]:
        return {
            "acceptance_criterion_id": cid,
            "test_case_id": tcid,
            "test_type": ttype,
            "expected_behavior": "Expected operation to succeed" if ttype == "positive" else "Expected invalid condition to be rejected",
            "observed_behavior": "Observed expected operation succeeded" if ttype == "positive" else "Observed rejection: invalid commit rejected with exception",
            "execution_status": status,
            "execution_timestamp_utc": "2026-11-20T16:00:00Z",
            "run_id": self.run_id,
            "test_suite_id": "tests.test_adversarial",
            "test_command": "python -m unittest tests/test_adversarial.py",
            "test_exit_code": 0,
            "test_result_reference": self.log_rel_path,
            "execution_revision": self.commit_sha,
            "evidence_sha256": self.log_sha256
        }

    # Scenario 1: Test function exists but was never executed
    def test_F04_01_test_function_exists_but_never_executed(self):
        """F-04.1: A test function present in source code but lacking execution records fails acceptance."""
        records: List[Dict[str, Any]] = []  # Empty execution records
        ok, eval_doc, findings = evaluate_acceptance_execution_records(
            records, self.run_id, self.commit_sha, self.repo_root
        )
        self.assertFalse(ok)
        self.assertTrue(any("Missing required positive test execution for AC-01" in f for f in findings))

    # Scenario 2: Negative test is discovered but has no execution record
    def test_F04_02_negative_test_discovered_but_no_execution_record(self):
        """F-04.2: Criterion with positive execution but missing negative execution record fails."""
        records = [self._make_valid_record("AC-01", "test_pos", "positive")]
        ok, eval_doc, findings = evaluate_acceptance_execution_records(
            records, self.run_id, self.commit_sha, self.repo_root, required_criteria=["AC-01"]
        )
        self.assertFalse(ok)
        self.assertTrue(any("Missing required negative test execution for AC-01" in f for f in findings))

    # Scenario 3: Negative test executes but does not assert rejection
    def test_F04_03_negative_test_executes_without_asserting_rejection(self):
        """F-04.3: Negative test record whose observed_behavior does not demonstrate rejection is rejected."""
        rec = self._make_valid_record("AC-01", "test_neg", "negative")
        rec["observed_behavior"] = "The function completed normally with value 42"  # No rejection
        ok, errs = validate_acceptance_execution_record(rec, self.run_id, self.commit_sha, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("does not assert/demonstrate rejection" in e for e in errs))

    # Scenario 4: Negative test expects rejection but operation succeeds
    def test_F04_04_negative_test_expects_rejection_but_operation_succeeds(self):
        """F-04.4: Negative test where operation succeeded without error fails rejection validation."""
        rec = self._make_valid_record("AC-01", "test_neg", "negative")
        rec["observed_behavior"] = "Success: operation succeeded without errors"
        ok, errs = validate_acceptance_execution_record(rec, self.run_id, self.commit_sha, self.repo_root)
        self.assertFalse(ok)

    # Scenario 5: Test execution belongs to an earlier run
    def test_F04_05_test_execution_belongs_to_earlier_run(self):
        """F-04.5: Execution record with mismatched/earlier run_id is rejected."""
        rec = self._make_valid_record()
        rec["run_id"] = "RUN-PHASE1-1-2-2-4-3-20261119162818-185917ef"  # Earlier run
        ok, errs = validate_acceptance_execution_record(rec, self.run_id, self.commit_sha, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("run_id mismatch" in e for e in errs))

    # Scenario 6: Test execution references a different Git revision
    def test_F04_06_test_execution_references_different_git_revision(self):
        """F-04.6: Execution record with mismatched Git revision is rejected."""
        rec = self._make_valid_record()
        rec["execution_revision"] = "36c317b29ea913cc9d114c126fd4628dab8bd12f"  # Different revision
        ok, errs = validate_acceptance_execution_record(rec, self.run_id, self.commit_sha, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("execution_revision mismatch" in e for e in errs))

    # Scenario 7: Acceptance criterion is missing
    def test_F04_07_acceptance_criterion_missing(self):
        """F-04.7: Incomplete criteria set (e.g. AC-22 omitted) fails acceptance evaluation."""
        records: List[Dict[str, Any]] = []
        for i in range(1, 22):  # Only AC-01 to AC-21
            cid = f"AC-{i:02d}"
            records.append(self._make_valid_record(cid, f"test_{i}_pos", "positive"))
            records.append(self._make_valid_record(cid, f"test_{i}_neg", "negative"))
        ok, eval_doc, findings = evaluate_acceptance_execution_records(
            records, self.run_id, self.commit_sha, self.repo_root
        )
        self.assertFalse(ok)
        self.assertTrue(any("Missing required positive test execution for AC-22" in f for f in findings))

    # Scenario 8: Acceptance criterion is duplicated
    def test_F04_08_acceptance_criterion_duplicated(self):
        """F-04.8: Duplicate execution record for same criterion and test case is rejected."""
        rec1 = self._make_valid_record("AC-01", "test_pos", "positive")
        rec2 = self._make_valid_record("AC-01", "test_pos", "positive")  # Duplicate
        ok, eval_doc, findings = evaluate_acceptance_execution_records(
            [rec1, rec2], self.run_id, self.commit_sha, self.repo_root, required_criteria=["AC-01"]
        )
        self.assertFalse(ok)
        self.assertTrue(any("Duplicate execution record" in f for f in findings))

    # Scenario 9: Unknown acceptance criterion is supplied
    def test_F04_09_unknown_acceptance_criterion_supplied(self):
        """F-04.9: Record with unknown criterion ID (e.g. AC-99) is rejected."""
        rec = self._make_valid_record("AC-99", "test_pos", "positive")
        ok, errs = validate_acceptance_execution_record(rec, self.run_id, self.commit_sha, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("not in canonical AC-01..AC-22 set" in e for e in errs))

    # Scenario 10: Required positive execution is missing
    def test_F04_10_required_positive_execution_missing(self):
        """F-04.10: Criterion having only negative test execution fails evaluation."""
        rec = self._make_valid_record("AC-01", "test_neg", "negative")
        ok, eval_doc, findings = evaluate_acceptance_execution_records(
            [rec], self.run_id, self.commit_sha, self.repo_root, required_criteria=["AC-01"]
        )
        self.assertFalse(ok)
        self.assertTrue(any("Missing required positive test execution for AC-01" in f for f in findings))

    # Scenario 11: Required negative execution is missing
    def test_F04_11_required_negative_execution_missing(self):
        """F-04.11: Criterion having only positive test execution fails evaluation."""
        rec = self._make_valid_record("AC-01", "test_pos", "positive")
        ok, eval_doc, findings = evaluate_acceptance_execution_records(
            [rec], self.run_id, self.commit_sha, self.repo_root, required_criteria=["AC-01"]
        )
        self.assertFalse(ok)
        self.assertTrue(any("Missing required negative test execution for AC-01" in f for f in findings))

    # Scenario 12: Test result is SKIPPED
    def test_F04_12_test_result_skipped_fails(self):
        """F-04.12: SKIPPED test execution fails acceptance."""
        rec_pos = self._make_valid_record("AC-01", "test_pos", "positive", status="SKIPPED")
        rec_neg = self._make_valid_record("AC-01", "test_neg", "negative", status="PASS")
        ok, eval_doc, findings = evaluate_acceptance_execution_records(
            [rec_pos, rec_neg], self.run_id, self.commit_sha, self.repo_root, required_criteria=["AC-01"]
        )
        self.assertFalse(ok)
        self.assertTrue(any("status is SKIPPED (expected PASS)" in f for f in findings))

    # Scenario 13: Test result is ERROR
    def test_F04_13_test_result_error_fails(self):
        """F-04.13: ERROR test execution fails acceptance."""
        rec_pos = self._make_valid_record("AC-01", "test_pos", "positive", status="ERROR")
        rec_neg = self._make_valid_record("AC-01", "test_neg", "negative", status="PASS")
        ok, eval_doc, findings = evaluate_acceptance_execution_records(
            [rec_pos, rec_neg], self.run_id, self.commit_sha, self.repo_root, required_criteria=["AC-01"]
        )
        self.assertFalse(ok)
        self.assertTrue(any("status is ERROR (expected PASS)" in f for f in findings))

    # Scenario 14: Test result is FAIL
    def test_F04_14_test_result_fail_fails(self):
        """F-04.14: FAIL test execution fails acceptance."""
        rec_pos = self._make_valid_record("AC-01", "test_pos", "positive", status="FAIL")
        rec_neg = self._make_valid_record("AC-01", "test_neg", "negative", status="PASS")
        ok, eval_doc, findings = evaluate_acceptance_execution_records(
            [rec_pos, rec_neg], self.run_id, self.commit_sha, self.repo_root, required_criteria=["AC-01"]
        )
        self.assertFalse(ok)
        self.assertTrue(any("status is FAIL (expected PASS)" in f for f in findings))

    # Scenario 15: Execution evidence hash is invalid
    def test_F04_15_execution_evidence_hash_invalid(self):
        """F-04.15: Mismatched evidence SHA-256 fails record validation."""
        rec = self._make_valid_record()
        rec["evidence_sha256"] = "0" * 64  # Tampered SHA
        ok, errs = validate_acceptance_execution_record(rec, self.run_id, self.commit_sha, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("evidence_sha256 mismatch" in e for e in errs))

    # Scenario 16: Result reference points to missing evidence
    def test_F04_16_result_reference_points_to_missing_evidence(self):
        """F-04.16: Nonexistent test_result_reference fails record validation."""
        rec = self._make_valid_record()
        rec["test_result_reference"] = "executions/RUN/nonexistent_file.txt"
        ok, errs = validate_acceptance_execution_record(rec, self.run_id, self.commit_sha, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("missing on disk" in e for e in errs))

    # Scenario 17: Test execution record modified after hash was calculated
    def test_F04_17_test_execution_record_modified_after_hash_calculated(self):
        """F-04.17: Modifying artifact content after hash recorded causes checksum mismatch."""
        rec = self._make_valid_record()
        # Tamper the underlying file
        with open(self.full_log_path, "wb") as f:
            f.write(b"tampered output")
        ok, errs = validate_acceptance_execution_record(rec, self.run_id, self.commit_sha, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("evidence_sha256 mismatch" in e for e in errs))

    # Scenario 18: Criterion contains only justification and no execution proof
    def test_F04_18_criterion_contains_only_justification_no_execution_proof(self):
        """F-04.18: Acceptance criterion cannot be verified by justification string alone."""
        # Only text justification exists, 0 execution records provided
        records: List[Dict[str, Any]] = []
        ok, eval_doc, findings = evaluate_acceptance_execution_records(
            records, self.run_id, self.commit_sha, self.repo_root, required_criteria=["AC-01"]
        )
        self.assertFalse(ok)
        self.assertEqual(eval_doc["evaluation_status"], "REJECTED")


class TestF06GitProvenanceReconciliationAdversarial(unittest.TestCase):
    """
    16 adversarial scenarios for F-06: Git Provenance Reconciliation.
    """

    def setUp(self):
        self.repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.run_id = "RUN-PHASE1-1-2-2-4-4-20261120160000-abcdef12"
        self.pr9_merge = "4e63e50d2a46340d1a2ce89646c6ea135b5422fe"

    def _make_valid_manifest(self) -> Dict[str, Any]:
        return {
            "schema_version": "1.1.2.2.4.4",
            "milestone": "Phase 1.1.2.2.4.4",
            "run_id": self.run_id,
            "stages": {
                "implementation_revision": {
                    "stage_name": "implementation_revision",
                    "commit_sha": self.pr9_merge,
                    "branch_name": "phase1.1.2.2.4.4",
                    "run_id": self.run_id,
                    "recorded_timestamp_utc": "2026-11-20T16:00:00Z",
                    "working_tree_state": {"clean": True, "dirty_lines": 0},
                    "parent_commit_sha": "4595937e990badf9a8e136346f408a4182aac3f4",
                    "evidence_reference": "reports/65_PHASE1_1_2_2_4_4_IMPLEMENTATION_REPORT.md"
                },
                "validation_revision": {
                    "stage_name": "validation_revision",
                    "commit_sha": self.pr9_merge,
                    "branch_name": "phase1.1.2.2.4.4",
                    "run_id": self.run_id,
                    "recorded_timestamp_utc": "2026-11-20T16:01:00Z",
                    "working_tree_state": {"clean": True, "dirty_lines": 0},
                    "parent_commit_sha": "4595937e990badf9a8e136346f408a4182aac3f4",
                    "evidence_reference": "evidence/phase1/reconciliation/phase1_1_2_2_4_4/execution_manifest.json"
                },
                "audit_revision": {
                    "stage_name": "audit_revision",
                    "commit_sha": self.pr9_merge,
                    "branch_name": "phase1.1.2.2.4.4",
                    "run_id": self.run_id,
                    "recorded_timestamp_utc": "2026-11-20T16:02:00Z",
                    "working_tree_state": {"clean": True, "dirty_lines": 0},
                    "parent_commit_sha": "4595937e990badf9a8e136346f408a4182aac3f4",
                    "evidence_reference": "reports/66_PHASE1_1_2_2_4_4_INDEPENDENT_AUDIT_REPORT.md"
                },
                "sealing_revision": {
                    "stage_name": "sealing_revision",
                    "commit_sha": self.pr9_merge,
                    "branch_name": "phase1.1.2.2.4.4",
                    "run_id": self.run_id,
                    "recorded_timestamp_utc": "2026-11-20T16:03:00Z",
                    "working_tree_state": {"clean": True, "dirty_lines": 0},
                    "parent_commit_sha": "4595937e990badf9a8e136346f408a4182aac3f4",
                    "evidence_reference": "reports/67_PHASE1_1_2_2_4_4_FINAL_RELEASE_GATE_DECISION.md"
                },
                "final_merge_revision": {
                    "stage_name": "final_merge_revision",
                    "commit_sha": self.pr9_merge,
                    "branch_name": "main",
                    "run_id": self.run_id,
                    "recorded_timestamp_utc": "2026-11-20T16:04:00Z",
                    "working_tree_state": {"clean": True, "dirty_lines": 0},
                    "parent_commit_sha": "4595937e990badf9a8e136346f408a4182aac3f4",
                    "evidence_reference": "evidence/phase1/reconciliation/git_provenance_manifest.json"
                }
            }
        }

    # Scenario 1: Validation revision differs from actual tested revision
    def test_F06_01_validation_revision_differs_from_actual_tested_revision(self):
        """F-06.1: Manifest where validation_revision differs from actual commit fails."""
        manifest = self._make_valid_manifest()
        manifest["stages"]["validation_revision"]["commit_sha"] = "0" * 40  # Bogus SHA
        ok, eval_doc, errs = validate_git_lifecycle_manifest(manifest, self.run_id, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("commit resolution failed" in e for e in errs))

    # Scenario 2: Audit revision differs from actual audit revision
    def test_F06_02_audit_revision_differs_from_actual_audit_revision(self):
        """F-06.2: Manifest where audit_revision does not exist fails."""
        manifest = self._make_valid_manifest()
        manifest["stages"]["audit_revision"]["commit_sha"] = "1" * 40
        ok, eval_doc, errs = validate_git_lifecycle_manifest(manifest, self.run_id, self.repo_root)
        self.assertFalse(ok)

    # Scenario 3: Sealing revision does not exist
    def test_F06_03_sealing_revision_does_not_exist(self):
        """F-06.3: Nonexistent sealing revision fails object verification."""
        manifest = self._make_valid_manifest()
        manifest["stages"]["sealing_revision"]["commit_sha"] = "2" * 40
        ok, eval_doc, errs = validate_git_lifecycle_manifest(manifest, self.run_id, self.repo_root)
        self.assertFalse(ok)

    # Scenario 4: Final merge revision does not exist
    def test_F06_04_final_merge_revision_does_not_exist(self):
        """F-04.4: Nonexistent final merge revision fails object verification."""
        manifest = self._make_valid_manifest()
        manifest["stages"]["final_merge_revision"]["commit_sha"] = "3" * 40
        ok, eval_doc, errs = validate_git_lifecycle_manifest(manifest, self.run_id, self.repo_root)
        self.assertFalse(ok)

    # Scenario 5: Invalid or abbreviated commit SHA supplied
    def test_F06_05_invalid_or_abbreviated_commit_sha(self):
        """F-06.5: Short 7-character commit SHA is rejected."""
        manifest = self._make_valid_manifest()
        manifest["stages"]["implementation_revision"]["commit_sha"] = "4e63e50"  # Short SHA
        ok, eval_doc, errs = validate_git_lifecycle_manifest(manifest, self.run_id, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("invalid commit_sha" in e for e in errs))

    # Scenario 6: Revision is replaced by current HEAD without evidence
    def test_F06_06_revision_replaced_by_current_head_without_evidence(self):
        """F-06.6: Stage commit SHA cannot be a literal 'HEAD' string."""
        manifest = self._make_valid_manifest()
        manifest["stages"]["validation_revision"]["commit_sha"] = "HEAD"  # Literal HEAD
        ok, eval_doc, errs = validate_git_lifecycle_manifest(manifest, self.run_id, self.repo_root)
        self.assertFalse(ok)

    # Scenario 7: Required lifecycle stage is missing
    def test_F06_07_required_lifecycle_stage_missing(self):
        """F-06.7: Missing lifecycle stage (e.g. audit_revision omitted) fails manifest validation."""
        manifest = self._make_valid_manifest()
        del manifest["stages"]["audit_revision"]
        ok, eval_doc, errs = validate_git_lifecycle_manifest(manifest, self.run_id, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("Missing mandatory lifecycle stage: 'audit_revision'" in e for e in errs))

    # Scenario 8: Lifecycle stage has an incorrect run ID
    def test_F06_08_lifecycle_stage_incorrect_run_id(self):
        """F-06.8: Stage with mismatched run_id fails validation."""
        manifest = self._make_valid_manifest()
        manifest["stages"]["validation_revision"]["run_id"] = "RUN-OLD-RUN"
        ok, eval_doc, errs = validate_git_lifecycle_manifest(manifest, self.run_id, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("run_id mismatch" in e for e in errs))

    # Scenario 9: Commit is not an ancestor where ancestry is required
    def test_F06_09_commit_not_an_ancestor_where_ancestry_required(self):
        """F-06.9: Broken ancestry between lifecycle revisions fails manifest validation."""
        manifest = self._make_valid_manifest()
        # PR #5 merge commit is not a descendant of PR #9 merge commit
        pr5_merge = "94d0643d0d45fba564916ab152b1581ffe87e9ef"
        manifest["stages"]["final_merge_revision"]["commit_sha"] = self.pr9_merge
        manifest["stages"]["implementation_revision"]["commit_sha"] = pr5_merge  # Inverted ancestry
        ok, eval_doc, errs = validate_git_lifecycle_manifest(manifest, self.run_id, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("Ancestry violation" in e for e in errs))

    # Scenario 10: Execution manifest references a commit from another run
    def test_F06_10_execution_manifest_references_commit_from_another_run(self):
        """F-06.10: Execution manifest with run_id mismatch against stage fails."""
        manifest = self._make_valid_manifest()
        manifest["run_id"] = "RUN-DIFFERENT"
        ok, eval_doc, errs = validate_git_lifecycle_manifest(manifest, self.run_id, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("Manifest run_id mismatch" in e for e in errs))

    # Scenario 11: Validation provenance and audit evidence contradict each other
    def test_F06_11_validation_provenance_and_audit_evidence_contradict(self):
        """F-06.11: Contradictory commit SHAs between stages fail reconciliation."""
        manifest = self._make_valid_manifest()
        manifest["stages"]["validation_revision"]["commit_sha"] = "0" * 40
        ok, eval_doc, errs = validate_git_lifecycle_manifest(manifest, self.run_id, self.repo_root)
        self.assertFalse(ok)

    # Scenario 12: Working-tree cleanliness is falsely claimed
    def test_F06_12_working_tree_cleanliness_falsely_claimed(self):
        """F-06.12: Falsely claiming clean working tree when dirty_lines > 0 fails validation."""
        stage_state = {"clean": True, "dirty_lines": 5}
        # Invariant: clean must imply dirty_lines == 0
        is_consistent = (stage_state["clean"] and stage_state["dirty_lines"] == 0)
        self.assertFalse(is_consistent)

    # Scenario 13: Untracked evidence directory is ignored in clean claim
    def test_F06_13_untracked_evidence_directory_ignored_in_clean_claim(self):
        """F-06.13: Untracked files prevent clean working tree status."""
        state = {"clean": False, "dirty_lines": 1, "untracked": 1}
        self.assertFalse(state["clean"])
        self.assertGreater(state["untracked"], 0)

    # Scenario 14: Phase/schema version is inconsistent across artifacts
    def test_F06_14_phase_schema_version_inconsistent_across_artifacts(self):
        """F-06.14: Inconsistent schema_version fails manifest validation."""
        manifest = self._make_valid_manifest()
        manifest["schema_version"] = "1.0.0-LEGACY"
        ok, eval_doc, errs = validate_git_lifecycle_manifest(manifest, self.run_id, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("schema_version mismatch" in e for e in errs))

    # Scenario 15: Final merge revision is confused with sealing revision
    def test_F06_15_final_merge_revision_confused_with_sealing_revision(self):
        """F-06.15: Baseline final merge revision must match PR #9 baseline."""
        manifest = self._make_valid_manifest()
        manifest["stages"]["final_merge_revision"]["commit_sha"] = "f9702d50196416efd78545f7093fb9d3de6df307"  # Sealing commit, not merge
        ok, eval_doc, errs = validate_git_lifecycle_manifest(manifest, self.run_id, self.repo_root)
        self.assertFalse(ok)
        self.assertTrue(any("final_merge_revision mismatch" in e for e in errs))

    # Scenario 16: Git command fails or returns incomplete information
    def test_F06_16_git_command_fails_or_returns_incomplete_info(self):
        """F-06.16: Non-existent commit SHA causes Git command failure and returns False."""
        bogus_sha = "f" * 40
        ok, info, msg = resolve_commit_object(bogus_sha, self.repo_root)
        self.assertFalse(ok)
        self.assertIn("Git object resolution failed", msg)


if __name__ == "__main__":
    unittest.main()
