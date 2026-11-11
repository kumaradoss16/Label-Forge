# Phase 1.1: Correction Log & Discrepancy Resolution Register

**Project:** Label-Forge  
**Milestone:** Phase 1.1 — Evidence Reconciliation & Validation  
**Target:** Seagull Scientific BarTender Designer 11.4 (`BarTend.exe`)  
**Date:** November 2026 (Updated Baseline)  
**Auditor:** Antigravity Senior Reverse Engineering Team  

---

## 1. Overview of Corrections

This register documents every discrepancy, contradiction, inaccurate metric, or unverified inference identified in prior Phase 1 reverse-engineering reports (Reports 11–19) and the corresponding authoritative resolution established in Phase 1.1.

---

## 2. Itemized Correction Log

### Item CORR-001: BarTend.exe Cryptographic Hashes & File Size

- **Original Claim (Report 11):**
  - MD5: `7d73010b91dcfaec676bb062bf6a20bc`
  - SHA-1: `4633e9ec2d8150eafe0ee994c6ca9c2bf41e39eb`
  - File Size: `20,774,984` bytes
- **Discrepancy / Problem Identified:**
  - The MD5 and SHA-1 values reported in Report 11 did not match the actual binary file on disk (`D:\BarTender\BarTend.exe`) or `evidence/phase1/target_identity.json`.
- **Root Cause:**
  - Stale draft placeholder values were copied into Report 11 from an initial template before final disk verification.
- **Corrected Claim:**
  - File Size: `20,774,984` bytes (19.81 MB)
  - MD5: `7af37ab384391fcc03935a569d705aa0`
  - SHA-1: `7a57fefa26e99ddec6a46625a8cc17c5a87593aa`
  - SHA-256: `d3498925149b91c646351e91638906ca4455b2a4cd8db82775bb6860d67d8594`
- **Verification Evidence:**
  - Python hashlib calculation on `D:\BarTender\BarTend.exe`. Validated via `scripts/validate-phase1-evidence.py`.
- **Affected Documents Updated:**
  - `reports/11_PHASE1_TARGET_IDENTITY.md`
  - `reports/19_PHASE1_REVERSE_ENGINEERING_SUMMARY.md`
  - `evidence/phase1/reconciliation/canonical_target_identity.json`

---

### Item CORR-002: Entry Point RVA and PE Section Headers

- **Original Claim (Report 11):**
  - Address of Entry Point: `0x6f3e1c`
  - Sections: `.text`, `.rdata`, `.data`, `.pdata`, `.tls`, `.rsrc`, `.reloc`
- **Discrepancy / Problem Identified:**
  - Parsing the PE optional header reveals AddressOfEntryPoint is `0x97d0fb`.
  - The section `.tls` does NOT exist in `BarTend.exe`. The actual section at index 1 is `.nep` (Native Entry Point).
- **Corrected Claim:**
  - Address of Entry Point: `0x97d0fb`.
  - Sections (7): `.text` (`0x1000`), `.nep` (`0xa6d000`), `.rdata` (`0xa83000`), `.data` (`0x10f6000`), `.pdata` (`0x11fd000`), `.rsrc` (`0x126e000`), `.reloc` (`0x13a3000`).
- **Verification Evidence:**
  - Direct binary parsing of `IMAGE_NT_HEADERS64.OptionalHeader.AddressOfEntryPoint` and `IMAGE_SECTION_HEADER`.
- **Affected Documents Updated:**
  - `reports/11_PHASE1_TARGET_IDENTITY.md`
  - `evidence/phase1/reconciliation/canonical_target_identity.json`

---

### Item CORR-003: Authenticode Security Directory Bounds

- **Original Claim (Report 11):**
  - Signature Offset: `0x13c7200`, Size: `9,472` bytes.
- **Discrepancy / Problem Identified:**
  - $0x13c7200 + 9472 = 20,747,264$ bytes, leaving an unaccounted 27,720 bytes before the file end (`20,774,984`).
- **Corrected Claim:**
  - Signature File Offset: `0x13cb000` (Decimal: `20,754,432`).
  - Signature Size: `20,552` bytes (`0x5048`).
  - Mathematical Proof: $20,754,432 + 20,552 = 20,774,984$ bytes, terminating exactly at the file boundary.
- **Verification Evidence:**
  - OptionalHeader Data Directory 4 inspection.
- **Affected Documents Updated:**
  - `reports/11_PHASE1_TARGET_IDENTITY.md`
  - `reports/20_PHASE1_1_EVIDENCE_RECONCILIATION.md`
  - `evidence/phase1/reconciliation/canonical_target_identity.json`

---

### Item CORR-004: Component Population & Filesystem Census

- **Original Claim (Report 12):**
  - "Component Population: 589 Total Files (24 Executables, 433 Dynamic Link Libraries)"
- **Discrepancy / Problem Identified:**
  - Conflated total filesystem items with files.
- **Corrected Claim:**
  - Total Filesystem Items: **589 items** (34 subdirectories + 555 files).
  - Mutually exclusive file breakdown: 24 EXEs, 433 DLLs, 4 OCXs, 29 configs, 40 XMLs, 10 XSDs, 7 PDFs, 3 INIs, 2 manifests, 3 other = 555 files.
- **Verification Evidence:**
  - Filesystem audit and automated sum verification in `scripts/validate-phase1-evidence.py`.
- **Affected Documents Updated:**
  - `reports/12_PHASE1_APPLICATION_STRUCTURE.md`
  - `reports/19_PHASE1_REVERSE_ENGINEERING_SUMMARY.md`
  - `evidence/phase1/reconciliation/file_inventory_summary.json`

---

### Item CORR-005: PE Binary Architecture & Managed vs. Native Classification

- **Original Claim (Report 12):**
  - 331 Managed .NET Assemblies, 102 Native C++ DLLs.
- **Corrected Claim:**
  - Of 461 total PE binaries (24 EXE + 433 DLL + 4 OCX):
    - Managed IL-Only: 332 binaries (19 EXE, 313 DLL)
    - Mixed-Mode C++/CLI: 20 binaries (2 EXE, 18 DLL)
    - Native x64: 27 binaries (1 EXE, 22 DLL, 4 OCX)
    - Native x86: 82 binaries (2 EXE, 80 satellite Win32 resource DLLs)
    - Sum: $332 + 20 + 27 + 82 = 461$ PE binaries.
- **Verification Evidence:**
  - COM descriptor CLI header inspection and machine architecture check of all 461 binaries.
- **Affected Documents Updated:**
  - `reports/12_PHASE1_APPLICATION_STRUCTURE.md`
  - `evidence/phase1/reconciliation/file_inventory_summary.json`
  - `evidence/phase1/reconciliation/module_architecture_summary.json`

---

### Item CORR-006: Elimination of Hypothetical / Phantom DLLs

- **Original Claim (Reports 12, 13, 15, 18):**
  - Core subsystems were cited as separate DLLs: `BtEngine.dll`, `BtBarcode.dll`, `BtPrint.dll`, `BtSystem.dll`, `BtLic.dll`, `BtData.dll`, and `XtremeToolkitPro.dll`.
- **Discrepancy / Problem Identified:**
  - None of these files exist on disk.
- **Corrected Claim:**
  - Core geometry, twip transformations, and `CArchive` serialization reside natively inside `BarTend.exe` itself.
  - Barcode rasterization is handled by modular native plugins (`BarCode_QRCode.dll`, `BarCode_DataMatrix.dll`, etc.) and internal routines.
  - Codejock library is `ToolkitPro1531vc142x64U.dll` (10,844,184 bytes).
- **Verification Evidence:**
  - Direct filesystem verification and PE import table parsing.
- **Affected Documents Updated:**
  - `reports/12_PHASE1_APPLICATION_STRUCTURE.md`
  - `reports/13_PHASE1_DEPENDENCY_ANALYSIS.md`
  - `reports/15_PHASE1_NATIVE_BINARY_ANALYSIS.md`
  - `reports/18_PHASE1_FEATURE_TRACEABILITY.md`
  - `evidence/phase1/reconciliation/dependency_reconciliation.json`

---

### Item CORR-007: Tooling Boundary & Ghidra Decompilation Status

- **Original Claim (Report 15):**
  - Did not explicitly record Ghidra status, creating ambiguity regarding decompilation.
- **Corrected Claim:**
  - Deep native function decompilation via Ghidra is formally marked `[NOT_PERFORMED]`.
  - All native findings are strictly bounded to PE export tables, import descriptors, and REA CLI P/Invoke boundaries.
- **Verification Evidence:**
  - Tooling environment audit (`GHIDRA_INSTALL_DIR` unset).
- **Affected Documents Updated:**
  - `reports/15_PHASE1_NATIVE_BINARY_ANALYSIS.md`
  - `reports/19_PHASE1_REVERSE_ENGINEERING_SUMMARY.md`
  - `reports/20_PHASE1_1_EVIDENCE_RECONCILIATION.md`
  - `evidence/phase1/reconciliation/claim_register.json` (Claim `P1-018`)

---

### Item CORR-008: Coordinate Precision Rationale

- **Original Claim (Report 15):**
  - "Avoid Twip Inaccuracies: BarTender's use of integer twips leads to rounding errors when mapping to metric mm or high-DPI thermal dots."
- **Corrected Claim:**
  - Twips operate on integer discretization (±8.8 µm error). At 203 DPI, 1 thermal dot corresponds to ~7.0936 twips.
  - LabelForge's use of IEEE-754 double-precision canonical millimeters (`Length`) provides $< 1\text{ picometer}$ resolution, eliminates cumulative rounding drift across rotations, and matches international metric label die standards.
- **Verification Evidence:**
  - Mathematical analysis of coordinate systems and `LabelForge.Core.Geometry.Length`.
- **Affected Documents Updated:**
  - `reports/15_PHASE1_NATIVE_BINARY_ANALYSIS.md`
  - `reports/20_PHASE1_1_EVIDENCE_RECONCILIATION.md`

---

### Item CORR-009: PE Section .data Raw File Offset Reconciled

- **Original Inconsistency:**
  - `canonical_target_identity.json` reported `.data` Raw Data Offset as `0x10f2a00`, but preliminary Report 20 and Report 11 drafts cited `0x10f2c00`.
- **Verification Evidence:**
  - Section header 4 at file offset `0x380` has PointerToRawData = `0x10f2a00` and SizeOfRawData = `0xc8c00` (`822,272` bytes).
- **Authoritative Resolution:**
  - Reconciled all reports (Reports 11, 20, 21) to **`0x10f2a00`**.

---

### Item CORR-010: Disambiguation of CLR COM Descriptor and CLI Metadata Root RVAs

- **Original Inconsistency:**
  - Preliminary drafts cited `CLI Metadata Root: RVA 0xae9bc8` or conflated the CLR COM descriptor directory with the metadata root.
- **Verification Evidence:**
  - PE Optional Header Data Directory 14 (COM Descriptor): RVA `0xae9b90`, Size `72` bytes (`0x48`) located at file offset `0xae7390`.
  - `IMAGE_COR20_HEADER.MetaData`: DataDirectory pointing to RVA `0xc3ca00`, Size `3,111,676` bytes located at file offset `0xc3a200`.
- **Authoritative Resolution:**
  - Explicitly differentiated both structures across `canonical_target_identity.json`, `reports/11`, and `reports/20`.

---

### Item CORR-011: Strict Copyright Compliance & Removal of Proprietary Images

- **Original Inconsistency:**
  - The repository contained 40 proprietary extracted image files in `screenshots/` while documentation stated that proprietary assets must not be redistributed.
- **Authoritative Resolution:**
  - All 40 proprietary image files were **permanently deleted** from git version control.
  - Authored [`screenshots/UI_OBSERVATIONS_REFERENCE.md`](file:///E:/ReverseEngineering/Label-Forge-clone/screenshots/UI_OBSERVATIONS_REFERENCE.md) to preserve non-infringing analytical descriptions, mathematical 9-point anchor rules, and UI layout specifications.

---

### Item CORR-012: Narrowing of Functional Claims to Verifiable Scope

- **Original Inconsistency:**
  - Claims in early drafts extrapolated beyond direct static evidence (e.g., claiming absence of `BtEngine.dll` proved all geometry was inside `BarTend.exe`, or that `winspool.drv` imports proved the complete printing pipeline).
- **Authoritative Resolution:**
  - Narrowed claims to what evidence directly proves:
    - Absence of `BtEngine.dll` proves no separate DLL with that name exists in the target root; `CArchive` and geometry symbols in `BarTend.exe` prove core primitives are hosted there.
    - Barcode export analysis proves exported procedural C APIs for matrix rasterization, not internal dispatch architecture.
    - `winspool.drv` imports prove static Win32 spooler linkage.
    - Certificate offset proves physical PE directory file-boundary alignment, not cryptographic trust chain validity.
    - `CArchive`/`CObList` proves linkage to MFC serialization primitives, not full `.btw` schema discovery.

---

### Item CORR-013: Registration and Explicit Classification of Runtime Claims

- **Original Inconsistency:**
  - `claim_register.json` listed 0 claims as `VERIFIED_RUNTIME`, despite Report 20 discussing runtime experiments `RT-01`, `RT-02`, and `RT-03`.
- **Authoritative Resolution:**
  - Registered claims `P1-023` (`RT-01` process startup/activation), `P1-024` (`RT-02` print API license exception), and `P1-025` (`RT-03` COM ProgID automation) as **`VERIFIED_RUNTIME`** linked to `evidence/phase1/runtime_observations.json`.
  - Reconciled status totals: 20 `VERIFIED_STATIC`, 3 `VERIFIED_RUNTIME`, 1 `VERIFIED_DOCUMENTATION`, 1 `NOT_PERFORMED` (Total: 25 claims).

---

### Item CORR-014: Evidence Manifest SHA-256 Validation Suite Overhaul

- **Original Inconsistency:**
  - `scripts/validate-phase1-evidence.py` performed only JSON parse checks rather than verifying the actual SHA-256 digests in `validation_manifest.json`, hardcoded expected values, and lacked comprehensive accounting.
- **Authoritative Resolution:**
  - Completely overhauled `scripts/validate-phase1-evidence.py` to:
    - Derive expected target identity dynamically from `canonical_target_identity.json`.
    - Cryptographically compute and verify SHA-256 digests and file sizes for all tracked evidence files against `validation_manifest.json`.
    - Validate claim register integrity, claim counts, and evidence references.
    - Verify all 24 markdown reports.
    - Provide complete accounting (`PASS`, `FAIL`, `WARNING`, `NOT_CHECKED`) with deterministic exit codes.
