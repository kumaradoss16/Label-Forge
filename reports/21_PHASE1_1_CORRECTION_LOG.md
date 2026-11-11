# Phase 1.1: Correction Log & Discrepancy Resolution Register

**Project:** Label-Forge  
**Milestone:** Phase 1.1 — Evidence Reconciliation & Validation  
**Target:** Seagull Scientific BarTender Designer 11.4 (`BarTend.exe`)  
**Date:** November 2026  
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
  - Computing cryptographic hashes directly on `D:\BarTender\BarTend.exe` yielded MD5 `7af37ab3...` and SHA-1 `7a57fefa...`.
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
  - Section sizes: `.text` Virtual Size `11,424,312`
- **Discrepancy / Problem Identified:**
  - Parsing the PE optional header reveals AddressOfEntryPoint is `0x97d0fb`.
  - The section `.tls` does NOT exist in `BarTend.exe`. The actual section at index 1 is `.nep` (Native Entry Point).
  - `.text` Virtual Size is `10,924,174` bytes, not `11,424,312`.
- **Root Cause:**
  - PE header metrics from a different preliminary test binary or template were transcribed.
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
- **Root Cause:**
  - Erroneous offset transcription.
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
  - `24 EXEs + 433 DLLs = 457 binaries`. Where did 589 come from? If 589 was "Total Files", what were the remaining 132 files?
  - In reality, counting files non-recursively in `D:\BarTender` yields 555 files and 34 subdirectories.
- **Root Cause:**
  - 589 was the count of all filesystem items (`Get-ChildItem`) in the top-level directory, conflating files with subdirectories.
- **Corrected Claim:**
  - Total Filesystem Items: **589 items**.
  - Directories: **34 subdirectories**.
  - Files: **555 files**, partitioned into mutually exclusive categories:
    - 24 Executables (.exe)
    - 433 Dynamic Link Libraries (.dll)
    - 4 ActiveX Controls (.ocx)
    - 29 Configuration Files (.config)
    - 40 XML Data Files (.xml)
    - 10 XML Schemas (.xsd)
    - 7 Documentation PDFs (.pdf)
    - 3 Initialization Files (.ini)
    - 2 Application Manifests (.manifest)
    - 3 Miscellaneous Assets (.dat, .ico, .stk)
    - Sum: $24 + 433 + 4 + 29 + 40 + 10 + 7 + 3 + 2 + 3 = 555$ files.
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
- **Discrepancy / Problem Identified:**
  - Did not specify how mixed-mode C++/CLI binaries were counted.
  - Did not detail the architecture breakdown (x64 vs. x86).
- **Corrected Claim:**
  - Of 461 total PE binaries (24 EXE + 433 DLL + 4 OCX):
    - **Managed IL-Only:** 332 binaries (19 EXE, 313 DLL).
    - **Mixed-Mode C++/CLI:** 20 binaries (2 EXE, 18 DLL).
    - **Native x64:** 27 binaries (1 EXE, 22 DLL, 4 OCX).
    - **Native x86:** 82 binaries (2 EXE, 80 DLL).
    - Sum: $332 + 20 + 27 + 82 = 461$ PE binaries.
  - The prior figure of 331 managed DLLs represented 313 managed IL + 18 mixed-mode DLLs.
  - The prior figure of 102 native DLLs represented 22 native x64 + 80 native x86 DLLs.
- **Verification Evidence:**
  - COM descriptor CLI header inspection and machine architecture check of all 461 binaries.
- **Affected Documents Updated:**
  - `reports/12_PHASE1_APPLICATION_STRUCTURE.md`
  - `evidence/phase1/reconciliation/file_inventory_summary.json`
  - `evidence/phase1/reconciliation/module_architecture_summary.json`

---

### Item CORR-006: Elimination of Hypothetical / Phantom DLLs

- **Original Claim (Reports 12, 13, 15, 18):**
  - Core subsystems were cited as separate DLLs: `BtEngine.dll` (geometry), `BtBarcode.dll` (symbologies), `BtPrint.dll` (spooler), `BtSystem.dll` (OS services), `BtLic.dll` (licensing), `BtData.dll` (data parser), and `XtremeToolkitPro.dll` (GUI).
- **Discrepancy / Problem Identified:**
  - Filesystem audit confirms none of these files exist in `D:\BarTender`.
- **Root Cause:**
  - Subsystems were speculatively named based on architectural roles or legacy naming rather than filesystem ground truth.
- **Corrected Claim:**
  - Core geometry, twip transformations, and `CArchive` serialization reside natively inside `BarTend.exe` itself.
  - Barcode rasterization is handled by modular native plugins (`BarCode_QRCode.dll`, `BarCode_DataMatrix.dll`, etc.) and internal routines.
  - Spooler integration is handled across `BarTend.exe`, `Seagull.BarTender.Print.dll`, and `winspool.drv`.
  - System and licensing services are provided by `BtSystem.Client.dll`, `Seagull.License.dll`, and `Seagull.Services.Licensing.dll`.
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
  - Report 15 discussed Ghidra absence as a tooling mitigation, but in some sections implied deep function analysis on non-existent modules.
- **Discrepancy / Problem Identified:**
  - Unclear classification of whether function-level decompilation had occurred.
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
  - "Avoid Twip Inaccuracies: BarTender's use of integer twips leads to rounding errors when mapping to metric mm or high-DPI thermal dots. LabelForge solves this with double-precision canonical millimeters."
- **Discrepancy / Problem Identified:**
  - Twips (1/1440 inch = 17.638 µm) are not "inherently inaccurate"; they are standard integer GDI units with fixed quantization.
- **Corrected Claim:**
  - Twips operate on integer discretization (±8.8 µm error). At 203 DPI, 1 thermal dot corresponds to ~7.0936 twips, which requires rounding when mapping to integer thermal head grids.
  - LabelForge's use of IEEE-754 double-precision canonical millimeters (`Length`) provides $< 1\text{ picometer}$ resolution, eliminates cumulative rounding drift across rotations and affine transformations, and matches international metric label die standards.
- **Verification Evidence:**
  - Mathematical analysis of coordinate systems and `LabelForge.Core.Geometry.Length`.
- **Affected Documents Updated:**
  - `reports/15_PHASE1_NATIVE_BINARY_ANALYSIS.md`
  - `reports/20_PHASE1_1_EVIDENCE_RECONCILIATION.md`

---

## 3. Summary of Changes

| Document | Type of Modification | Primary Reconciliation Outcome |
| :--- | :--- | :--- |
| `reports/11_PHASE1_TARGET_IDENTITY.md` | Overwrite / Correction | Reconciled hashes, entry point, section table (`.nep`), Authenticode offset/size |
| `reports/12_PHASE1_APPLICATION_STRUCTURE.md` | Overwrite / Correction | Reconciled 589 items (555 files, 34 dirs, 461 PE binaries), eliminated phantom DLLs |
| `reports/13_PHASE1_DEPENDENCY_ANALYSIS.md` | Overwrite / Correction | Reconciled 48 direct imports, 17 delay-load imports, replaced phantom DLLs |
| `reports/15_PHASE1_NATIVE_BINARY_ANALYSIS.md` | Overwrite / Correction | Marked Ghidra `NOT_PERFORMED`, documented real barcode plugins, mathematical twip analysis |
| `reports/16_PHASE1_RESOURCE_ANALYSIS.md` | Overwrite / Correction | Corrected `.rsrc` bounds, reinforced strict clean-room copyright boundary on 83 CHM assets |
| `reports/18_PHASE1_FEATURE_TRACEABILITY.md` | Overwrite / Correction | Replaced phantom references with verified executable core and modular plugins |
| `reports/19_PHASE1_REVERSE_ENGINEERING_SUMMARY.md` | In-place Edit | Updated hashes, inventory counts, eliminated phantom references |
| `reports/20_PHASE1_1_EVIDENCE_RECONCILIATION.md` | New Deliverable | 20-section authoritative reconciliation master report |
| `reports/21_PHASE1_1_CORRECTION_LOG.md` | New Deliverable | Exhaustive itemized audit and correction register |
