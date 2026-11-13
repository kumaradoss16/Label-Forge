"""
Label-Forge Evidence Integrity Validation Framework
Module: validation.evidence_integrity

Handles RFC 6901 JSON Pointer resolution, structured evidence references validation,
exact claim-status accounting, and recursive prohibited-image scanning.
"""

import os
from typing import Dict, List, Set, Any, Tuple, Optional

ALLOWED_CLAIM_STATUSES: Set[str] = {
    'VERIFIED_STATIC',
    'VERIFIED_RUNTIME',
    'VERIFIED_DOCUMENTATION',
    'INFERRED',
    'UNKNOWN',
    'NOT_PERFORMED'
}

PROHIBITED_IMAGE_EXTENSIONS: Tuple[str, ...] = (
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico',
    '.webp', '.tif', '.tiff', '.svg', '.avif', '.heic',
    '.heif', '.jfif'
)

def resolve_json_pointer(doc: Any, pointer: str) -> Any:
    """
    Resolves an RFC 6901 JSON pointer against a Python dictionary/list structure.
    Escaping:
      ~1 -> /
      ~0 -> ~
    """
    if not pointer or pointer == "":
        return doc
    if not pointer.startswith('/'):
        raise ValueError(f"Invalid JSON pointer (must start with '/'): '{pointer}'")

    parts = pointer[1:].split('/')
    curr = doc
    for part in parts:
        part = part.replace('~1', '/').replace('~0', '~')
        if isinstance(curr, list):
            try:
                idx = int(part)
            except ValueError:
                raise IndexError(f"List index must be integer, got '{part}'")
            if idx < 0 or idx >= len(curr):
                raise IndexError(f"Index {idx} out of range (length {len(curr)})")
            curr = curr[idx]
        elif isinstance(curr, dict):
            if part not in curr:
                raise KeyError(f"Key '{part}' not found in dict")
            curr = curr[part]
        else:
            raise KeyError(f"Cannot traverse into primitive value at '{part}'")
    return curr

def validate_status_accounting(
    claims: List[Dict[str, Any]],
    declared_status_counts: Dict[str, int],
    allowed_statuses: Set[str] = ALLOWED_CLAIM_STATUSES
) -> Dict[str, Any]:
    """
    Enforces exact full-dictionary status equality:
    1. Every claim has exactly one recognized status.
    2. Claim IDs are unique.
    3. No unknown statuses exist.
    4. Declared status dictionary keys exactly match allowed_statuses.
    5. Actual counts match declared counts for every single key.
    6. Total count matches array length.
    """
    errors: List[str] = []
    claim_ids = [c.get('id') for c in claims]
    duplicate_ids = [cid for cid in set(claim_ids) if claim_ids.count(cid) > 1]
    if duplicate_ids:
        errors.append(f"Duplicate claim IDs found: {duplicate_ids}")

    actual_counts: Dict[str, int] = {st: 0 for st in allowed_statuses}
    unexpected_claim_statuses: List[Tuple[str, str]] = []

    for c in claims:
        cid = c.get('id', 'UNKNOWN')
        st = c.get('status')
        if not st:
            errors.append(f"Claim {cid} missing status field")
            continue
        if st not in allowed_statuses:
            unexpected_claim_statuses.append((cid, st))
            errors.append(f"Claim {cid} has unrecognized status: '{st}'")
        else:
            actual_counts[st] += 1

    # Check declared categories
    declared_keys = set(declared_status_counts.keys())
    missing_declared_categories = allowed_statuses - declared_keys
    unexpected_declared_categories = declared_keys - allowed_statuses

    if missing_declared_categories:
        errors.append(f"Declared status dictionary missing categories: {missing_declared_categories}")
    if unexpected_declared_categories:
        errors.append(f"Declared status dictionary has unexpected categories: {unexpected_declared_categories}")

    # Check exact count matches
    mismatched_counts: Dict[str, Dict[str, int]] = {}
    for st in allowed_statuses:
        act = actual_counts.get(st, 0)
        dec = declared_status_counts.get(st, 0)
        if act != dec:
            mismatched_counts[st] = {'actual': act, 'declared': dec}
            errors.append(f"Status count mismatch for '{st}': actual={act}, declared={dec}")

    # Total count check
    total_claims = len(claims)
    sum_actual = sum(actual_counts.values())
    if sum_actual != total_claims:
        errors.append(f"Total claims array length ({total_claims}) != sum of actual counts ({sum_actual})")

    is_valid = (len(errors) == 0)

    return {
        'is_valid': is_valid,
        'errors': errors,
        'total_claims': total_claims,
        'actual_counts': actual_counts,
        'declared_counts': declared_status_counts,
        'mismatched_counts': mismatched_counts,
        'duplicate_ids': duplicate_ids
    }

def scan_prohibited_images(
    target_directory: str,
    prohibited_extensions: Tuple[str, ...] = PROHIBITED_IMAGE_EXTENSIONS,
    follow_symlinks: bool = False
) -> Dict[str, Any]:
    """
    Recursively scans target_directory for files with prohibited image extensions.
    Guards against symlink directory traversal outside the root.
    Records any traversal or access errors explicitly.
    """
    found_images: List[str] = []
    traversal_errors: List[str] = []

    if not os.path.exists(target_directory):
        return {
            'is_clean': True,
            'directory_exists': False,
            'found_images': [],
            'traversal_errors': [f"Directory not found: '{target_directory}'"]
        }

    real_target_root = os.path.realpath(target_directory)

    try:
        for root, dirs, files in os.walk(target_directory, followlinks=follow_symlinks):
            # Check symlink boundary
            if not follow_symlinks:
                real_current = os.path.realpath(root)
                if not real_current.startswith(real_target_root):
                    traversal_errors.append(f"Symlink directory traversal detected outside target: '{root}'")
                    continue

            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in prohibited_extensions:
                    rel_p = os.path.relpath(os.path.join(root, f), target_directory).replace('\\', '/')
                    found_images.append(rel_p)

    except Exception as e:
        traversal_errors.append(f"Filesystem traversal exception: {str(e)}")

    is_clean = (len(found_images) == 0 and len(traversal_errors) == 0)

    return {
        'is_clean': is_clean,
        'directory_exists': True,
        'found_images': found_images,
        'traversal_errors': traversal_errors
    }

def validate_structured_evidence_reference(
    ref: Dict[str, Any],
    repo_root: str,
    empirical_test_ids: Optional[Set[str]] = None
) -> Tuple[bool, str]:
    """
    Validates an individual structured evidence reference:
    - Path safety (repository-relative, no traversal, no escapes).
    - File existence on disk.
    - JSON pointer validity and non-null resolution.
    - Runtime test ID existence.
    """
    rtype = ref.get('type')
    rpath = ref.get('path')

    if not rtype:
        return False, "Missing 'type' in evidence reference"
    if not rpath:
        return False, "Missing 'path' in evidence reference"

    # Path traversal and safety checks
    if os.path.isabs(rpath) or '..' in rpath or '\\' in rpath or rpath.startswith('/'):
        return False, f"Invalid path (must be repository-relative forward-slash path): '{rpath}'"

    full_path = os.path.join(repo_root, rpath.replace('/', os.sep))
    real_repo_root = os.path.realpath(repo_root)
    real_file_path = os.path.realpath(full_path)

    if not real_file_path.startswith(real_repo_root):
        return False, f"Path escapes repository root: '{rpath}'"

    if not os.path.exists(full_path):
        return False, f"Referenced file missing on disk: '{rpath}'"

    if rtype == 'file':
        return True, "File reference verified"

    elif rtype == 'json_pointer':
        pointer = ref.get('pointer')
        if not pointer:
            return False, "Missing 'pointer' field in json_pointer reference"
        try:
            import json
            with open(full_path, 'r', encoding='utf-8') as jf:
                jdoc = json.load(jf)
            val = resolve_json_pointer(jdoc, pointer)
            if val is None:
                return False, f"JSON pointer '{pointer}' resolved to None in '{rpath}'"
            return True, f"JSON pointer '{pointer}' successfully resolved"
        except Exception as e:
            return False, f"JSON pointer '{pointer}' failed in '{rpath}': {str(e)}"

    elif rtype == 'runtime_test':
        test_id = ref.get('test_id')
        if not test_id:
            return False, "Missing 'test_id' in runtime_test reference"
        if empirical_test_ids is not None:
            if test_id not in empirical_test_ids:
                return False, f"Test ID '{test_id}' not found in authoritative runtime test set"
        return True, f"Runtime test reference '{test_id}' verified"

    else:
        return False, f"Unknown reference type: '{rtype}'"
