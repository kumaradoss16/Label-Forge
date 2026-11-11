# Phase 1.1: Evidence Reconciliation & Authoritative Validation Report

**Target:** Seagull Scientific BarTender Designer 11.4  
**Primary Executable:** `BarTend.exe` (Build `11.4.238.365`)  
**Project:** LabelForge (Independent C# 12 / .NET 8 / WPF Clean-Room Desktop Application)  
**Milestone:** Phase 1.1 — Evidence Reconciliation & Validation  
**Date:** November 2026 (Updated Baseline)  
**Status:** Authoritative Baseline Verified  

---

## 1. Executive Summary & Purpose

Phase 1.1 establishes an internally consistent, mathematically verified, and reproducible evidence baseline for the reverse engineering of **BarTender Designer 11.4** before feature development continues in Label-Forge.

In the initial Phase 1 reports and preliminary drafts, several release-blocking evidence issues were identified:
- Conflicting `.data` section raw offsets between JSON and Markdown reports.
- Conflation of the COM descriptor directory (CLR header) RVA with the CLI metadata root RVA.
- Retention of extracted proprietary UI screenshot binaries in the repository.
- Validation scripts that only tested JSON parseability rather than cryptographic SHA-256 hashes of tracked evidence.
- Overstated functional claims extending beyond what static evidence strictly establishes.
- Incomplete classification of runtime evidence in the centralized claim register.

Phase 1.1 resolves every issue, replaces speculative claims with defensible facts from `D:\BarTender\BarTend.exe`, enforces strict clean-room copyright compliance, delivers an automated validation suite (`scripts/validate-phase1-evidence.py`), and formally signs off on the engineering baseline for Milestone M2.

---

## 2. Audit Scope & Methodology

The audit was conducted across three interconnected tiers:

1. **Byte-Level Binary Inspection:** Direct parsing of PE32+ optional headers, section headers, export address tables, import address tables, delay-load descriptors, Authenticode directories, COM descriptors, and CLI metadata tables from `D:\BarTender\BarTend.exe`.
2. **Filesystem Component Census:** Complete enumeration and structural classification of all 589 filesystem items in the vendor installation directory `D:\BarTender\`.
3. **Automated Verification Harness:** Creation and execution of `scripts/validate-phase1-evidence.py`, testing actual file SHA-256 digests against `validation_manifest.json`, PE bounds, claim register integrity, and report consistency with deterministic accounting (`PASS`, `FAIL`, `WARNING`, `NOT_CHECKED`).

---

## 3. Target Executable Identity & Baseline Ground Truth

Direct cryptographic and structural analysis of `D:\BarTender\BarTend.exe` establishes the authoritative baseline:

| Attribute | Verified Authoritative Value | Verification Mechanism | Status |
| :--- | :--- | :--- | :--- |
| **Filename** | `BarTend.exe` | Filesystem and PE VersionInfo | `[VERIFIED_STATIC]` |
| **Absolute Path** | `D:\BarTender\BarTend.exe` | Filesystem | `[VERIFIED_STATIC]` |
| **File Size** | `20,774,984` bytes (19.81 MB) | Filesystem Master | `[VERIFIED_STATIC]` |
| **MD5 Digest** | `7af37ab384391fcc03935a569d705aa0` | Cryptographic Hash (128-bit) | `[VERIFIED_STATIC]` |
| **SHA-1 Digest** | `7a57fefa26e99ddec6a46625a8cc17c5a87593aa` | Cryptographic Hash (160-bit) | `[VERIFIED_STATIC]` |
| **SHA-256 Digest** | `d3498925149b91c646351e91638906ca4455b2a4cd8db82775bb6860d67d8594` | Cryptographic Hash (256-bit) | `[VERIFIED_STATIC]` |
| **File Version** | `11.4.238.365` | `VS_FIXEDFILEINFO.dwFileVersion` | `[VERIFIED_STATIC]` |
| **Product Version** | `11.4.0.1` | `VS_FIXEDFILEINFO.dwProductVersion` | `[VERIFIED_STATIC]` |
| **Company Name** | `Seagull Scientific, LLC` | StringFileInfo StringTable | `[VERIFIED_STATIC]` |
| **Product Name** | `BarTender 11.4` | StringFileInfo StringTable | `[VERIFIED_STATIC]` |

---

## 4. PE Architecture & Section Layout Analysis

`BarTend.exe` is a 64-bit Windows GUI executable:
- **Machine Architecture:** `0x8664` (`IMAGE_FILE_MACHINE_AMD64`).
- **Optional Header Magic:** `0x20b` (`PE32+`).
- **Image Subsystem:** `2` (`IMAGE_SUBSYSTEM_WINDOWS_GUI`).
- **Image Base:** `0x140000000`.
- **Address of Entry Point:** `0x97d0fb` (pointing into executable code within `.text`).
- **Section Alignment:** `4096` bytes (`0x1000`).
- **File Alignment:** `512` bytes (`0x200`).
- **TimeDateStamp:** `0x6798a1b1` (Tue Jan 28 08:39:13 2025 UTC).
- **Number of Sections:** `7`.

### 4.1 Reconciled Section Table

| Section | Virtual Address | Virtual Size | Raw File Offset | Raw File Size | Characteristics | Subsystem Contents |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`.text`** | `0x1000` | `10,924,174` | `0x400` | `10,924,544` | `0x60000020` | Native x64 C++ Code & CLI Stubs |
| **`.nep`** | `0xa6d000` | `86,272` | `0xa6b600` | `86,528` | `0x60000020` | Native Entry Point Trampolines (C++/CLI) |
| **`.rdata`** | `0xa83000` | `6,758,812` | `0xa80800` | `6,758,912` | `0x40000040` | Read-only Data, RTTI, Imports, CLI Headers |
| **`.data`** | `0x10f6000` | `1,076,568` | `0x10f2a00` | `822,272` | `0xc0000040` | Read/Write Global & Static Variables |
| **`.pdata`** | `0x11fd000` | `462,588` | `0x11bb600` | `462,848` | `0x40000040` | x64 Structured Exception Handling (SEH) |
| **`.rsrc`** | `0x126e000` | `1,264,272` | `0x122c600` | `1,264,640` | `0x40000040` | Win32 Resources (Icons, Dialogs, Manifest) |
| **`.reloc`** | `0x13a3000` | `433,500` | `0x1361200` | `433,664` | `0x42000040` | Relocation Table for ASLR |

> [!NOTE]
> The section `.data` raw file offset is verified as **`0x10f2a00`**. Earlier draft references to `0x10f2c00` have been fully corrected across all JSON manifests and reports.

### 4.2 Authenticode Security Directory Physical Bounds
- **Directory Index:** 4 (`IMAGE_DIRECTORY_ENTRY_SECURITY`).
- **File Offset:** `0x13cb000` (`20,754,432` decimal).
- **Directory Size:** `20,552` bytes (`0x5048`).
- **Termination Offset:** $20,754,432 + 20,552 = 20,774,984$ bytes.
- **Evidentiary Limit:** Physical directory bounds confirm that the security directory terminates exactly at the file boundary (`20,774,984` bytes) with zero appended or truncated trailing bytes. Full cryptographic certificate chain validation is a distinct PKI verification step.

---

## 5. Component Inventory Reconciliation

Direct enumeration of `D:\BarTender\` proves:
- **Total Filesystem Items:** **589 items**.
- **Top-Level Directories:** **34 subdirectories** (23 language folders, `Templates`, `Help`, `Barcodes`, `SDK`, etc.).
- **Top-Level Files:** **555 files**.

### 5.1 Mutually Exclusive File Breakdown

$$\sum \text{Categories} = 24 + 433 + 4 + 29 + 40 + 10 + 7 + 3 + 2 + 3 = 555 \text{ files}$$

| Category | File Count | Extensions | Primary Description |
| :--- | :--- | :--- | :--- |
| **Executable Binaries** | `24` | `.exe` | Applications, background services, setup utilities |
| **Dynamic Link Libraries** | `433` | `.dll` | Business logic, UI components, barcode rasterizers |
| **ActiveX Controls** | `4` | `.ocx` | Codejock DockingPane, PropertyGrid, Controls, ReportControl |
| **Application Configs** | `29` | `.config` | XML .NET runtime and WCF endpoint configurations |
| **Data & Translation XMLs**| `40` | `.xml` | Language translations, printer command profiles |
| **XML Schemas** | `10` | `.xsd` | Label XML formats, command schemas, external info definitions |
| **Documentation PDFs** | `7` | `.pdf` | BarTender user guides, quick start manuals |
| **Initialization Settings**| `3` | `.ini` | Legacy bootstrap settings |
| **Win32 Manifests** | `2` | `.manifest` | Side-by-side assembly manifests |
| **Miscellaneous Assets** | `3` | `.dat`, `.ico`, `.stk`| Stock definitions, application icon, cache |
| **Total Files** | **555** | | **Strictly mutually exclusive, zero overlap** |

---

## 6. PE Binary Classification

Of the 555 files, exactly **461 files are PE binaries** (24 EXEs + 433 DLLs + 4 OCXs):

| Binary Classification | Architecture | Count | Subsystem Role | Representative Examples |
| :--- | :--- | :--- | :--- | :--- |
| **Managed IL-Only** | `MSIL` / `x64` | **332** | Pure .NET Common Intermediate Language | `AdminConsole.exe`, `Seagull.BarTender.Print.dll`, `Seagull.Data.dll` |
| **Mixed-Mode C++/CLI** | `x86_64` | **20** | Dual native x64 and CIL instructions | `BarTend.exe`, `ActivationWizard.exe`, `Leadtools.*`, `Seagull.Framework.Interop.dll` |
| **Native x64** | `x86_64` | **27** | Unmanaged 64-bit native machine code | `ToolkitPro1531vc142x64U.dll`, `BarCode_QRCode.dll`, `SciLexer64.dll`, 4 OCXs |
| **Native x86** | `x86` (32-bit) | **82** | Legacy 32-bit binaries & Win32 resource DLLs | `BtwConv.exe`, `PrintStation.exe`, 78 localized satellite DLLs (`Bt*.dll`, `AW*.dll`) |
| **Total PE Binaries** | | **461** | | **$\mathbf{332 + 20 + 27 + 82 = 461}$** |

---

## 7. Dependency Analysis & Direct/Delay Imports

### 7.1 Direct Static Imports (48 DLLs)
`BarTend.exe` binds directly at launch to 48 dynamic link libraries, classified into mutually exclusive, non-overlapping functional categories:
- **Windows OS Core & Subsystems (13):** `KERNEL32.dll`, `USER32.dll`, `GDI32.dll`, `ADVAPI32.dll`, `VERSION.dll`, `WINMM.dll`, `IMM32.dll`, `USP10.dll`, `USERENV.dll`, `RPCRT4.dll`, `SETUPAPI.dll`, `IPHLPAPI.DLL`, `NETAPI32.dll`.
- **Windows Printing Spooler (1):** `WINSPOOL.DRV` (direct spooler interfacing for printer handles, DC creation, and raw escapes).
- **COM, Security & Cryptography (8):** `ole32.dll`, `OLEAUT32.dll`, `COMCTL32.dll`, `COMDLG32.dll`, `CRYPT32.dll`, `WINTRUST.dll`, `Secur32.dll`, `imagehlp.dll`.
- **C++ Runtime & MFC (16):** `mfc140u.dll`, `MFCM140U.dll`, `MSVCP140.dll`, `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll`, plus 11 Universal CRT modules (`api-ms-win-crt-convert-l1-1-0.dll`, `api-ms-win-crt-environment-l1-1-0.dll`, `api-ms-win-crt-filesystem-l1-1-0.dll`, `api-ms-win-crt-heap-l1-1-0.dll`, `api-ms-win-crt-locale-l1-1-0.dll`, `api-ms-win-crt-math-l1-1-0.dll`, `api-ms-win-crt-runtime-l1-1-0.dll`, `api-ms-win-crt-stdio-l1-1-0.dll`, `api-ms-win-crt-string-l1-1-0.dll`, `api-ms-win-crt-time-l1-1-0.dll`, `api-ms-win-crt-utility-l1-1-0.dll`).
- **CLR Execution Engine Shim (1):** `mscoree.dll` (manages transition to CLR v4.0.30319).
- **Commercial GUI & Imaging Libraries (3):** `ToolkitPro1531vc142x64U.dll` (Codejock Xtreme Toolkit Pro), `SLImage.dll` (imaging engine), `dlsdk_shared.dll` (shared device SDK).
- **Modular Native Barcode Rasterizers (6):** `BarCode_Code93i.dll`, `BarCode_DotCode.dll`, `BarCode_GridMatrix.dll`, `BarCode_HanXin.dll`, `BarCode_iQRCode.dll`, `BarCode_rMQRCode.dll`.
- **Category Sum Verification:** $13 + 1 + 8 + 16 + 1 + 3 + 6 = 48\text{ DLLs}$ ($100\%$ accounted for exactly once).

### 7.2 Delay-Loaded Imports (17 DLLs)
- **Complex 2D Symbologies (7):** `BarCode_Aztec.dll`, `BarCode_Composite.dll`, `BarCode_DataMatrix.dll`, `BarCode_MaxiCode.dll`, `BarCode_QRCode.dll`, `BarCode_RoyalMail_FourStateMailmark_TypeC.dll`, `BarCode_RoyalMail_FourStateMailmark_TypeL.dll`.
- **Graphics & Shell (5):** `gdiplus.dll`, `MSIMG32.dll`, `SHELL32.dll`, `SHLWAPI.dll`, `dwmapi.dll`.
- **Drivers & Network (5):** `ODBC32.dll`, `WININET.dll`, `WTSAPI32.dll`, `wfapi64.dll`, `DriverUtilityLibrary.dll`.

---

## 8. Defensible Subsystem Boundaries (Narrowed Claims)

To maintain absolute scientific defensibility, claims regarding unmanaged components are strictly bounded by direct evidence:

1. **Absence of Standalone `BtEngine.dll`:**
   - *Evidence:* Filesystem scan confirms no file named `BtEngine.dll` exists in `D:\BarTender`.
   - *Defensible Scope:* Proves no separate DLL with that name exists in the target directory. The presence of MFC `CArchive` serialization symbols and geometry calculation imports inside `BarTend.exe` establishes that core layout and serialization primitives are hosted within `BarTend.exe`, though supporting assemblies or unmanaged helpers may contribute.
2. **Modular 2D Barcode Plugins:**
   - *Evidence:* `BarCode_QRCode.dll` and `BarCode_DataMatrix.dll` export C-style procedural APIs (`GenerateQRCode`, `GetQRCell`, `get_dm_cell`, `IDM_initialize`).
   - *Defensible Scope:* Proves exported procedural C APIs for matrix rasterization; does not claim full knowledge of internal dispatch mechanisms.
3. **Print Spooler Linkage (`winspool.drv`):**
   - *Evidence:* Static import of `winspool.drv` (`OpenPrinterW`, `StartDocPrinterW`, `WritePrinter`).
   - *Defensible Scope:* Proves static linkage to the Win32 spooler API; other printing pathways (managed APIs, third-party port monitors) operate alongside it.

---

## 9. Third-Party Commercial Library Audit

| Binary | Vendor | Version | Functional Role |
| :--- | :--- | :--- | :--- |
| `ToolkitPro1531vc142x64U.dll` | Codejock Software | 15.3.1 | Professional MFC Ribbon, docking panels, property grid (27,958 exported symbols) |
| `SciLexer64.dll` | Neil Hodgson / Scintilla | 3.x/4.x | VBScript and JavaScript syntax-highlighting editor |
| `ClearScriptV8.win-x64.dll` | Microsoft / Google | V8 | Embedded high-performance JavaScript execution engine |
| `WebView2Loader.dll` | Microsoft Corporation | Evergreen | Embedded Chromium web host for modern cloud integration |

---

## 10. .NET Managed Assembly & Metadata Audit

Analysis of the CLI metadata directory in `BarTend.exe`:
- **COM Descriptor Directory (Data Directory 14):** RVA `0xae9b90`, Size `72` bytes (`0x48`), File Offset `0xae7390` in `.rdata`.
- **`IMAGE_COR20_HEADER`:** Header Size 72 bytes, Runtime Version `2.5`, Flags `0x0` (`COMIMAGE_FLAGS_ILONLY = 0`).
- **CLI Metadata Root:** Located at RVA `0xc3ca00` (File Offset `0xc3a200`, Size `3,111,676` bytes).
- **Target Runtime:** `v4.0.30319` (.NET Framework 4.8.x).
- **Metadata Tables:** 2,421 TypeDefs, 1,034 TypeRefs, 17,547 MethodDefs, 84 AssemblyRefs, 662 ImplMap entries.
- **Entry Point Token:** `0x06002c63`.

---

## 11. Native/Managed Boundary & P/Invoke Audit

REA tool `inspect_managed_native_boundaries` extracted 662 native interop thunks:
- **`CArchive.WriteCount` & `CArchive.ReadCount`:** Implements schema-versioned serialization.
- **`CObList.AddTail` & `CObList.RemoveAll`:** Manages polymorphic document object lists.
- **`CWnd.CreateControl`, `ShowWindow`, `SetWindowPos`:** Embeds Win32 controls into canvas.
- **`SysAllocString`:** Marshals BSTR strings across COM/CIL boundaries.
- *Defensible Scope:* Establishes that MFC serialization and collection primitives are linked into the binary; does not claim full independent reverse engineering of the proprietary `.btw` binary schema.

---

## 12. Native Binary Investigation & Tooling Boundary

> [!IMPORTANT]
> **Status:** `[NOT_PERFORMED]` for Ghidra Native Decompilation.
> 
> A precompiled Ghidra distribution was not installed on the host environment (`GHIDRA_INSTALL_DIR` unset).
> No unmanaged function control-flow graphs or internal C++ function decompilations were executed.
> All native findings in LabelForge reports are derived strictly from PE headers, export tables, and P/Invoke boundaries.

---

## 13. Modular Barcode Architecture Analysis

Export analysis confirms that specialized 2D symbologies are dispatched to dedicated native C++ DLLs:
- **`BarCode_QRCode.dll` (229 KB):** Exports `GenerateQRCode`, `GetQRCell`, `SavePattern`.
- **`BarCode_DataMatrix.dll` (209 KB):** Exports `IDM_initialize`, `get_dm_cell`, `set_dm_cell`, etc. (20 exports).
- **`BarCode_Aztec.dll`, `BarCode_DotCode.dll`, `BarCode_MaxiCode.dll`, etc.**

---

## 14. Resource Inventory & Win32 Embedded Assets Audit

- **`.rsrc` Section:** Virtual Size `1,264,272` bytes, Raw Size `1,264,640` bytes at VA `0x126e000` (file offset `0x122c600`).
- **Embedded Dialogs:** Win32 dialog templates (`IDD_PAGESETUP`, `IDD_OBJ_PROPERTIES`).
- **DPI Awareness:** Embedded manifest specifies Per-Monitor V2 DPI awareness.

---

## 15. Copyright & Clean-Room Compliance Review for Extracted Assets

> [!CAUTION]
> **Strict Asset Removal & Legal Compliance:**
> All 40 proprietary graphic assets (PNGs, GIFs, JPEGs) previously stored in `screenshots/` have been **permanently deleted from repository version control**.
> 
> Purely textual observations, mathematical anchor rules, and structural canvas specifications are preserved in:
> [`screenshots/UI_OBSERVATIONS_REFERENCE.md`](file:///E:/ReverseEngineering/Label-Forge-clone/screenshots/UI_OBSERVATIONS_REFERENCE.md)
> 
> Label-Forge uses exclusively original vector iconography and native WPF MVVM controls.

---

## 16. Controlled Runtime Observations & Verification

Controlled runtime execution experiments are documented in `evidence/phase1/runtime_observations.json` and registered as explicit claims:

1. **Process Startup Lifecycle (`RT-01`, Claim `P1-023` `[VERIFIED_RUNTIME]`):**
   - Invocation: `BarTend.exe /Min=SystemTray`.
   - Behavior: Spawns x64 process, loads CRT and CLR v4.0.30319, blocks on modal activation prompt in non-interactive Session 22.
2. **Managed Print API License Enforcement (`RT-02`, Claim `P1-024` `[VERIFIED_RUNTIME]`):**
   - Invocation: Reflection instantiation of `Seagull.BarTender.Print.Engine.Start()`.
   - Result: Throws `Seagull.BarTender.Print.LicenseException: You must activate BarTender with a valid product key code`.
3. **COM Automation Registration & Unattended Limitation (`RT-03`, Claim `P1-025` `[VERIFIED_RUNTIME]`):**
   - Invocation: `New-Object -ComObject "BarTender.Application"`.
   - Result: Resolves registered CLSID `{D5856250-13D3-11D1-9D2B-00609787E3AE}` launching `BarTend.exe /Automation`.
   - **Crucial Distinction:** In an unactivated installation, execution halts on a modal licensing activation prompt, requiring interactive desktop acknowledgment. Therefore, successful COM registration and process launch do **not** constitute proof of unattended automated execution in an unactivated environment.

---

## 17. Printing Pipeline Integration

- Direct imports of `winspool.drv` (`OpenPrinterW`, `StartDocPrinterW`, `WritePrinter`).
- Dual-Path Printing Model:
  1. Standard GDI/EMF spooling for office printers.
  2. Direct thermal command streaming (`DATATYPE="RAW"`) for industrial barcode printers.

---

## 18. Coordinate Precision Mathematical Audit

- **BarTender Twip Storage:** 1 twip = 1/1440 inch = 0.01763889 mm (17.638 µm).
- **Quantization:** Integer twips introduce ±8.8 µm quantization error. At 203 DPI, 1 thermal dot = 7.0936 twips.
- **Label-Forge Advantage:** Double-precision millimeters (`Length` struct) provide continuous floating-point transformations without cumulative drift across DPIs.

---

## 19. Automated Validation Tooling & Test Results

The comprehensive validation suite (`scripts/validate-phase1-evidence.py` and `scripts/validate-phase1-evidence.ps1`) was executed:
- **Dynamic Derivation:** All expected target identity values derived from `canonical_target_identity.json` without hardcoded PE constants.
- **Evidence Manifest Checksums:** Verified actual SHA-256 digests and file sizes of all 15 tracked evidence files against `validation_manifest.json`.
- **Exact Direct-Import Partition:** Verified exact category partition where $\text{categorized\_modules} == \text{canonical\_direct\_imports}$ ($48$ DLLs) with zero internal duplicates, zero cross-category overlaps, zero missing modules, and zero unexpected modules.
- **Structured Evidence Traceability:** Verified that every verified claim defines valid, structured `evidence_refs` (RFC 6901 JSON Pointers, repository-relative file paths, runtime tests) that resolve to concrete evidence targets.
- **Claim-Specific Assertion Registry:** Replaced all unconditional static PASS fallbacks with dedicated assertion procedures for all 25 claims in the register.
- **Exact Status Accounting:** Enforced complete dictionary equality between actual claim status frequencies and declared counts across all recognized categories.
- **Recursive Prohibited-Image Audit:** Traversed the complete `screenshots/` directory tree case-insensitively across 14 image extensions, confirming zero proprietary image files remain.
- **Report Integrity:** Verified all 24 markdown reports (01 through 21) exist, have content, and contain no obsolete offsets.
- **Execution Provenance:** Automatically recorded audit execution metadata, environment specs, target executable SHA-256 (`d3498925149b91c646351e91638906ca4455b2a4cd8db82775bb6860d67d8594`), commit SHA, and accounting in `evidence/phase1/reconciliation/validation_provenance.json`.
- **Result:** Complete deterministic `PASS` across 136 automated checks with 0 failures, 0 warnings, and exit code `0`.

---

## 20. Final Engineering Conclusion & Phase 2 Gate Clearance

Phase 1.1 and Phase 1.1.2 have achieved:
1. Complete mathematical and structural reconciliation of PE headers and section layouts.
2. Elimination of proprietary assets from repository version control verified via recursive tree traversal.
3. Cryptographic SHA-256 evidence manifest verification.
4. Defensibly narrowed functional claims, verified runtime evidence, and structured RFC 6901 traceability.
5. Exact direct-import category partition and exact claim status accounting.
6. Deterministic validation tooling passing cleanly with zero failures and verified execution provenance.

**Phase 1.1 and Phase 1.1.2 are officially COMPLETE and VALIDATED. Label-Forge is fully cleared to proceed to Phase 2 (Milestone M2).**
