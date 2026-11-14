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
) -> Tuple[bool, str]:
    """
    Verifies that the final merge commit resolves to a tree SHA that is
    byte-for-byte identical to the validated tree SHA.
    """
    ok, info, msg = resolve_git_commit_and_tree(final_merge_commit, repo_root)
    if not ok or info is None:
        return False, f"Failed to verify final merge commit: {msg}"

    actual_merge_tree = info['tree_sha']
    if actual_merge_tree != validated_tree_sha:
        return False, f"Final merge tree mismatch: commit '{final_merge_commit}' has tree '{actual_merge_tree}', expected validated tree '{validated_tree_sha}'"

    return True, f"Final merge commit '{final_merge_commit}' tree identity verified ({actual_merge_tree})"
