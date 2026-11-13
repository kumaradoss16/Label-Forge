"""
Label-Forge Evidence Integrity Validation Framework
Module: validation.stage_results

Provides structured assertion records and stage-level status aggregation.
Enforces that stage status is mathematically derived from assertion results,
with zero unconditional overwrites.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# Authoritative Statuses
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_WARNING = "WARNING"
STATUS_NOT_CHECKED = "NOT_CHECKED"

ALLOWED_RESULT_STATUSES = {
    STATUS_PASS,
    STATUS_FAIL,
    STATUS_WARNING,
    STATUS_NOT_CHECKED
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
        has_not_checked = any(a.status == STATUS_NOT_CHECKED for a in self.assertions)
        has_warning = any(a.status == STATUS_WARNING for a in self.assertions)
        all_pass = all(a.status == STATUS_PASS for a in self.assertions)

        if has_fail:
            self.status = STATUS_FAIL
        elif has_not_checked:
            # If any mandatory subcheck is NOT_CHECKED, the stage cannot be PASS
            self.status = STATUS_NOT_CHECKED
        elif has_warning:
            self.status = STATUS_WARNING
        elif all_pass:
            self.status = STATUS_PASS
        else:
            self.status = STATUS_FAIL

        return self.status

def aggregate_stage_status(assertions: List[AssertionRecord]) -> str:
    """Helper function to aggregate a list of assertions into a stage status."""
    dummy = StageResult(stage_id="aggregate", description="aggregated", assertions=list(assertions))
    return dummy.recompute_status()
