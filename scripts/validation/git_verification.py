"""
Label-Forge Evidence Integrity Validation Framework
Module: validation.git_verification

Handles independent Git object resolution, commit-to-tree verification,
and final merge revision equivalence checking.
Zero reliance on naive SHA string length checks.
"""

import os
import subprocess
from typing import Dict, Any, Tuple, Optional, List


def resolve_git_commit_and_tree(commit_ref: str, repo_root: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Independently resolves a Git commit reference using git cat-file.
    Returns: (is_valid, commit_info_dict, error_message)
    commit_info_dict contains:
      - commit_sha: 40-hex commit SHA
      - tree_sha: 40-hex tree SHA
      - parents: list of parent SHAs
      - author: author string
      - committer: committer string
    """
    if not commit_ref:
        return False, None, "Commit reference cannot be empty"

    try:
        # Resolve full 40-hex commit SHA
        full_commit = subprocess.check_output(
            ['git', 'rev-parse', '--verify', f"{commit_ref}^{{commit}}"],
            cwd=repo_root,
            stderr=subprocess.PIPE
        ).decode('utf-8').strip()
    except Exception as e:
        return False, None, f"Failed to resolve commit '{commit_ref}': {str(e)}"

    try:
        # Verify object type is commit
        obj_type = subprocess.check_output(
            ['git', 'cat-file', '-t', full_commit],
            cwd=repo_root,
            stderr=subprocess.PIPE
        ).decode('utf-8').strip()
        if obj_type != 'commit':
            return False, None, f"Git object '{full_commit}' is of type '{obj_type}', expected 'commit'"

        # Parse commit object content
        commit_content = subprocess.check_output(
            ['git', 'cat-file', '-p', full_commit],
            cwd=repo_root,
            stderr=subprocess.PIPE
        ).decode('utf-8')

        lines = commit_content.splitlines()
        tree_sha = None
        parents = []
        author = ""
        committer = ""

        for line in lines:
            if line.startswith('tree '):
                tree_sha = line.split()[1].strip()
            elif line.startswith('parent '):
                parents.append(line.split()[1].strip())
            elif line.startswith('author '):
                author = line[7:].strip()
            elif line.startswith('committer '):
                committer = line[10:].strip()
            elif line == "":
                # Commit header terminates on first empty line
                break

        if not tree_sha:
            return False, None, f"Commit object '{full_commit}' missing 'tree' header"

        # Verify that tree object actually exists in git object database
        tree_type = subprocess.check_output(
            ['git', 'cat-file', '-t', tree_sha],
            cwd=repo_root,
            stderr=subprocess.PIPE
        ).decode('utf-8').strip()
        if tree_type != 'tree':
            return False, None, f"Referenced tree object '{tree_sha}' is of type '{tree_type}', expected 'tree'"

        info = {
            'commit_sha': full_commit,
            'tree_sha': tree_sha,
            'parents': parents,
            'author': author,
            'committer': committer
        }
        return True, info, "Commit and tree objects independently verified"

    except Exception as e:
        return False, None, f"Error inspecting git object for commit '{full_commit}': {str(e)}"


def verify_final_merge_equivalence(
    final_merge_commit: str,
    validated_tree_sha: str,
    repo_root: str
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Verifies that the final merge commit resolves to a tree SHA and assesses its
    relationship to the validated tree SHA.
    Returns: (is_valid, message, details_dict)
    details_dict contains:
      - final_merge_commit: str
      - final_merge_tree: str
      - validated_tree_sha: str
      - tree_equivalence_status: 'TREE_EQUIVALENT' | 'TREE_DIFFERENT'
      - parents: List[str]
    """
    ok, info, msg = resolve_git_commit_and_tree(final_merge_commit, repo_root)
    if not ok or info is None:
        return False, f"Failed to verify final merge commit: {msg}", {}

    actual_merge_tree = info['tree_sha']
    is_equiv = (actual_merge_tree == validated_tree_sha)
    equiv_status = "TREE_EQUIVALENT" if is_equiv else "TREE_DIFFERENT"

    details = {
        'final_merge_commit': info['commit_sha'],
        'final_merge_tree': actual_merge_tree,
        'validated_tree_sha': validated_tree_sha,
        'tree_equivalence_status': equiv_status,
        'parents': info.get('parents', []),
        'author': info.get('author', ''),
        'committer': info.get('committer', '')
    }

    if is_equiv:
        return True, f"Final merge commit '{final_merge_commit}' tree identity verified (TREE_EQUIVALENT: {actual_merge_tree})", details
    else:
        return False, f"Final merge tree mismatch (TREE_DIFFERENT): commit '{final_merge_commit}' has tree '{actual_merge_tree}', expected validated tree '{validated_tree_sha}'", details


def verify_working_tree_cleanliness(repo_root: str) -> Tuple[bool, List[str]]:
    """
    Independently inspects git working-tree status with ZERO directory exclusions.
    Returns: (is_clean, dirty_lines)
    """
    try:
        porcelain = subprocess.check_output(
            ['git', 'status', '--porcelain'],
            cwd=repo_root,
            stderr=subprocess.PIPE
        ).decode('utf-8').strip()
        lines = [l.strip() for l in porcelain.splitlines() if l.strip()]
        return (len(lines) == 0), lines
    except Exception as e:
        return False, [f"git status failed: {str(e)}"]


def verify_provenance_lifecycle(
    repo_root: str,
    baseline_merge_commit: str,
    implementation_commit: str,
    sealing_commit: Optional[str] = None,
    final_merge_commit: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Validates complete lifecycle revision relationships:
    1. baseline_merge_commit exists
    2. implementation_commit exists
    3. sealing_commit exists (if provided) and has implementation_commit in its history
    4. final_merge_commit exists (if provided)
    """
    errors: List[str] = []
    ok_b, info_b, msg_b = resolve_git_commit_and_tree(baseline_merge_commit, repo_root)
    if not ok_b:
        errors.append(f"Baseline merge commit invalid: {msg_b}")

    ok_i, info_i, msg_i = resolve_git_commit_and_tree(implementation_commit, repo_root)
    if not ok_i:
        errors.append(f"Implementation commit invalid: {msg_i}")

    if sealing_commit and sealing_commit not in ("PENDING", "UNKNOWN"):
        ok_s, info_s, msg_s = resolve_git_commit_and_tree(sealing_commit, repo_root)
        if not ok_s:
            errors.append(f"Sealing commit invalid: {msg_s}")
        elif ok_i:
            try:
                subprocess.check_call(
                    ['git', 'merge-base', '--is-ancestor', implementation_commit, sealing_commit],
                    cwd=repo_root,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception:
                errors.append(f"Implementation commit '{implementation_commit}' is not an ancestor of sealing commit '{sealing_commit}'")

    if final_merge_commit and final_merge_commit not in ("PENDING", "UNKNOWN"):
        ok_m, info_m, msg_m = resolve_git_commit_and_tree(final_merge_commit, repo_root)
        if not ok_m:
            errors.append(f"Final merge commit invalid: {msg_m}")

    return (len(errors) == 0), errors

