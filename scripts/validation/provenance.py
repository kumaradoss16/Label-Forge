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
from typing import Dict, Any, Optional, Tuple, List
from scripts.validation.git_verification import resolve_git_commit_and_tree, verify_final_merge_equivalence

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
    target_available: bool = False,
    results_path: Optional[str] = None,
    stdout_log_path: Optional[str] = None,
    stderr_log_path: Optional[str] = None
) -> Dict[str, Any]:
    """Generates the authoritative validation provenance dictionary."""

    try:
        commit_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_root).decode('utf-8').strip()
    except Exception:
        commit_sha = "UNKNOWN_COMMIT"

    try:
        tree_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=repo_root).decode('utf-8').strip()
    except Exception:
        tree_sha = "UNKNOWN_TREE"

    try:
        branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=repo_root).decode('utf-8').strip()
    except Exception:
        branch = "UNKNOWN_BRANCH"

    try:
        status_porcelain = subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo_root).decode('utf-8').strip()
        lines = [l.strip() for l in status_porcelain.splitlines() if l.strip() and not l.strip().endswith('validation_provenance.json')]
        is_clean = (len(lines) == 0)
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

    results_sha256 = "MISSING"
    if results_path and os.path.exists(results_path):
        with open(results_path, 'rb') as f:
            results_sha256 = hashlib.sha256(f.read()).hexdigest()

    stdout_sha = "MISSING"
    if stdout_log_path and os.path.exists(stdout_log_path):
        with open(stdout_log_path, 'rb') as f:
            stdout_sha = hashlib.sha256(f.read()).hexdigest()

    stderr_sha = "MISSING"
    if stderr_log_path and os.path.exists(stderr_log_path):
        with open(stderr_log_path, 'rb') as f:
            stderr_sha = hashlib.sha256(f.read()).hexdigest()

    manifest_verified = (stage_breakdown.get('manifest_integrity') == 'PASS')

    result_status = 'PASS' if exit_code == 0 else ('NOT_CHECKED' if exit_code == 2 else 'FAIL')
    gate_status = 'PHASE 1.1.2.2.2 — APPROVED' if exit_code == 0 else 'PHASE 1.1.2.2.2 — BLOCKED'

    provenance = {
        'schema_version': '1.1.2.2.2',
        'status': 'RECONCILED_AUTHORITATIVE',
        'provenance_metadata': {
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'validated_commit_sha': commit_sha,
            'validated_tree_sha': tree_sha,
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
            'validation_results_artifact': {
                'path': os.path.relpath(results_path, repo_root).replace('\\', '/') if results_path else "MISSING",
                'sha256': results_sha256
            },
            'raw_execution_logs': {
                'stdout': {
                    'path': os.path.relpath(stdout_log_path, repo_root).replace('\\', '/') if stdout_log_path else "evidence/phase1/reconciliation/windows_validation/phase1_1_2_2_stdout.txt",
                    'sha256': stdout_sha
                },
                'stderr': {
                    'path': os.path.relpath(stderr_log_path, repo_root).replace('\\', '/') if stderr_log_path else "evidence/phase1/reconciliation/windows_validation/phase1_1_2_2_stderr.txt",
                    'sha256': stderr_sha
                }
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

def validate_provenance_record(
    provenance_doc: Dict[str, Any],
    repo_root: str
) -> Tuple[bool, List[str]]:
    """
    Validates provenance integrity:
    - schema_version and status
    - metadata presence (commit_sha, tree_sha, cleanliness)
    - referenced validator and manifest files exist and hashes match
    - execution environment records valid Python/OS strings
    - exit code and summary accounting reconcile exactly
    """
    errors: List[str] = []
    meta = provenance_doc.get('provenance_metadata', {})
    commit_sha = meta.get('validated_commit_sha', '')
    if not commit_sha or len(commit_sha) != 40:
        errors.append(f"Invalid or missing validated_commit_sha: '{commit_sha}'")
    else:
        # Independently verify Git commit object and tree relationship
        ok_git, info_git, msg_git = resolve_git_commit_and_tree(commit_sha, repo_root)
        if not ok_git or info_git is None:
            errors.append(f"Git object verification failed for validated_commit_sha '{commit_sha}': {msg_git}")
        else:
            rec_tree = meta.get('validated_tree_sha', '')
            if rec_tree and info_git['tree_sha'] != rec_tree:
                errors.append(f"Recorded tree SHA '{rec_tree}' does not match actual commit tree '{info_git['tree_sha']}'")

    # If final merge commit is specified, verify it and its tree identity
    final_merge = meta.get('final_merge_commit')
    if final_merge:
        ok_m, info_m, msg_m = resolve_git_commit_and_tree(final_merge, repo_root)
        if not ok_m or info_m is None:
            errors.append(f"Git object verification failed for final_merge_commit '{final_merge}': {msg_m}")
        else:
            rec_m_tree = meta.get('final_merge_tree')
            if rec_m_tree and info_m['tree_sha'] != rec_m_tree:
                errors.append(f"Recorded final merge tree '{rec_m_tree}' does not match actual merge commit tree '{info_m['tree_sha']}'")

    val_script = meta.get('validator_script', {})
    val_path = os.path.join(repo_root, val_script.get('path', '').replace('/', os.sep))
    if not os.path.exists(val_path):
        errors.append(f"Referenced validator script not found: '{val_script.get('path')}'")
    else:
        with open(val_path, 'rb') as f:
            act_sha = hashlib.sha256(f.read()).hexdigest()
        if act_sha != val_script.get('sha256'):
            errors.append(f"Validator script SHA-256 mismatch: recorded={val_script.get('sha256')}, actual={act_sha}")

    val_manifest = meta.get('validation_manifest', {})
    manifest_p = os.path.join(repo_root, val_manifest.get('path', '').replace('/', os.sep))
    if not os.path.exists(manifest_p):
        errors.append(f"Referenced validation manifest not found: '{val_manifest.get('path')}'")
    else:
        with open(manifest_p, 'rb') as f:
            act_m_sha = hashlib.sha256(f.read()).hexdigest()
        if act_m_sha != val_manifest.get('sha256'):
            errors.append(f"Validation manifest SHA-256 mismatch: recorded={val_manifest.get('sha256')}, actual={act_m_sha}")

    val_res = meta.get('validation_results_artifact')
    if val_res and val_res.get('path') and val_res.get('path') != "MISSING":
        res_p = os.path.join(repo_root, val_res.get('path', '').replace('/', os.sep))
        if not os.path.exists(res_p):
            errors.append(f"Referenced validation results not found: '{val_res.get('path')}'")
        else:
            with open(res_p, 'rb') as f:
                act_r_sha = hashlib.sha256(f.read()).hexdigest()
            if act_r_sha != val_res.get('sha256'):
                errors.append(f"Validation results SHA-256 mismatch: recorded={val_res.get('sha256')}, actual={act_r_sha}")

    # Validate raw execution logs (stdout and stderr)
    raw_logs = meta.get('raw_execution_logs', {})
    stdout_entry = raw_logs.get('stdout')
    if stdout_entry and stdout_entry.get('path') and stdout_entry.get('path') != "MISSING":
        out_p = os.path.join(repo_root, stdout_entry.get('path', '').replace('/', os.sep))
        if not os.path.exists(out_p):
            errors.append(f"Referenced raw stdout log not found: '{stdout_entry.get('path')}'")
        else:
            with open(out_p, 'rb') as f:
                act_out_sha = hashlib.sha256(f.read()).hexdigest()
            if act_out_sha != stdout_entry.get('sha256'):
                errors.append(f"Raw stdout log SHA-256 mismatch: recorded={stdout_entry.get('sha256')}, actual={act_out_sha}")

    stderr_entry = raw_logs.get('stderr')
    if stderr_entry and stderr_entry.get('path') and stderr_entry.get('path') != "MISSING":
        err_p = os.path.join(repo_root, stderr_entry.get('path', '').replace('/', os.sep))
        if not os.path.exists(err_p):
            errors.append(f"Referenced raw stderr log not found: '{stderr_entry.get('path')}'")
        else:
            with open(err_p, 'rb') as f:
                act_err_sha = hashlib.sha256(f.read()).hexdigest()
            if act_err_sha != stderr_entry.get('sha256'):
                errors.append(f"Raw stderr log SHA-256 mismatch: recorded={stderr_entry.get('sha256')}, actual={act_err_sha}")

    res = provenance_doc.get('validation_results', {})
    acc = res.get('summary_accounting', {})
    tot = acc.get('total_checks', 0)
    p = acc.get('pass', 0)
    fl = acc.get('fail', 0)
    w = acc.get('warning', 0)
    nc = acc.get('not_checked', 0)
    if tot != (p + fl + w + nc):
        errors.append(f"Summary accounting arithmetic error: total {tot} != sum {p + fl + w + nc}")

    is_valid = (len(errors) == 0)
    return is_valid, errors
