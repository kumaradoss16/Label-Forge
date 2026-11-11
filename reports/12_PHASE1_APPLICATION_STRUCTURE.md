# Phase 1: Application Structure & Component Discovery

**Target:** Seagull Scientific BarTender Designer 11.4  
**Audit Directory:** `D:\BarTender\`  
**Component Population:** 589 Filesystem Items (555 Files, 34 Subdirectories)  
**Classification:** `[VERIFIED_STATIC]` via Filesystem Audit and PE Header Analysis  
**Reconciled Baseline:** Phase 1.1 Authoritative Verification  

---

## 1. Authoritative Inventory Breakdown

During Phase 1.1 reconciliation, the root installation folder `D:\BarTender\` was audited to establish mutually exclusive, non-overlapping categories:

| Item Category | Item Count | Primary Extensions / Architecture | Subsystem Role |
| :--- | :--- | :--- | :--- |
| **Main Executable** | 1 | `BarTend.exe` (`x86_64` C++/CLI) | Primary Designer studio application |
| **Auxiliary Executables** | 23 | `.exe` (19 Managed x64, 2 Mixed x64, 2 Native x86) | Print Station, Admin Console, License Setup, Services |
| **Dynamic Link Libraries** | 433 | `.dll` (313 Managed IL, 18 Mixed CLI, 22 Native x64, 80 Native x86) | Core business logic, UI controls, barcode engines, satellites |
| **ActiveX Controls** | 4 | `.ocx` (`x86_64` Native) | Codejock DockingPane, PropertyGrid, ReportControl, Controls |
| **Configuration Files** | 29 | `.config` (XML .NET AppConfigs) | Runtime framework bindings, service endpoints |
| **Data & Formatting Schemas** | 50 | `.xml` (40 files), `.xsd` (10 files) | Label format schemas, translations, printer profiles |
| **Documentation & Guides** | 7 | `.pdf` (Portable Document Format) | User manuals, Quick Start guides |
| **Initialization Settings** | 3 | `.ini` (Text configuration) | Legacy setup parameters |
| **Application Manifests** | 2 | `.manifest` (Side-by-side XML) | Win32 activation contexts, DPI awareness |
| **Assets & Miscellaneous** | 3 | `.dat` (1), `.ico` (1), `.stk` (1) | Stock definitions, application icon, license cache |
| **Top-Level Subdirectories** | 34 | Language folders (23), Templates, Help, Barcodes, SDK | Localized resources, help documentation, templates |
| **Total Filesystem Items** | **589** | **555 Files + 34 Subdirectories** | **100% Mathematically Reconciled** |

### 1.1 PE Binary Classification (461 Total PE Binaries)

The 461 PE binaries (24 `.exe` + 433 `.dll` + 4 `.ocx`) classify into:

- **Managed IL-Only (.NET):** `332` binaries (19 EXE, 313 DLL). Pure Common Intermediate Language running on CLR v4.0.30319.
- **Mixed-Mode C++/CLI:** `20` binaries (2 EXE, 18 DLL). Contain both native x64 machine code and managed CIL. Includes `BarTend.exe`, `ActivationWizard.exe`, `DriverInteropLibrary.dll`, `Leadtools.*`, and `Seagull.Framework.Interop.dll`.
- **Native x64:** `27` binaries (1 EXE, 22 DLL, 4 OCX). Includes modular barcode plugins (`BarCode_QRCode.dll`, `BarCode_DataMatrix.dll`), Codejock GUI runtime (`ToolkitPro1531vc142x64U.dll`), and Scintilla editor (`SciLexer64.dll`).
- **Native x86:** `82` binaries (2 EXE, 80 DLL). Comprises 2 legacy executables (`BtwConv.exe`, `PrintStation.exe`) and 80 satellite Win32 resource DLLs (`Bt*.dll`, `AW*.dll`, `ToolkitPro.Resource*.dll`) containing localized dialogs and string tables.

---

## 2. Core Architectural Subsystems

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      BarTend.exe (C++/CLI Mixed-Mode)                       │
├─────────────────────────────────────┬───────────────────────────────────────┤
│       Native Subsystems (x64)       │       Managed Subsystems (.NET)       │
├─────────────────────────────────────┼───────────────────────────────────────┤
│ • MFC 14.0 Runtime (mfc140u.dll)    │ • PresentationFramework / WPF         │
│ • ToolkitPro1531vc142x64U.dll       │ • Seagull.BarTender.Print.dll         │
│ • Internal CArchive & Object Graph  │ • Seagull.Data.dll (CSV / Queries)    │
│ • BarCode_*.dll (Modular 2D Plugins)│ • Seagull.Services.Licensing.dll      │
│ • winspool.drv Spooler Integration  │ • Seagull.Wpf.Controls.dll            │
└─────────────────────────────────────┴───────────────────────────────────────┘
```

> [!IMPORTANT]
> **Reconciliation Finding:** The core label object model, twip geometry calculations, and `.btw` serialization reside directly inside `BarTend.exe` itself. BarTender does not break these out into separate DLLs such as `BtEngine.dll` or `BtPrint.dll`.

### 2.1 Presentation & UI Shell
- **Primary Modules:** `BarTend.exe`, `mfc140u.dll`, `ToolkitPro1531vc142x64U.dll`, `PresentationFramework.dll`.
- **Composition:** Codejock Xtreme Toolkit Pro v15.3.1 ribbon and docking panes hosting mixed Win32/MFC dialogs and WPF controls.
- **Evidence:** `BarTend.exe` directly imports MFC `CWnd` and Codejock decorated entry points, hosting WPF content via `HwndHost` and `FormsInterop`.

### 2.2 Document & Object Model Subsystem
- **Primary Module:** `BarTend.exe` (internal native C++ core).
- **Responsibilities:**
  - Maintains the in-memory object hierarchy (text, barcodes, shapes, pictures).
  - Serializes to/from proprietary `.btw` files via MFC `CArchive` binary streams in OLE Structured Storage containers.
  - Computes coordinates using internal integer twip units (1/1440 inch).

### 2.3 Barcode Processing Engine
- **Primary Modules:** `BarTend.exe` (1D linear barcodes) + Modular `BarCode_*.dll` plugins (2D symbologies).
- **Verified 2D Plugin Modules:**
  - `BarCode_QRCode.dll`: Generates QR Code symbologies (exports `GenerateQRCode`, `GetQRCell`, `SavePattern`).
  - `BarCode_DataMatrix.dll`: Generates ECC 200 Data Matrix (exports `get_dm_cell`, `IDM_initialize`, etc.).
  - `BarCode_Aztec.dll`, `BarCode_DotCode.dll`, `BarCode_MaxiCode.dll`, `BarCode_HanXin.dll`, `BarCode_GridMatrix.dll`.

### 2.4 Data Sources & Variable Evaluation
- **Primary Modules:** `Seagull.Data.dll`, `Seagull.Data.Core.dll`, `Seagull.Data.TextFileClient.dll`, `Seagull.Data.DataBuilder.dll`.
- **Responsibilities:**
  - Delimited text parsing (CSV, TSV), JSON databases, XML, and OLEDB/ODBC connectors.
  - Serialization counters, named data sources, and global data fields.
  - VBScript and JavaScript execution via `SciLexer64.dll` and `ClearScriptV8.win-x64.dll`.

### 2.5 Industrial Printing Pipeline
- **Primary Modules:** `BarTend.exe`, `Seagull.BarTender.Print.dll`, `Seagull.PrinterSetup.dll`, `winspool.drv`.
- **Responsibilities:**
  - Windows GDI/XPS print spooling via `OpenPrinter`, `StartDocPrinter`, and `WritePrinter`.
  - Direct thermal pass-through (ZPL, EPL, DPL) sending raw byte streams to Seagull printer drivers.
