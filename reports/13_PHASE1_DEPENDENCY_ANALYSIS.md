# Phase 1: Dependency Analysis & External Linkages

**Target:** Seagull Scientific BarTender Designer 11.4 (`BarTend.exe`)  
**Scope:** Direct PE Imports, Delay-Loaded Modules, Managed References, Third-Party Binaries  
**Classification:** `[VERIFIED_STATIC]` via PE Import Tables and REA Analysis  
**Reconciled Baseline:** Phase 1.1 Authoritative Verification  

---

## 1. PE Import Hierarchy Overview

Static parsing of `BarTend.exe` reveals a multi-tier dependency architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        BarTend.exe Import Tiers                        │
├───────────────────────────────────┬────────────────────────────────────┤
│   Direct Static Imports (48 DLLs) │    Delay-Loaded Modules (17 DLLs)  │
├───────────────────────────────────┼────────────────────────────────────┤
│ • Win32 Subsystem (KERNEL32,      │ • Advanced Barcode Plugins         │
│   USER32, GDI32, ADVAPI32)        │   (BarCode_QRCode, DataMatrix)     │
│ • CRT & Runtime (VCRUNTIME140,    │ • Windows Graphics & Shell         │
│   MSVCP140, mscoree.dll)          │   (gdiplus.dll, MSIMG32, SHELL32)  │
│ • UI Runtime (mfc140u, MFCM140U,  │ • Networking & Security            │
│   ToolkitPro1531vc142x64U.dll)    │   (WININET, WTSAPI32, ODBC32)      │
│ • Spooler Subsystem (WINSPOOL.DRV)│ • Driver Utilities                 │
└───────────────────────────────────┴────────────────────────────────────┘
```

---

## 2. Direct PE Static Imports (48 DLLs)

The primary executable directly binds to 48 DLLs across seven mutually exclusive categories (mathematically reconciling $13 + 1 + 8 + 16 + 1 + 3 + 6 = 48$):

1. **Windows OS Core & Subsystems (13 DLLs):**
   `KERNEL32.dll`, `USER32.dll`, `GDI32.dll`, `ADVAPI32.dll`, `VERSION.dll`, `WINMM.dll`, `IMM32.dll`, `USP10.dll`, `USERENV.dll`, `RPCRT4.dll`, `SETUPAPI.dll`, `IPHLPAPI.DLL`, `NETAPI32.dll`.
2. **Windows Printing Spooler (1 DLL):**
   `WINSPOOL.DRV` (direct spooler access for device capabilities, DC creation, and raw escape streaming).
3. **COM, Security & Cryptography (8 DLLs):**
   `ole32.dll`, `OLEAUT32.dll`, `COMCTL32.dll`, `COMDLG32.dll`, `CRYPT32.dll`, `WINTRUST.dll`, `Secur32.dll`, `imagehlp.dll`.
4. **C++ CRT & MFC Runtime (16 DLLs):**
   `mfc140u.dll`, `MFCM140U.dll`, `MSVCP140.dll`, `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll`, plus 11 Universal CRT modules (`api-ms-win-crt-*`).
5. **CLR Execution Engine Shim (1 DLL):**
   `mscoree.dll` (manages transition between native x64 and CLR v4.0.30319 runtime).
6. **Commercial GUI & Imaging Libraries (3 DLLs):**
   `ToolkitPro1531vc142x64U.dll`, `SLImage.dll`, `dlsdk_shared.dll`.
7. **Modular Native Barcode Rasterizers (6 DLLs):**
   `BarCode_Code93i.dll`, `BarCode_DotCode.dll`, `BarCode_GridMatrix.dll`, `BarCode_HanXin.dll`, `BarCode_iQRCode.dll`, `BarCode_rMQRCode.dll`.

$$\text{Total Direct Static Imports} = 13 + 1 + 8 + 16 + 1 + 3 + 6 = 48\text{ DLLs}$$

---

## 3. Delay-Loaded Imports (17 DLLs)

To optimize startup time and avoid unnecessary footprint during idle launch, BarTender delay-loads 17 modules:

- **Complex 2D Barcode Rasterizers:** `BarCode_Aztec.dll`, `BarCode_Composite.dll`, `BarCode_DataMatrix.dll`, `BarCode_MaxiCode.dll`, `BarCode_QRCode.dll`, `BarCode_RoyalMail_FourStateMailmark_TypeC.dll`, `BarCode_RoyalMail_FourStateMailmark_TypeL.dll`.
- **GDI+ & Shell Interop:** `gdiplus.dll`, `MSIMG32.dll`, `SHELL32.dll`, `SHLWAPI.dll`, `dwmapi.dll`.
- **Connectivity & Drivers:** `ODBC32.dll`, `WININET.dll`, `WTSAPI32.dll`, `wfapi64.dll`, `DriverUtilityLibrary.dll`.

---

## 4. Third-Party Commercial Components

| Module | Vendor | Version | Functional Role |
| :--- | :--- | :--- | :--- |
| **`ToolkitPro1531vc142x64U.dll`** | Codejock Software | 15.3.1 | Professional MFC Ribbon, docking panels, property grid |
| **`SciLexer64.dll`** | Neil Hodgson / Scintilla | 3.x/4.x | VBScript and JavaScript syntax-highlighted editor |
| **`ClearScriptV8.win-x64.dll`** | Microsoft / Google | V8 | Embedded high-performance JavaScript execution engine |
| **`WebView2Loader.dll`** | Microsoft Corporation | Evergreen | Embedded Chromium web host for modern cloud integration |

---

## 5. Phantom Dependency Reconciliation

> [!WARNING]
> Prior drafts referenced hypothetical DLL names based on assumed modularity. Comprehensive filesystem auditing confirms that the following names **do not exist**:

| Hypothesized Reference | Actual Verified Module | Explanation |
| :--- | :--- | :--- |
| `BtEngine.dll` | `BarTend.exe` (Internal Native) | Core geometry and `.btw` serialization are compiled natively inside `BarTend.exe`. |
| `BtBarcode.dll` | `BarCode_*.dll` Plugins + `BarTend.exe` | Modular 2D symbologies are in separate plugins; 1D barcodes are rasterized in `BarTend.exe`. |
| `BtPrint.dll` | `BarTend.exe` + `Seagull.BarTender.Print.dll` | Spooler interactions are divided between `BarTend.exe` and managed print libraries. |
| `BtSystem.dll` | `BtSystem.Client.dll` + `Seagull.Framework.dll` | System infrastructure is handled by the managed `BtSystem.*` suite. |
| `BtLic.dll` | `Seagull.License.dll` + `Seagull.Services.Licensing.*` | Licensing operates via WCF/HTTP service communication. |
| `XtremeToolkitPro.dll` | `ToolkitPro1531vc142x64U.dll` | Codejock binary on disk has the explicit compiler/architecture naming scheme. |
