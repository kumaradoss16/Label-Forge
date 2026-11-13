"""
Label-Forge Evidence Integrity Validation Framework
Module: validation.provenance

Handles deterministic provenance recording and schema management.
Ensures provenance accurately captures the validated commit SHA and runtime metadata.
"""

import os
import hashlib
import platform
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, Optional

def generate_provenance_record(
    repo_root: str,
    val_manifest_path: str,
    validator_path: str,
    exit_code: int,
    total_checks: int,
    pass_count: int,
    fail_count: int,
    warning_count: int,
    not_checked_count: int,
    stage_breakdown: Dict[str, str],
    logs: list,
    target_exe_path: Optional[str] = None,
    actual_target_sha256: Optional[str] = None,
    expected_target_sha256: Optional[str] = None,
    target_available: bool = False
) -> Dict[str, Any]:
    """Generates the authoritative validation provenance dictionary."""

    try:
        commit_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_root).decode('utf-8').strip()
    except Exception:
        commit_sha = "UNKNOWN_COMMIT"

    try:
        branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=repo_root).decode('utf-8').strip()
    except Exception:
        branch = "UNKNOWN_BRANCH"

    try:
        status_porcelain = subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo_root).decode('utf-8').strip()
        is_clean = (len(status_porcelain) == 0)
    except Exception:
        is_clean = False
        status_porcelain = "GIT_STATUS_FAILED"

    # Compute checksums of validator and manifest
    validator_sha256 = "MISSING"
    if os.path.exists(validator_path):
        with open(validator_path, 'rb') as f:
            validator_sha256 = hashlib.sha256(f.read()).hexdigest()

    manifest_sha256 = "MISSING"
    if os.path.exists(val_manifest_path):
        with open(val_manifest_path, 'rb') as f:
            manifest_sha256 = hashlib.sha256(f.read()).hexdigest()

    manifest_verified = (stage_breakdown.get('manifest_integrity') == 'PASS')

    result_status = 'PASS' if exit_code == 0 else ('NOT_CHECKED' if exit_code == 2 else 'FAIL')
    gate_status = 'PHASE 1.1.2.1 — APPROVED' if exit_code == 0 else 'PHASE 1.1.2.1 — BLOCKED'

    provenance = {
        'schema_version': '1.1.2.1',
        'status': 'RECONCILED_AUTHORITATIVE',
        'provenance_metadata': {
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'validated_commit_sha': commit_sha,
            'branch': branch,
            'is_working_tree_clean': is_clean,
            'working_tree_status_porcelain': status_porcelain,
            'validator_script': {
                'path': os.path.relpath(validator_path, repo_root).replace('\\', '/'),
                'sha256': validator_sha256
            },
            'validation_manifest': {
                'path': os.path.relpath(val_manifest_path, repo_root).replace('\\', '/'),
                'sha256': manifest_sha256
            },
            'target_executable': {
                'path': target_exe_path,
                'sha256': actual_target_sha256 if target_available else "NOT_CHECKED",
                'matches_canonical': (actual_target_sha256 == expected_target_sha256) if target_available else False
            },
            'execution_environment': {
                'os': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version()
            }
        },
        'validation_results': {
            'exit_code': exit_code,
            'result_status': result_status,
            'release_gate_status': gate_status,
            'summary_accounting': {
                'total_checks': total_checks,
                'pass': pass_count,
                'fail': fail_count,
                'warning': warning_count,
                'not_checked': not_checked_count
            },
            'stage_breakdown': stage_breakdown,
            'manifest_integrity_verified': manifest_verified,
            'category_partition_verified': (stage_breakdown.get('direct_import_partition') == 'PASS'),
            'claim_traceability_verified': (stage_breakdown.get('evidence_references') == 'PASS'),
            'recursive_image_audit_verified': (stage_breakdown.get('recursive_image_audit') == 'PASS')
        },
        'execution_log': logs
    }

    return provenance
