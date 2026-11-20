"""
Label-Forge Acceptance Execution Proof Framework
Module: scripts.validation.acceptance_execution

Defines the structured schema for acceptance execution records (AC-01 through AC-22)
and provides independent, fail-closed validation.

F-04 Remediation:
- Eliminates static source-code discovery (def test_*) as evidence.
- Requires genuine positive and negative test executions.
- Enforces exact criterion set: AC-01 through AC-22.
- Binds every record to current run_id and execution_revision.
- Verifies test_result_reference containment, existence, and SHA-256 match.
- Verifies that negative tests demonstrate genuine rejection behavior.
"""

import os
import re
import json
import hashlib
from typing import Dict, List, Tuple, Any, Optional

ALLOWED_TEST_TYPES = {"positive", "negative"}
ALLOWED_EXECUTION_STATUSES = {"PASS", "FAIL", "ERROR", "SKIPPED", "NOT_EXECUTED"}

CANONICAL_ACCEPTANCE_CRITERIA = [f"AC-{i:02d}" for i in range(1, 23)]

ACCEPTANCE_RECORD_FIELDS = [
    "acceptance_criterion_id",
    "test_case_id",
    "test_type",
    "expected_behavior",
    "observed_behavior",
    "execution_status",
    "execution_timestamp_utc",
    "run_id",
    "test_suite_id",
    "test_command",
    "test_exit_code",
    "test_result_reference",
    "execution_revision",
    "evidence_sha256"
]


def validate_acceptance_execution_record(
    record: Dict[str, Any],
    expected_run_id: Optional[str] = None,
    expected_revision: Optional[str] = None,
    repo_root: Optional[str] = None,
    strict_schema: bool = True
) -> Tuple[bool, List[str]]:
    """
    Validates a single acceptance execution record against strict schema and integrity rules:
    - Exactly contains all 14 canonical fields (rejects extra/missing fields if strict_schema=True).
    - Field types and formats strictly checked.
    - execution_status member of ALLOWED_EXECUTION_STATUSES.
    - test_type member of ALLOWED_TEST_TYPES.
    - run_id matches expected_run_id if provided.
    - execution_revision matches expected_revision if provided.
    - test_result_reference safely contained within repo_root and matches evidence_sha256.
    - Negative test cases must document genuine rejection behavior in observed_behavior.
    """
    failures: List[str] = []

    if not isinstance(record, dict):
        return False, ["Record must be a dictionary"]

    # Check for missing fields
    missing_fields = [f for f in ACCEPTANCE_RECORD_FIELDS if f not in record]
    if missing_fields:
        failures.append(f"Missing required fields: {missing_fields}")

    # Check for unknown fields in strict mode
    if strict_schema:
        unknown_fields = [f for f in record if f not in ACCEPTANCE_RECORD_FIELDS]
        if unknown_fields:
            failures.append(f"Unknown fields present: {unknown_fields}")

    # 1. acceptance_criterion_id
    acid = record.get("acceptance_criterion_id")
    if not acid or not isinstance(acid, str):
        failures.append("acceptance_criterion_id must be a non-empty string")
    elif acid not in CANONICAL_ACCEPTANCE_CRITERIA:
        failures.append(f"acceptance_criterion_id '{acid}' not in canonical AC-01..AC-22 set")

    # 2. test_case_id
    tcid = record.get("test_case_id")
    if not tcid or not isinstance(tcid, str) or not tcid.strip():
        failures.append("test_case_id must be a non-empty string")

    # 3. test_type
    tt = record.get("test_type")
    if tt not in ALLOWED_TEST_TYPES:
        failures.append(f"test_type '{tt}' must be one of {sorted(ALLOWED_TEST_TYPES)}")

    # 4. expected_behavior
    eb = record.get("expected_behavior")
    if not eb or not isinstance(eb, str) or not eb.strip():
        failures.append("expected_behavior must be a non-empty string")

    # 5. observed_behavior
    ob = record.get("observed_behavior")
    if not ob or not isinstance(ob, str) or not ob.strip():
        failures.append("observed_behavior must be a non-empty string")

    # 6. execution_status
    es = record.get("execution_status")
    if es not in ALLOWED_EXECUTION_STATUSES:
        failures.append(f"execution_status '{es}' must be one of {sorted(ALLOWED_EXECUTION_STATUSES)}")

    # 7. execution_timestamp_utc
    ts = record.get("execution_timestamp_utc")
    if not ts or not isinstance(ts, str):
        failures.append("execution_timestamp_utc must be a non-empty ISO 8601 string")
    else:
        # ISO 8601 validation
        iso_regex = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$'
        if not re.match(iso_regex, ts):
            failures.append(f"execution_timestamp_utc '{ts}' does not match ISO 8601 UTC format")

    # 8. run_id
    rid = record.get("run_id")
    if not rid or not isinstance(rid, str) or not rid.strip():
        failures.append("run_id must be a non-empty string")
    elif expected_run_id and rid != expected_run_id:
        failures.append(f"run_id mismatch: expected '{expected_run_id}', observed '{rid}'")

    # 9. test_suite_id
    sid = record.get("test_suite_id")
    if not sid or not isinstance(sid, str) or not sid.strip():
        failures.append("test_suite_id must be a non-empty string")

    # 10. test_command
    tc = record.get("test_command")
    if not tc or not isinstance(tc, str) or not tc.strip():
        failures.append("test_command must be a non-empty string")

    # 11. test_exit_code
    tec = record.get("test_exit_code")
    if isinstance(tec, bool) or not isinstance(tec, int):
        failures.append("test_exit_code must be an integer (not boolean)")

    # 12. execution_revision
    rev = record.get("execution_revision")
    if not rev or not isinstance(rev, str) or len(rev) != 40:
        failures.append("execution_revision must be a 40-character commit SHA string")
    elif not all(c in "0123456789abcdefABCDEF" for c in rev):
        failures.append(f"execution_revision '{rev}' is not a valid hex SHA")
    elif expected_revision and rev.lower() != expected_revision.lower():
        failures.append(f"execution_revision mismatch: expected '{expected_revision}', observed '{rev}'")

    # 13. test_result_reference and 14. evidence_sha256
    trr = record.get("test_result_reference")
    esha = record.get("evidence_sha256")

    if not esha or not isinstance(esha, str) or len(esha) != 64:
        failures.append("evidence_sha256 must be a 64-character hex string")
    elif not all(c in "0123456789abcdef" for c in esha.lower()):
        failures.append("evidence_sha256 contains invalid hex characters")

    if not trr or not isinstance(trr, str):
        failures.append("test_result_reference must be a non-empty string")
    elif repo_root:
        # Check containment and existence
        if "\\" in trr:
            failures.append(f"test_result_reference contains backslashes: '{trr}'")
        elif ".." in trr.split("/"):
            failures.append(f"test_result_reference attempts traversal: '{trr}'")
        else:
            real_root = os.path.realpath(repo_root)
            full_path = os.path.normpath(os.path.join(real_root, trr.replace("/", os.sep)))
            real_file = os.path.realpath(full_path)
            try:
                common = os.path.commonpath([real_root, real_file])
                if os.path.normcase(common) != os.path.normcase(real_root):
                    failures.append(f"test_result_reference escapes repository root: '{trr}'")
                elif not os.path.exists(full_path):
                    failures.append(f"test_result_reference path missing on disk: '{trr}'")
                elif os.path.islink(full_path):
                    failures.append(f"test_result_reference is a symlink: '{trr}'")
                elif not os.path.isfile(full_path):
                    failures.append(f"test_result_reference is not a regular file: '{trr}'")
                else:
                    # Verify evidence_sha256 matches actual file
                    h = hashlib.sha256()
                    with open(full_path, "rb") as f:
                        for chunk in iter(lambda: f.read(65536), b""):
                            h.update(chunk)
                    actual_sha = h.hexdigest().lower()
                    if esha and actual_sha != esha.lower():
                        failures.append(f"evidence_sha256 mismatch for '{trr}': expected '{esha}', actual '{actual_sha}'")
            except ValueError:
                failures.append(f"test_result_reference drive mismatch: '{trr}'")

    # Negative test verification: observed_behavior must demonstrate genuine rejection
    if tt == "negative":
        ob_lower = str(ob).lower() if ob else ""
        success_tokens = ["operation succeeded", "without error", "without errors", "succeeded normally", "success:"]
        if any(st in ob_lower for st in success_tokens):
            failures.append(f"Negative test '{tcid}' indicates success rather than rejection: '{ob}'")
        else:
            rejection_tokens = [
                "reject", "fail", "error", "mismatch", "invalid", "prohibit", 
                "dirty", "traversal", "symlink", "exit status 1", "exit status 2",
                "assertionerror", "exception", "non-zero", "returned non-zero",
                "out-of-bounds", "duplicate", "missing", "unsupported", "overstated"
            ]
            if not any(token in ob_lower for token in rejection_tokens):
                failures.append(f"Negative test '{tcid}' observed_behavior does not assert/demonstrate rejection: '{ob}'")

    return len(failures) == 0, failures


def evaluate_acceptance_execution_records(
    records: List[Dict[str, Any]],
    expected_run_id: str,
    expected_revision: str,
    repo_root: str,
    required_criteria: Optional[List[str]] = None
) -> Tuple[bool, Dict[str, Any], List[str]]:
    """
    Evaluates the complete set of acceptance execution records for AC-01 through AC-22 fail-closed:
    - Enforces exact set: AC-01 through AC-22 (no missing, no unknown, no duplicates).
    - Every criterion must have at least 1 valid positive test record with status PASS.
    - Every criterion must have at least 1 valid negative test record with status PASS.
    - Negative test must demonstrate actual rejection.
    - All records must match expected_run_id and expected_revision.
    - Returns: (is_passed, evaluation_doc, all_findings)
    """
    if required_criteria is None:
        required_criteria = list(CANONICAL_ACCEPTANCE_CRITERIA)

    findings: List[str] = []
    by_criterion: Dict[str, List[Dict[str, Any]]] = {c: [] for c in required_criteria}
    unknown_criteria: List[str] = []

    seen_records: Dict[Tuple[str, str, str], int] = {}
    record_validation_errors: List[str] = []

    for idx, rec in enumerate(records):
        cid = rec.get("acceptance_criterion_id")
        tcid = rec.get("test_case_id")
        ttype = rec.get("test_type")

        # Validate individual record
        ok_rec, rec_errs = validate_acceptance_execution_record(
            rec,
            expected_run_id=expected_run_id,
            expected_revision=expected_revision,
            repo_root=repo_root,
            strict_schema=True
        )
        if not ok_rec:
            record_validation_errors.extend([f"Record #{idx} ({cid}:{tcid}): {e}" for e in rec_errs])

        # Duplicate check
        key = (str(cid), str(tcid), str(ttype))
        if key in seen_records:
            findings.append(f"Duplicate execution record for criterion '{cid}', test_case '{tcid}', type '{ttype}'")
        seen_records[key] = idx

        if cid in by_criterion:
            by_criterion[cid].append(rec)
        else:
            unknown_criteria.append(str(cid))

    if unknown_criteria:
        findings.append(f"Unknown criterion IDs in execution records: {sorted(set(unknown_criteria))}")

    if record_validation_errors:
        findings.extend(record_validation_errors)

    criteria_evaluations: List[Dict[str, Any]] = []
    all_criteria_pass = True

    for cid in required_criteria:
        recs = by_criterion.get(cid, [])
        pos_recs = [r for r in recs if r.get("test_type") == "positive"]
        neg_recs = [r for r in recs if r.get("test_type") == "negative"]

        crit_findings: List[str] = []

        if not pos_recs:
            crit_findings.append(f"Missing required positive test execution for {cid}")
        else:
            # Check positive statuses
            for pr in pos_recs:
                st = pr.get("execution_status")
                if st != "PASS":
                    crit_findings.append(f"Positive test '{pr.get('test_case_id')}' status is {st} (expected PASS)")

        if not neg_recs:
            crit_findings.append(f"Missing required negative test execution for {cid}")
        else:
            # Check negative statuses
            for nr in neg_recs:
                st = nr.get("execution_status")
                if st != "PASS":
                    crit_findings.append(f"Negative test '{nr.get('test_case_id')}' status is {st} (expected PASS)")

        status = "PASS" if len(crit_findings) == 0 else "FAIL"
        if status != "PASS":
            all_criteria_pass = False
            findings.extend([f"{cid}: {f}" for f in crit_findings])

        criteria_evaluations.append({
            "criterion_id": cid,
            "status": status,
            "positive_test_count": len(pos_recs),
            "negative_test_count": len(neg_recs),
            "positive_tests": [r.get("test_case_id") for r in pos_recs],
            "negative_tests": [r.get("test_case_id") for r in neg_recs],
            "findings": crit_findings
        })

    is_passed = (all_criteria_pass and len(findings) == 0 and len(unknown_criteria) == 0)

    evaluation_doc = {
        "schema_version": "1.1.2.2.4.4",
        "milestone": "Phase 1.1.2.2.4.4 — Critical Acceptance Execution Proof & Git Provenance Reconciliation",
        "run_id": expected_run_id,
        "execution_revision": expected_revision,
        "evaluation_status": "APPROVED" if is_passed else "REJECTED",
        "total_criteria": len(required_criteria),
        "criteria_passed": sum(1 for c in criteria_evaluations if c["status"] == "PASS"),
        "criteria_failed": sum(1 for c in criteria_evaluations if c["status"] != "PASS"),
        "total_execution_records": len(records),
        "findings": findings,
        "criteria_evaluations": criteria_evaluations
    }

    return is_passed, evaluation_doc, findings
