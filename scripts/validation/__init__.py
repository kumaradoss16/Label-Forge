"""
Label-Forge Evidence Integrity Validation Framework
Package: validation
"""

from .stage_results import (
    AssertionRecord,
    StageResult,
    aggregate_stage_status,
    STATUS_PASS,
    STATUS_FAIL,
    STATUS_WARNING,
    STATUS_NOT_CHECKED,
    ALLOWED_RESULT_STATUSES
)
from .dependency_validation import validate_direct_import_partition
from .evidence_integrity import (
    resolve_json_pointer,
    validate_status_accounting,
    scan_prohibited_images,
    validate_structured_evidence_reference,
    ALLOWED_CLAIM_STATUSES,
    PROHIBITED_IMAGE_EXTENSIONS
)
from .claim_assertions import make_claim_assertion_registry
from .provenance import generate_provenance_record
