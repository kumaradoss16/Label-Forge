# PHASE 1.1.2.2: TEST COVERAGE & INVARIANT TRACEABILITY MATRIX
## Production Function Verification & Negative Fixture Audit

- **Target Application:** Seagull Scientific BarTender Designer 11.4 (Build 11.4.238.365)
- **Primary Binary:** `D:\BarTender\BarTend.exe` (SHA-256: `d3498925149b91c646351e91638906ca4455b2a4cd8db82775bb6860d67d8594`)
- **Repository:** `https://github.com/kumaradoss16/Label-Forge.git`
- **Working Branch:** `phase1.1.2.2-independent-validator-audit`
- **Execution Date:** November 13, 2026
- **Status:** **`VERIFIED / 100% COVERAGE OF MANDATORY INVARIANTS (32/32 UNIT TESTS PASS)`**

---

## 1. Executive Summary

This document establishes the authoritative test coverage matrix for the Label-Forge Phase 1.1.2.2 validation framework. Every invariant mandated by the milestone specification (Section 7.3 and Section 19) is tested via real production functions located in `scripts/validation/`. All synthetic mock tampering has been eliminated; every negative test exercises actual production parsers, validators, and aggregation engines against isolated corrupted fixtures.

---

## 2. Invariant & Test Traceability Matrix

### 2.1 Positive Baseline Tests

| Test ID | Category | Target Production Function | Input Fixture / Data Source | Expected Status | Verified Assertion Invariant | Result |
| :---: | :--- | :--- | :--- | :---: | :--- | :---: |
| **`POS-01`** | RFC 6901 Pointer | `resolve_json_pointer` | Nested Python dictionary with slashes and tildes | `PASS` | Evaluates keys `/a/b/0`, `/slash~1key`, `/tilde~0key` accurately | **PASS** |
| **`POS-02`** | RFC 6901 Tokens | `decode_reference_token` | Valid escape strings `~0`, `~1`, `~01` | `PASS` | Decodes `~0` to `~`, `~1` to `/`, and `~01` to `~1` | **PASS** |
| **`POS-03`** | RFC 6901 Indices | `resolve_json_pointer` | Synthetic list with malformed index tokens (`/01`, `/-1`, `/abc`) | `PASS` | Rejects leading zeros, negatives, and non-digits via `IndexError` | **PASS** |
| **`POS-04`** | Dependency Partition | `validate_direct_import_partition` | Repository `dependency_reconciliation.json` | `PASS` | Exact partition equality: 48 modules, 0 duplicates, 0 overlaps | **PASS** |
| **`POS-05`** | Status Accounting | `validate_status_accounting` | Repository `claim_register.json` | `PASS` | Exact dictionary and count match across all 6 status categories | **PASS** |
| **`POS-06`** | Manifest Validation | `validate_evidence_manifest` | Repository `validation_manifest.json` | `PASS` | All 15 tracked evidence files exist with matching SHA-256 digests | **PASS** |
| **`POS-07`** | Release Gate | `evaluate_release_gate` | Dictionary of all 8 passing mandatory stages | `PASS` | Returns exit code `0` and status `PHASE 1.1.2.2 — APPROVED` | **PASS** |
| **`POS-08`** | Path Boundary | `validate_structured_evidence_reference` | Traversal path pointing to `../../../../Windows/System32/drivers/etc/hosts` | `PASS` | Rejects out-of-root traversal paths deterministically | **PASS** |

### 2.2 Mandatory Negative Fixture Suite (Section 7.3 Strictly Mapped)

| Test ID | Test Area | Target Production Function | Corrupted Fixture Description | Expected Outcome | Actual Verification |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **`T01`** | Missing evidence file | `validate_evidence_manifest` | Manifest fixture referencing nonexistent file | `FAIL` | `is_valid == False`, missing file assertion recorded |
| **`T02`** | File size mismatch | `validate_evidence_manifest` | File present on disk but declared `size_bytes` differs | `FAIL` | `is_valid == False`, size mismatch assertion recorded |
| **`T03`** | SHA-256 mismatch | `validate_evidence_manifest` | File present on disk but declared SHA-256 is `"0" * 64` | `FAIL` | `is_valid == False`, SHA-256 mismatch recorded |
| **`T04`** | Invalid manifest reference | `validate_structured_evidence_reference` | Reference with `../outside.json` or system path | `FAIL` | `ok == False`, traversal/boundary error returned |
| **`T05`** | Binary integrity mismatch | `validate_target_binary` | Executable fixture with wrong file size or digest | `FAIL` | `is_valid == False`, file size/digest failure recorded |
| **`T06`** | Invalid PE metadata | `validate_target_binary` | Binary fixture with invalid PE signature `NOTP` | `FAIL` | `is_valid == False`, PE parsing exception captured |
| **`T07`** | Missing dependency category | `validate_direct_import_partition` | Direct imports missing canonical DLL (`missing_modules`) | `FAIL` | `is_exact_partition == False`, missing module identified |
| **`T08`** | Duplicate dependency class | `validate_direct_import_partition` | Module assigned to multiple categories | `FAIL` | `is_exact_partition == False`, cross-category overlap detected |
| **`T09`** | Unexpected direct import | `validate_direct_import_partition` | Category containing undeclared module `EXTRA.DLL` | `FAIL` | `is_exact_partition == False`, unexpected module identified |
| **`T10`** | Unknown claim ID | `make_claim_assertion_registry` | Query for unregistered claim `P1-999` | `FAIL` | Registry returns `None` for unregistered identifier |
| **`T11`** | Missing claim evidence ref | `validate_structured_evidence_reference` | Malformed reference missing `type` or `path` | `FAIL` | Rejection returned with descriptive error |
| **`T12`** | Invalid JSON Pointer | `resolve_json_pointer` | Pointer with invalid escape `~2` or leading zero `/01` | `FAIL` | Raises `ValueError` or `IndexError` |
| **`T13`** | Missing referenced object | `resolve_json_pointer` | Pointer to nonexistent key `/missing_key` or index `/10` | `FAIL` | Raises `KeyError` or `IndexError` |
| **`T14`** | Invalid claim status | `validate_status_accounting` | Claim with unrecognized status `VERIFIED_UNSUPPORTED` | `FAIL` | `is_valid == False`, unrecognized status reported |
| **`T15`** | Incorrect claim totals | `validate_status_accounting` | Declared count (999) mismatching actual count (1) | `FAIL` | `is_valid == False`, count mismatch detected |
| **`T16`** | Missing status category | `validate_status_accounting` | Declared dictionary omitting mandatory status key | `FAIL` | `is_valid == False`, missing category reported |
| **`T17`** | Prohibited nested image | `scan_prohibited_images` | Tree with prohibited image in nested `sub1/sub2/` | `FAIL` | `is_clean == False`, prohibited image detected |
| **`T18`** | Missing screenshot dir | `scan_prohibited_images` | Nonexistent directory path | `FAIL` | `directory_exists == False`, `is_clean == False` |
| **`T19`** | Screenshot traversal error | `scan_prohibited_images` | File path passed as directory or traversal error | `FAIL` | `traversal_errors` populated, `is_clean == False` |
| **`T20`** | Source revision mismatch | `validate_provenance_record` | Provenance document with invalid or truncated commit SHA | `FAIL` | `is_valid == False`, commit SHA error returned |
| **`T21`** | Script/manifest hash mismatch | `validate_provenance_record` | Provenance document with altered validator/manifest SHA | `FAIL` | `is_valid == False`, hash mismatch error returned |
| **`T22`** | Incomplete validation stage | `evaluate_release_gate` | Stage results omitting mandatory validation stage | `BLOCKED` | Exit code `1`, status `PHASE 1.1.2.2 — BLOCKED` |
| **`T23`** | Mandatory check treated as PASS | `evaluate_release_gate` | Mandatory stage marked `STATUS_FAIL` | `FAIL` | Exit code `1`, status `PHASE 1.1.2.2 — FAILED` |
| **`T24`** | Warning/NOT_CHECKED approved | `evaluate_release_gate` | Stage marked `NOT_CHECKED` or `WARNING` | `BLOCKED` | Exit code `2` (NOT_CHECKED) or `1` (WARNING), blocked |

---

## 3. Test Suite Execution Summary

- **Runner:** `python -m unittest tests/test_validation_invariants.py`
- **Total Test Cases:** 32
- **Passing Test Cases:** 32 (100%)
- **Failing Test Cases:** 0 (0%)
- **Errors / Exceptions:** 0 (0%)
- **Execution Duration:** ~0.10 seconds
- **Zero Mock Tampering:** Verified. Every negative test invokes production code.
