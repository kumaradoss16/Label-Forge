"""
Label-Forge Evidence Integrity Validation Framework
Module: validation.evidence_integrity

Handles RFC 6901 JSON Pointer resolution, structured evidence references validation,
exact claim-status accounting, and recursive prohibited-image scanning.
"""

import os
import re
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

def decode_reference_token(token: str) -> str:
    """
    Decodes an RFC 6901 reference token.
    Enforces strict RFC 6901 rules:
    - '~1' decodes to '/'
    - '~0' decodes to '~'
    - Any '~' followed by a character other than '0' or '1' is an error.
    - A trailing '~' is an error.
    """
    i = 0
    n = len(token)
    res = []
    while i < n:
        if token[i] == '~':
            if i + 1 >= n:
                raise ValueError(f"Invalid RFC 6901 JSON pointer: trailing '~' in token '{token}'")
            next_c = token[i + 1]
            if next_c == '0':
                res.append('~')
                i += 2
            elif next_c == '1':
                res.append('/')
                i += 2
            else:
                raise ValueError(f"Invalid RFC 6901 JSON pointer: invalid escape sequence '~{next_c}' in token '{token}'")
        else:
            res.append(token[i])
            i += 1
    return "".join(res)

def resolve_json_pointer(doc: Any, pointer: str) -> Any:
    """
    Resolves an RFC 6901 JSON pointer against a Python dictionary/list structure.
    Enforces strict RFC 6901 syntax validation:
    - Pointer must be empty string (whole doc) or start with '/'
    - Reference tokens are separated by '/'
    - Tokens are strictly decoded with decode_reference_token
    - Array indexes must be non-negative integers without leading zeros or signs
    """
    if not pointer or pointer == "":
        return doc
    if not pointer.startswith('/'):
        raise ValueError(f"Invalid RFC 6901 JSON pointer (must start with '/'): '{pointer}'")

    raw_parts = pointer[1:].split('/')
    curr = doc
    for raw_part in raw_parts:
        part = decode_reference_token(raw_part)
        if isinstance(curr, list):
            # RFC 6901 Section 4: array-index = "0" / ( %x31-39 *(%x30-39) )
            # Strict ASCII digit check: reject Unicode digits, leading zeros, signs, etc.
            if not re.fullmatch(r'^(?:0|[1-9][0-9]*)$', part):
                raise IndexError(f"Invalid array index token: '{part}' (must be non-negative ASCII integer without leading zeros)")
            idx = int(part)
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
    CRITICAL ACCEPTANCE RULE:
    - If target_directory does not exist: is_clean is FALSE (directory_exists = False).
    - If any traversal/permission error occurs: is_clean is FALSE.
    - If any prohibited image is found: is_clean is FALSE.
    """
    found_images: List[str] = []
    traversal_errors: List[str] = []

    if not os.path.exists(target_directory):
        return {
            'is_clean': False,
            'directory_exists': False,
            'found_images': [],
            'traversal_errors': [f"Directory not found: '{target_directory}'"]
        }

    real_target_root = os.path.realpath(target_directory)

    def on_walk_error(err: OSError):
        traversal_errors.append(f"Filesystem traversal error at '{err.filename}': {err.strerror}")

    def is_contained_in_target(path_to_check: str) -> bool:
        real_p = os.path.realpath(path_to_check)
        try:
            common = os.path.commonpath([real_target_root, real_p])
            return os.path.normcase(common) == os.path.normcase(real_target_root)
        except ValueError:
            return False

    try:
        for root, dirs, files in os.walk(target_directory, followlinks=follow_symlinks, onerror=on_walk_error):
            if not is_contained_in_target(root):
                traversal_errors.append(f"Symlink directory traversal detected outside target: '{root}'")
                continue

            for d in list(dirs):
                dpath = os.path.join(root, d)
                if os.path.islink(dpath) and not follow_symlinks:
                    if not is_contained_in_target(dpath):
                        traversal_errors.append(f"Symlinked directory escapes target root: '{dpath}' -> '{os.path.realpath(dpath)}'")

            for f in files:
                fpath = os.path.join(root, f)
                if os.path.islink(fpath) and not follow_symlinks:
                    if not is_contained_in_target(fpath):
                        traversal_errors.append(f"Symlinked file escapes target root: '{fpath}' -> '{os.path.realpath(fpath)}'")

                ext = os.path.splitext(f)[1].lower()
                if ext in prohibited_extensions:
                    rel_p = os.path.relpath(fpath, target_directory).replace('\\', '/')
                    found_images.append(rel_p)

    except Exception as e:
        traversal_errors.append(f"Filesystem traversal exception: {str(e)}")

    is_clean = (len(found_images) == 0 and len(traversal_errors) == 0)

    return {
        'is_clean': is_clean,
        'directory_exists': True,
        'found_images': sorted(found_images),
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

    full_path = os.path.normpath(os.path.join(repo_root, rpath.replace('/', os.sep)))
    real_repo_root = os.path.realpath(repo_root)
    real_file_path = os.path.realpath(full_path)

    # Robust path-aware containment via os.path.commonpath and normalized drive case
    try:
        common = os.path.commonpath([real_repo_root, real_file_path])
        if os.path.normcase(common) != os.path.normcase(real_repo_root):
            return False, f"Path escapes repository root via traversal: '{rpath}'"
    except ValueError:
        return False, f"Path on different drive or invalid path: '{rpath}'"

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

def validate_execution_artifact(
    artifact_entry: Dict[str, Any],
    repo_root: str,
    expected_run_id: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Validates an individual execution artifact (e.g. stdout.log or stderr.log):
    - Path safety (relative, repository-contained, no traversal, no symlink escape)
    - File existence and regular file verification
    - Byte size calculation and exact comparison
    - SHA-256 calculation and exact comparison
    - Run ID match if specified
    """
    if not isinstance(artifact_entry, dict):
        return False, "Artifact entry must be a dictionary"

    rel_path = artifact_entry.get("path")
    if not rel_path:
        return False, "Missing 'path' in artifact entry"

    # Traversal and slash checks
    if os.path.isabs(rel_path) or ".." in rel_path or "\\" in rel_path or rel_path.startswith("/"):
        return False, f"Invalid artifact path (must be repository-relative forward-slash): '{rel_path}'"

    full_path = os.path.normpath(os.path.join(repo_root, rel_path.replace("/", os.sep)))
    real_repo_root = os.path.realpath(repo_root)
    real_file_path = os.path.realpath(full_path)

    try:
        common = os.path.commonpath([real_repo_root, real_file_path])
        if os.path.normcase(common) != os.path.normcase(real_repo_root):
            return False, f"Artifact path escapes repository root: '{rel_path}'"
    except ValueError:
        return False, f"Artifact path on different drive or invalid: '{rel_path}'"

    if not os.path.exists(full_path):
        return False, f"Artifact file missing on disk: '{rel_path}'"

    if not os.path.isfile(full_path):
        return False, f"Artifact path is not a regular file: '{rel_path}'"

    if os.path.islink(full_path):
        # Additional symlink boundary check
        target_real = os.path.realpath(full_path)
        common_sym = os.path.commonpath([real_repo_root, target_real])
        if os.path.normcase(common_sym) != os.path.normcase(real_repo_root):
            return False, f"Artifact symlink escapes repository root: '{rel_path}'"

    with open(full_path, "rb") as f:
        data = f.read()

    actual_size = len(data)
    import hashlib
    actual_sha = hashlib.sha256(data).hexdigest()

    expected_size = artifact_entry.get("byte_size")
    if expected_size is not None and expected_size != actual_size:
        return False, f"Artifact byte size mismatch for '{rel_path}': expected {expected_size}, got {actual_size}"

    expected_sha = artifact_entry.get("sha256")
    if expected_sha and expected_sha != actual_sha:
        return False, f"Artifact SHA-256 mismatch for '{rel_path}': expected {expected_sha}, got {actual_sha}"

    if expected_run_id and artifact_entry.get("run_id"):
        if artifact_entry.get("run_id") != expected_run_id:
            return False, f"Artifact run_id mismatch for '{rel_path}': expected {expected_run_id}, got {artifact_entry.get('run_id')}"

    return True, f"Artifact '{rel_path}' verified (size: {actual_size}, sha: {actual_sha[:8]}...)"

