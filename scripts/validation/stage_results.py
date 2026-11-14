"""
Label-Forge Evidence Integrity Validation Framework
Module: validation.stage_results

Provides structured assertion records and stage-level status aggregation.
Enforces that stage status is mathematically derived from assertion results,
with zero unconditional overwrites.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

# Authoritative Statuses
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_WARNING = "WARNING"
STATUS_NOT_CHECKED = "NOT_CHECKED"
STATUS_BLOCKED = "BLOCKED"
STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"

ALLOWED_RESULT_STATUSES = {
    STATUS_PASS,
    STATUS_FAIL,
    STATUS_WARNING,
    STATUS_NOT_CHECKED,
    STATUS_BLOCKED,
    STATUS_NOT_APPLICABLE
}

# Authoritative 10 Validation Stages Registry
STAGE_REGISTRY = {
    "target_prerequisites": {
        "id": "target_prerequisites",
        "name": "Target & Environmental Prerequisites",
        "required": True,
        "legacy_key": "target_prerequisites"
    },
    "target_binary_integrity": {
        "id": "target_binary_integrity",
        "name": "Target Binary Cryptographic & Header Verification",
        "required": True,
        "legacy_key": "target_binary_integrity"
    },
    "manifest_integrity": {
        "id": "manifest_integrity",
        "name": "Evidence Manifest Checksum Integrity Audit",
        "required": True,
        "legacy_key": "manifest_integrity"
    },
    "component_inventory": {
        "id": "component_inventory",
        "name": "Component Inventory Mathematical Reconciliation",
        "required": True,
        "legacy_key": "component_inventory"
    },
    "direct_import_partition": {
        "id": "direct_import_partition",
        "name": "Direct-Import Category Partition & Dependency Audit",
        "required": True,
        "legacy_key": "direct_import_partition"
    },
    "status_accounting": {
        "id": "status_accounting",
        "name": "Claim Status Accounting Integrity",
        "required": True,
        "legacy_key": "status_accounting"
    },
    "evidence_references": {
        "id": "evidence_references",
        "name": "Structured Evidence References Verification Audit",
        "required": True,
        "legacy_key": "evidence_references"
    },
    "claim_specific_assertions": {
        "id": "claim_specific_assertions",
        "name": "Claim-Specific Assertion Registry",
        "required": True,
        "legacy_key": "claim_specific_assertions"
    },
    "recursive_image_audit": {
        "id": "recursive_image_audit",
        "name": "Recursive Prohibited-Image Compliance Audit",
        "required": True,
        "legacy_key": "recursive_image_audit"
    },
    "report_consistency": {
        "id": "report_consistency",
        "name": "Report Cross-References & Markdown Integrity Audit",
        "required": True,
        "legacy_key": "report_consistency"
    }
}


@dataclass
class AssertionRecord:
    assertion_id: str
    status: str
    detail: str = ""
    stage_id: str = ""
    evidence_ref: str = ""
    expected: Any = None
    actual: Any = None

    def __post_init__(self):
        if self.status not in ALLOWED_RESULT_STATUSES:
            raise ValueError(f"Invalid assertion status: '{self.status}'. Must be one of {ALLOWED_RESULT_STATUSES}")

    @property
    def name(self) -> str:
        return self.assertion_id

@dataclass
class StageResult:
    stage_id: str
    description: str = ""
    status: str = STATUS_NOT_CHECKED
    assertions: List[AssertionRecord] = field(default_factory=list)

    def add(self, record: AssertionRecord):
        self.assertions.append(record)
        self.recompute_status()
        return record

    def record_assertion(self, assertion_id: str, status: str, detail: str = "", evidence_ref: str = "", expected: Any = None, actual: Any = None) -> AssertionRecord:
        record = AssertionRecord(
            stage_id=self.stage_id,
            assertion_id=assertion_id,
            status=status,
            detail=detail,
            evidence_ref=evidence_ref,
            expected=expected,
            actual=actual
        )
        self.assertions.append(record)
        self.recompute_status()
        return record

    def recompute_status(self) -> str:
        """
        Derives stage status strictly from its underlying assertion records:
        - FAIL: If any assertion has status FAIL.
        - NOT_CHECKED: If no assertions exist, or if all assertions are NOT_CHECKED.
        - WARNING: If no FAIL, but at least one WARNING exists.
        - PASS: Only if at least one assertion exists, every assertion is PASS (or allowed WARNING), and zero FAIL/NOT_CHECKED.
        """
        if not self.assertions:
            self.status = STATUS_NOT_CHECKED
            return self.status

        has_fail = any(a.status == STATUS_FAIL for a in self.assertions)
        has_blocked = any(a.status == STATUS_BLOCKED for a in self.assertions)
        has_not_checked = any(a.status == STATUS_NOT_CHECKED for a in self.assertions)
        has_warning = any(a.status == STATUS_WARNING for a in self.assertions)
        all_pass = all(a.status in (STATUS_PASS, STATUS_NOT_APPLICABLE) for a in self.assertions)

        if has_fail:
            self.status = STATUS_FAIL
        elif has_blocked:
            self.status = STATUS_BLOCKED
        elif has_not_checked:
            # If any mandatory subcheck is NOT_CHECKED, the stage cannot be PASS
            self.status = STATUS_NOT_CHECKED
        elif has_warning:
            self.status = STATUS_WARNING
        elif all_pass and any(a.status == STATUS_PASS for a in self.assertions):
            self.status = STATUS_PASS
        else:
            self.status = STATUS_FAIL

        return self.status


def aggregate_stage_status(assertions: List[AssertionRecord]) -> str:
    """Helper function to aggregate a list of assertions into a stage status."""
    dummy = StageResult(stage_id="aggregate", description="aggregated", assertions=list(assertions))
    return dummy.recompute_status()

def evaluate_release_gate(
    stage_results: Dict[str, str],
    counts: Dict[str, int],
    mandatory_stages: Optional[List[str]] = None
) -> Tuple[int, str, str]:
    """
    Evaluates the final release gate across stage results and check counts.
    Returns: (exit_code, release_gate_status, detail_message)
    Exit Codes:
      0: Fully passed release gate (All mandatory checks pass, 0 fail, 0 not_checked, 0 warnings)
      1: Validation failure or unapproved warnings
      2: Prerequisite unavailable / NOT_CHECKED / BLOCKED
      3: Internal validator error
    """
    if mandatory_stages is None:
        mandatory_stages = list(STAGE_REGISTRY.keys())

    if counts.get(STATUS_FAIL, 0) > 0 or any(stage_results.get(st) == STATUS_FAIL for st in mandatory_stages):
        return (1, "PHASE 1.1.2.2.3 — FAILED", "One or more mandatory validation checks failed")

    missing_stages = [st for st in mandatory_stages if st not in stage_results]
    if missing_stages:
        return (1, "PHASE 1.1.2.2.3 — BLOCKED", f"Missing mandatory validation stages: {missing_stages}")


    if counts.get(STATUS_BLOCKED, 0) > 0 or any(stage_results.get(st) == STATUS_BLOCKED for st in mandatory_stages):
        return (2, "PHASE 1.1.2.2.3 — BLOCKED", "One or more mandatory stages were BLOCKED due to unavailable prerequisites")

    if counts.get(STATUS_NOT_CHECKED, 0) > 0 or any(stage_results.get(st) == STATUS_NOT_CHECKED for st in mandatory_stages):
        return (2, "PHASE 1.1.2.2.3 — BLOCKED", "One or more mandatory stages were NOT_CHECKED due to missing prerequisites")

    if counts.get(STATUS_WARNING, 0) > 0 or any(stage_results.get(st) == STATUS_WARNING for st in mandatory_stages):
        return (1, "PHASE 1.1.2.2.3 — BLOCKED", "Unresolved validation warnings present")

    all_stages_pass = all(stage_results.get(st) == STATUS_PASS for st in mandatory_stages)
    if all_stages_pass and counts.get(STATUS_PASS, 0) > 0:
        return (0, "PHASE 1.1.2.2.3 — APPROVED", "All mandatory integrity and evidence checks verified")

    return (1, "PHASE 1.1.2.2.3 — FAILED", "Incomplete validation results")

