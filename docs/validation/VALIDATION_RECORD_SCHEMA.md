# Canonical Validation Record Schema Specification

**Standard Version:** 1.1.2.2.4.2  
**Governing Standard:** Fail-Closed Cryptographic Evidence Reconciliation  
**Applicability:** All Phase 1.x Validation Engines & Independent Evidence Auditors  

---

## 1. Overview & Purpose

This specification defines the authoritative **13-field canonical record schema** for all validation checks executed within the Label-Forge project. Every executed check must produce a structured record conforming exactly to these requirements before it can be accepted by the stage accounting aggregator, independent auditor, or release gate engine.

---

## 2. Canonical 13-Field Schema Specification

Each validation record must be represented as a JSON object containing the following 13 canonical fields:

| Field Name | Type | Allowed Values / Format | Description & Invariants |
| :--- | :--- | :--- | :--- |
| `check_id` | `string` | Regex: `^[A-Z0-9_-]{3,64}$` | Globally unique identifier for the check (e.g. `PE-HDR-01`, `AC-01-CLAIM`). Duplicates are strictly rejected. |
| `stage_id` | `string` | Member of `STAGE_REGISTRY` | Identifies which of the 10 registered validation stages owns this check. Empty or unregistered stages fail validation. |
| `claim_id` | `string` | Regex: `^(C-[0-9]{2}|GENERAL|AC-[0-9]{2})$` | Identifies the empirical claim or acceptance criterion substantiated by this check. |
| `evidence_path` | `string` | Relative path with `/` separators | Path from repository root to primary evidence file. Must be contained within `REPO_ROOT` and must not be a symlink. |
| `evidence_sha256` | `string` | Regex: `^[a-f0-9]{64}$` | Lowercase hexadecimal SHA-256 hash of the evidence file referenced by `evidence_path`. |
| `result_status` | `string` | `PASS`, `FAIL`, `WARNING`, `BLOCKED`, `NOT_CHECKED`, `NOT_APPLICABLE` | Verification outcome token. Only `PASS` contributes to acceptance gates. |
| `message` | `string` | Non-empty string | Human-readable explanation of the test outcome, evidence observed, and values reconciled. |
| `execution_timestamp_utc` | `string` | ISO 8601 UTC timestamp | UTC timestamp of check execution. Must satisfy $\text{process\_start} \le t \le \text{process\_completion}$. |
| `validator_version` | `string` | Semver format (e.g. `1.1.2.2.4.2`) | Version of the validator engine executing the check. |
| `target_binary_sha256` | `string` | `d3498925149b91c646351e91638906ca4455b2a4cd8db82775bb6860d67d8594` | Lowercase SHA-256 of authoritative target `BarTend.exe`. |
| `git_commit_sha` | `string` | 40-character lowercase hex SHA | Commit SHA of the tree under validation. |
| `environment_hash` | `string` | 16-to-64 hex characters | Hash representing operating system, architecture, and Python runtime environment. |
| `execution_duration_ms` | `number` | Float or integer $\ge 0.0$ | Time spent executing this check in milliseconds. |

---

## 3. Allowed Result Status Enum Tokens

The status token must be strictly one of the six allowed enum values:

- **`PASS`**: The check was genuinely executed, evidence was resolved on disk, cryptographic hashes matched, and all assertions passed.
- **`FAIL`**: The check was executed, and one or more assertions, cryptographic hashes, or file checks failed. Fails release gates.
- **`WARNING`**: Non-critical discrepancy observed. Requires explicit documented sign-off; treated as blocking in fail-closed release gates.
- **`BLOCKED`**: Prerequisites could not be met (e.g. missing target binary or missing dependency). Blocks release gates.
- **`NOT_CHECKED`**: Check was skipped or omitted during execution. Must never be treated as approval. Blocks release gates.
- **`NOT_APPLICABLE`**: Check does not apply to this platform or execution mode. Does not contribute to PASS totals.

---

## 4. Timestamp Lifecycle Constraints

1. **Ordering Invariant:** Every record's `execution_timestamp_utc` must satisfy:
   $$\text{process\_start\_utc} \le \text{execution\_timestamp\_utc} \le \text{process\_completion\_utc}$$
2. **Monotonic Clocks:** Duration measurements must be obtained via `time.monotonic()` or `time.perf_counter()` to prevent system clock adjustments from distorting measured elapsed times.
3. **UTC Strictness:** Timestamps must be recorded in UTC with explicit timezone indicator (`+00:00` or `Z`). Local offsets without UTC conversion are prohibited.

---

## 5. Filesystem Containment and Symlink Safety

1. **Repository Containment:** All `evidence_path` and `evidence_refs` entries must resolve strictly within the repository workspace root:
   $$\text{commonpath}([\text{realpath}(\text{REPO\_ROOT}), \text{realpath}(\text{file\_path})]) = \text{realpath}(\text{REPO\_ROOT})$$
2. **Traversal Prohibition:** Paths must be relative, use standard forward slashes (`/`), must not start with `/` or `\`, and must not contain `..` path traversal segments.
3. **Symlink Prohibition:** Every referenced evidence file and log artifact must be a regular file (`os.path.isfile(p)` is `True` and `os.path.islink(p)` is `False`). Symlinks, hardlinks across security boundaries, and NTFS reparse points are strictly prohibited.

---

## 6. Backward Compatibility & Field Aliases

For interoperability with historical Phase 1 validation artifacts, consumers and parsers should accept the following standard field aliases:

| Canonical Field | Recognized Historical Aliases |
| :--- | :--- |
| `result_status` | `status`, `check_status` |
| `execution_timestamp_utc` | `executed_at_utc`, `execution_timestamp`, `timestamp_utc` |
| `evidence_path` | `evidence_refs` (when list with single string element) |
| `check_id` | `id` |
| `message` | `actual_result`, `detail` |

---

## 7. Stage Accounting Mathematical Invariants

For any set of validation records $R$, the stage accounting aggregator must verify:
1. Total record count equals sum of status counts:
   $$|R| = N_{\text{PASS}} + N_{\text{FAIL}} + N_{\text{WARNING}} + N_{\text{BLOCKED}} + N_{\text{NOT\_CHECKED}} + N_{\text{NOT\_APPLICABLE}}$$
2. Total check count equals sum of checks across all 10 registered stages:
   $$|R| = \sum_{s \in \text{STAGE\_REGISTRY}} N_s$$
3. For each stage $s$, stage total equals sum of stage statuses:
   $$N_s = N_{s,\text{PASS}} + N_{s,\text{FAIL}} + N_{s,\text{WARNING}} + N_{s,\text{BLOCKED}} + N_{s,\text{NOT\_CHECKED}} + N_{s,\text{NOT\_APPLICABLE}}$$
4. Zero records may contain empty, null, or unregistered `stage_id`.
