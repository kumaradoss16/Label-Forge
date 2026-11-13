"""
Label-Forge Evidence Integrity Validation Framework
Module: validation.dependency_validation

Implements exact set- and frequency-based direct-import category partition validation.
Enforces that categorized modules form a true non-overlapping partition of canonical direct imports.
"""

from typing import Dict, List, Set, Tuple, Any

def validate_direct_import_partition(
    canonical_direct_imports: List[str],
    categorized_modules_dict: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Validates that categorized_modules_dict forms an exact partition of canonical_direct_imports:
    1. Canonical direct imports have 0 duplicates.
    2. Each category has 0 internal duplicates.
    3. Cross-category overlap is 0 (each module assigned to <= 1 category).
    4. Missing modules is 0 (Canonical \\ Categorized == 0).
    5. Unexpected modules is 0 (Categorized \\ Canonical == 0).
    6. Exact equality: Categorized set == Canonical set and total counts match.
    """
    canonical_norm = [m.strip().upper() for m in canonical_direct_imports]
    canonical_set = set(canonical_norm)

    # 1. Canonical duplicate detection
    canonical_duplicates = [m for m in canonical_set if canonical_norm.count(m) > 1]

    # 2. Category internal duplicate detection and mapping
    category_internal_duplicates: Dict[str, List[str]] = {}
    categorized_all: List[str] = []
    category_assignment_map: Dict[str, List[str]] = {}

    for cat_name, cat_mods in categorized_modules_dict.items():
        cat_norm = [m.strip().upper() for m in cat_mods]
        dups = [m for m in set(cat_norm) if cat_norm.count(m) > 1]
        if dups:
            category_internal_duplicates[cat_name] = dups

        for m in cat_norm:
            categorized_all.append(m)
            category_assignment_map.setdefault(m, []).append(cat_name)

    # 3. Cross-category duplicates
    cross_category_overlaps = {
        m: cats for m, cats in category_assignment_map.items() if len(cats) > 1
    }

    # 4. Missing & Unexpected
    categorized_set = set(categorized_all)
    missing_modules = list(canonical_set - categorized_set)
    unexpected_modules = list(categorized_set - canonical_set)

    # 5. Exact partition boolean
    is_exact_partition = (
        len(canonical_duplicates) == 0 and
        len(category_internal_duplicates) == 0 and
        len(cross_category_overlaps) == 0 and
        len(missing_modules) == 0 and
        len(unexpected_modules) == 0 and
        categorized_set == canonical_set and
        len(categorized_all) == len(canonical_norm)
    )

    return {
        'is_exact_partition': is_exact_partition,
        'canonical_count': len(canonical_norm),
        'canonical_unique_count': len(canonical_set),
        'canonical_duplicates': canonical_duplicates,
        'categorized_count': len(categorized_all),
        'categorized_unique_count': len(categorized_set),
        'category_internal_duplicates': category_internal_duplicates,
        'cross_category_overlaps': cross_category_overlaps,
        'missing_modules': missing_modules,
        'unexpected_modules': unexpected_modules
    }
