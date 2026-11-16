#!/usr/bin/env python3
"""
Label-Forge Phase 1.1.2.2.4 Independent Evidence Integrity Auditor
Performs strict, independent recalculation and audit of all evidence,
Git provenance, validation records, stage accounting, acceptance matrix,
and execution artifacts without trusting generated summaries.

Exit Codes:
  0: PASS (All invariants independently verified)
  1: FAIL (Discrepancy, missing evidence, hash mismatch, or unverified criterion)
"""

import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.validation.stage_results import STAGE_REGISTRY, ALLOWED_RESULT_STATUSES
from scripts.validation.git_verification import resolve_git_commit_and_tree, verify_final_merge_equivalence
from scripts.validation.evidence_integrity import validate_execution_artifact

EVIDENCE_DIR = os.path.join(REPO_ROOT, 'evidence', 'phase1')
RECON_DIR = os.path.join(EVIDENCE_DIR, 'reconciliation')


class IndependentAuditor:
    def __init__(self, repo_root: str = REPO_ROOT):
        self.repo_root = repo_root
        self.findings = []
        self.invariants_passed = 0
        self.invariants_failed = 0
        self.audit_log = []

    def log(self, msg: str):
        self.audit_log.append(msg)
        print(msg)

    def assert_invariant(self, invariant_name: str, condition: bool, detail: str = ""):
        if condition:
            self.invariants_passed += 1
            self.log(f"  [PASS] {invariant_name}" + (f" ({detail})" if detail else ""))
        else:
            self.invariants_failed += 1
            self.findings.append(f"{invariant_name}: {detail}")
            self.log(f"  [FAIL] {invariant_name}: {detail}")

    def audit_git_objects_and_provenance(self) -> Dict[str, Any]:
        self.log("\n[INDEPENDENT AUDIT 1] Git Objects & PR #5 Revision Provenance")
        pr5_commit = "94d0643d0d45fba564916ab152b1581ffe87e9ef"
        pr5_expected_tree = "0891300af884bd8820b2ceadbbca6b4d8a4865fd"
        sealing_commit = "6a93ed886f9c3e2f23c5918c9ca21e11c89bfaec"

        # 1. PR #5 merge commit object
        ok_pr5, info_pr5, msg_pr5 = resolve_git_commit_and_tree(pr5_commit, self.repo_root)
        self.assert_invariant("INV-GIT-01: PR #5 merge commit object exists", ok_pr5, msg_pr5)
        
        pr5_tree = info_pr5['tree_sha'] if (ok_pr5 and info_pr5) else None
        self.assert_invariant(
            "INV-GIT-02: PR #5 merge tree SHA matches expected",
            pr5_tree == pr5_expected_tree,
            f"actual={pr5_tree}, expected={pr5_expected_tree}"
        )

        # 2. Sealing commit object
        ok_seal, info_seal, msg_seal = resolve_git_commit_and_tree(sealing_commit, self.repo_root)
        self.assert_invariant("INV-GIT-03: Phase 1.1.2.2.3 sealing commit object exists", ok_seal, msg_seal)

        seal_tree = info_seal['tree_sha'] if (ok_seal and info_seal) else None
        self.assert_invariant(
            "INV-GIT-04: PR #5 merge commit is TREE_EQUIVALENT to sealing commit",
            (pr5_tree is not None and pr5_tree == seal_tree),
            f"pr5_tree={pr5_tree}, seal_tree={seal_tree}"
        )

        # 3. Current HEAD commit and tree
        try:
            head_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.repo_root).decode('utf-8').strip()
            head_tree = subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=self.repo_root).decode('utf-8').strip()
            ok_head = True
        except Exception as e:
            head_commit = "ERROR"
            head_tree = "ERROR"
            ok_head = False
        self.assert_invariant("INV-GIT-05: Current HEAD commit resolved", ok_head, f"commit={head_commit}")

        # 4. Working tree cleanliness (non-evidence files must be clean)
        try:
            porcelain = subprocess.check_output(['git', 'status', '--porcelain'], cwd=self.repo_root).decode('utf-8').strip()
            dirty_lines = [
                l for l in porcelain.splitlines()
                if l.strip() and not ('evidence/phase1/reconciliation/' in l or 'evidence\\phase1\\reconciliation\\' in l)
            ]
            is_clean = len(dirty_lines) == 0
        except Exception:
            is_clean = False
        self.assert_invariant("INV-GIT-06: Working tree cleanliness verified", is_clean, f"dirty_lines={len(dirty_lines) if 'dirty_lines' in locals() else 'unknown'}")

        return {
            'pr5_merge_commit': pr5_commit,
            'pr5_merge_tree': pr5_tree,
            'sealing_commit': sealing_commit,
            'sealing_tree': seal_tree,
            'head_commit': head_commit,
            'head_tree': head_tree,
            'is_clean': is_clean
        }

    def audit_validation_records(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        self.log("\n[INDEPENDENT AUDIT 2] Raw Validation Records Inspection")
        results_path = os.path.join(RECON_DIR, 'validation_results.json')
        self.assert_invariant("INV-REC-01: validation_results.json exists", os.path.exists(results_path), results_path)

        with open(results_path, 'r', encoding='utf-8') as f:
            doc = json.load(f)

        checks = doc.get('checks', [])
        self.assert_invariant("INV-REC-02: Checks list is populated", len(checks) > 0, f"count={len(checks)}")

        # Check-ID uniqueness
        check_ids = [c.get('check_id') for c in checks]
        id_set = set()
        duplicate_ids = []
        for cid in check_ids:
            if not cid:
                duplicate_ids.append("EMPTY_ID")
            elif cid in id_set:
                duplicate_ids.append(cid)
            else:
                id_set.add(cid)
        self.assert_invariant("INV-REC-03: Every check_id is unique and non-empty", len(duplicate_ids) == 0, f"duplicates={duplicate_ids}")

        # Valid stage_id for every record
        empty_stages = [c.get('check_id') for c in checks if not c.get('stage_id')]
        unknown_stages = [c.get('check_id') for c in checks if c.get('stage_id') and c.get('stage_id') not in STAGE_REGISTRY]
        self.assert_invariant("INV-REC-04: Zero checks with empty stage_id", len(empty_stages) == 0, f"empty={len(empty_stages)}")
        self.assert_invariant("INV-REC-05: Zero checks with unknown stage_id", len(unknown_stages) == 0, f"unknown={len(unknown_stages)}")

        # Evidence references validity
        missing_refs = []
        unresolvable_refs = []
        for c in checks:
            cid = c.get('check_id')
            refs = c.get('evidence_refs', [])
            if not refs or len(refs) == 0:
                missing_refs.append(cid)
            else:
                for r in refs:
                    if not isinstance(r, str):
                        unresolvable_refs.append((cid, str(r)))
                        continue
                    full_p = os.path.normpath(os.path.join(self.repo_root, r.replace('/', os.sep)))
                    if not os.path.exists(full_p):
                        unresolvable_refs.append((cid, r))

        self.assert_invariant("INV-REC-06: Zero checks with empty evidence_refs", len(missing_refs) == 0, f"missing_count={len(missing_refs)}")
        self.assert_invariant("INV-REC-07: Every evidence_ref resolves to existing file on disk", len(unresolvable_refs) == 0, f"unresolvable_count={len(unresolvable_refs)}")

        return checks, doc

    def audit_stage_accounting_reconciliation(self, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.log("\n[INDEPENDENT AUDIT 3] Mathematical Stage Accounting Reconciliation")
        acc_path = os.path.join(RECON_DIR, 'accounting_summary.json')
        self.assert_invariant("INV-ACC-01: accounting_summary.json exists", os.path.exists(acc_path), acc_path)

        with open(acc_path, 'r', encoding='utf-8') as f:
            acc_doc = json.load(f)

        # Independently calculate totals from raw checks
        raw_total = len(checks)
        raw_counts = {st: 0 for st in ALLOWED_RESULT_STATUSES}
        stage_calc = {st_id: {s: 0 for s in ALLOWED_RESULT_STATUSES} for st_id in STAGE_REGISTRY}
        for st_id in stage_calc:
            stage_calc[st_id]['total'] = 0

        for c in checks:
            st = c.get('status')
            stage_id = c.get('stage_id')
            if st in raw_counts:
                raw_counts[st] += 1
            if stage_id in stage_calc and st in stage_calc[stage_id]:
                stage_calc[stage_id][st] += 1
                stage_calc[stage_id]['total'] += 1

        overall_totals = acc_doc.get('overall_totals', {})
        self.assert_invariant(
            "INV-ACC-02: Overall total_checks equals raw record count",
            overall_totals.get('total_checks') == raw_total,
            f"declared={overall_totals.get('total_checks')}, calculated={raw_total}"
        )
        self.assert_invariant(
            "INV-ACC-03: Overall PASS count equals raw PASS count",
            overall_totals.get('pass') == raw_counts['PASS'],
            f"declared={overall_totals.get('pass')}, calculated={raw_counts['PASS']}"
        )
        self.assert_invariant(
            "INV-ACC-04: Overall FAIL count equals raw FAIL count",
            overall_totals.get('fail') == raw_counts['FAIL'],
            f"declared={overall_totals.get('fail')}, calculated={raw_counts['FAIL']}"
        )

        # Stage totals reconciliation
        stage_totals = acc_doc.get('stage_totals', {})
        stage_mismatches = []
        for st_id in STAGE_REGISTRY:
            decl = stage_totals.get(st_id, {})
            calc = stage_calc[st_id]
            if decl.get('total') != calc['total'] or decl.get('pass') != calc['PASS'] or decl.get('fail') != calc['FAIL']:
                stage_mismatches.append((st_id, decl, calc))

        self.assert_invariant(
            "INV-ACC-05: Every registered stage total matches independently calculated totals",
            len(stage_mismatches) == 0,
            f"mismatches={stage_mismatches}"
        )

        sum_stage_totals = sum(stage_calc[st_id]['total'] for st_id in STAGE_REGISTRY)
        self.assert_invariant(
            "INV-ACC-06: Sum of all stage totals equals overall check count",
            sum_stage_totals == raw_total,
            f"sum_stage={sum_stage_totals}, total={raw_total}"
        )

        return {
            'raw_total': raw_total,
            'raw_counts': raw_counts,
            'stage_calc': stage_calc,
            'is_perfect_match': (len(stage_mismatches) == 0 and sum_stage_totals == raw_total)
        }

    def audit_acceptance_matrix(self, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.log("\n[INDEPENDENT AUDIT 4] Acceptance Matrix Programmatic Derivation")
        matrix_path = os.path.join(RECON_DIR, 'acceptance_matrix.json')
        self.assert_invariant("INV-AC-01: acceptance_matrix.json exists", os.path.exists(matrix_path), matrix_path)

        with open(matrix_path, 'r', encoding='utf-8') as f:
            matrix_doc = json.load(f)

        criteria = matrix_doc.get('criteria', [])
        self.assert_invariant("INV-AC-02: Exactly 22 criteria defined (AC-01 to AC-22)", len(criteria) == 22, f"count={len(criteria)}")

        check_status_map = {c.get('check_id'): c.get('status') for c in checks}
        criteria_findings = []

        for crit in criteria:
            cid = crit.get('criterion_id')
            recorded_status = crit.get('status')
            related = crit.get('related_check_ids', [])

            if not related:
                criteria_findings.append((cid, "EMPTY_RELATED_CHECK_IDS"))
                continue

            unknown_related = [r for r in related if r not in check_status_map]
            if unknown_related:
                criteria_findings.append((cid, f"UNKNOWN_CHECK_IDS: {unknown_related}"))
                continue

            # Derive expected status
            statuses = [check_status_map[r] for r in related]
            if any(s == 'FAIL' for s in statuses):
                expected_st = 'FAIL'
            elif any(s == 'BLOCKED' for s in statuses):
                expected_st = 'BLOCKED'
            elif any(s == 'NOT_CHECKED' for s in statuses):
                expected_st = 'NOT_CHECKED'
            elif all(s == 'PASS' for s in statuses):
                expected_st = 'PASS'
            else:
                expected_st = 'WARNING'

            if recorded_status != expected_st:
                criteria_findings.append((cid, f"STATUS_MISMATCH: recorded={recorded_status}, derived={expected_st}"))

        self.assert_invariant(
            "INV-AC-03: Every criterion status strictly derives from real executed check records",
            len(criteria_findings) == 0,
            f"findings={criteria_findings}"
        )

        all_ac_pass = all(crit.get('status') == 'PASS' for crit in criteria)
        self.assert_invariant("INV-AC-04: All 22 criteria evaluated as PASS", all_ac_pass, f"evaluation_status={matrix_doc.get('evaluation_status')}")

        return {
            'total_criteria': len(criteria),
            'all_pass': all_ac_pass,
            'findings': criteria_findings
        }

    def audit_execution_artifacts(self) -> Dict[str, Any]:
        self.log("\n[INDEPENDENT AUDIT 5] Execution Manifest & Raw Log Artifact Integrity")
        manifest_path = os.path.join(RECON_DIR, 'execution_manifest.json')
        self.assert_invariant("INV-ART-01: execution_manifest.json exists", os.path.exists(manifest_path), manifest_path)

        with open(manifest_path, 'r', encoding='utf-8') as f:
            man = json.load(f)

        run_id = man.get('run_id')
        self.assert_invariant("INV-ART-02: Run ID is populated", bool(run_id), f"run_id={run_id}")

        # Check stdout
        stdout_entry = man.get('stdout', {})
        ok_out, msg_out = validate_execution_artifact(stdout_entry, self.repo_root, expected_run_id=run_id)
        self.assert_invariant("INV-ART-03: stdout log artifact hash, size, and containment verified", ok_out, msg_out)

        # Check stderr
        stderr_entry = man.get('stderr', {})
        ok_err, msg_err = validate_execution_artifact(stderr_entry, self.repo_root, expected_run_id=run_id)
        self.assert_invariant("INV-ART-04: stderr log artifact hash, size, and containment verified", ok_err, msg_err)

        return {
            'run_id': run_id,
            'stdout_valid': ok_out,
            'stderr_valid': ok_err
        }

    def audit_regression_tests(self) -> Dict[str, Any]:
        self.log("\n[INDEPENDENT AUDIT 6] Regression Test Suite Verification")
        # Run unittest suite directly to confirm real execution output and exit code
        cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
        start_time = datetime.now(timezone.utc)
        res = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True)
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        is_success = (res.returncode == 0)
        self.assert_invariant(
            "INV-TEST-01: Regression test suite executes with exit code 0",
            is_success,
            f"exit_code={res.returncode}"
        )

        test_count = 0
        for line in res.stderr.splitlines():
            if line.startswith("Ran ") and "tests in" in line:
                try:
                    test_count = int(line.split()[1])
                except Exception:
                    pass

        self.assert_invariant(
            "INV-TEST-02: Regression test suite executed at least 56 tests",
            test_count >= 56,
            f"executed={test_count}"
        )

        return {
            'command': ' '.join(cmd),
            'exit_code': res.returncode,
            'tests_run': test_count,
            'duration_seconds': duration,
            'stderr_summary': res.stderr.splitlines()[-3:] if res.stderr else []
        }

    def evaluate_final_release_gate(self, audit_summary: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        self.log("\n[INDEPENDENT AUDIT 7] Fail-Closed Release Gate Evaluation")
        
        has_blockers = (self.invariants_failed > 0)
        final_status = "ACCEPTED" if not has_blockers else "REJECTED"

        release_gate_doc = {
            'schema_version': '1.1.2.2.4',
            'milestone': 'Phase 1.1.2.2.4',
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'final_status': final_status,
            'decision_message': (
                "PHASE 1.1.2.2.4 — ACCEPTED: All independent evidence invariants, PR #5 attestation, "
                "validation check records, stage accounting, acceptance matrix, artifact integrity, "
                "and regression tests verified."
                if not has_blockers else
                f"PHASE 1.1.2.2.4 — REJECTED: {self.invariants_failed} independent invariants failed."
            ),
            'invariants_evaluated': self.invariants_passed + self.invariants_failed,
            'invariants_passed': self.invariants_passed,
            'invariants_failed': self.invariants_failed,
            'blocking_findings': self.findings,
            'git_attestation': audit_summary.get('git', {}),
            'execution_evidence': audit_summary.get('artifacts', {}),
            'accounting_reconciliation': {
                'total_checks': audit_summary.get('accounting', {}).get('raw_total', 0),
                'pass_count': audit_summary.get('accounting', {}).get('raw_counts', {}).get('PASS', 0),
                'is_perfect_match': audit_summary.get('accounting', {}).get('is_perfect_match', False)
            },
            'acceptance_matrix': {
                'total_criteria': audit_summary.get('matrix', {}).get('total_criteria', 0),
                'all_pass': audit_summary.get('matrix', {}).get('all_pass', False)
            },
            'regression_suite': audit_summary.get('regression', {})
        }

        rg_path = os.path.join(RECON_DIR, 'release_gate_result.json')
        with open(rg_path, 'w', encoding='utf-8') as f:
            json.dump(release_gate_doc, f, indent=2)

        self.log(f"\nRelease Gate Decision: {final_status}")
        self.log(f"Invariants Passed: {self.invariants_passed}/{self.invariants_passed + self.invariants_failed}")
        self.log(f"Findings: {len(self.findings)}")

        return final_status, release_gate_doc

    def run_audit(self) -> int:
        self.log("=" * 78)
        self.log("    LABEL-FORGE INDEPENDENT EVIDENCE INTEGRITY AUDITOR (PHASE 1.1.2.2.4)")
        self.log("=" * 78)

        git_summary = self.audit_git_objects_and_provenance()
        checks, results_doc = self.audit_validation_records()
        acc_summary = self.audit_stage_accounting_reconciliation(checks)
        matrix_summary = self.audit_acceptance_matrix(checks)
        art_summary = self.audit_execution_artifacts()
        reg_summary = self.audit_regression_tests()

        audit_summary = {
            'git': git_summary,
            'records': {'total': len(checks)},
            'accounting': acc_summary,
            'matrix': matrix_summary,
            'artifacts': art_summary,
            'regression': reg_summary
        }

        # Save independent audit report
        indep_doc = {
            'schema_version': '1.1.2.2.4',
            'milestone': 'Phase 1.1.2.2.4',
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'audit_result': 'PASS' if self.invariants_failed == 0 else 'FAIL',
            'invariants_evaluated': self.invariants_passed + self.invariants_failed,
            'invariants_passed': self.invariants_passed,
            'invariants_failed': self.invariants_failed,
            'findings': self.findings,
            'summary': audit_summary
        }

        indep_path = os.path.join(RECON_DIR, 'independent_audit.json')
        with open(indep_path, 'w', encoding='utf-8') as f:
            json.dump(indep_doc, f, indent=2)

        gate_status, gate_doc = self.evaluate_final_release_gate(audit_summary)

        return 0 if self.invariants_failed == 0 else 1


if __name__ == '__main__':
    auditor = IndependentAuditor()
    code = auditor.run_audit()
    sys.exit(code)
