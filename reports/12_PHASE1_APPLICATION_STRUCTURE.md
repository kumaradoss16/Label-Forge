# Phase 1: Application Structure & Component Discovery

**Target:** Seagull Scientific BarTender Designer 11.4  
**Audit Directory:** `D:\BarTender\`  
**Component Population:** 589 Total Files (24 Executables, 433 Dynamic Link Libraries)  
**Classification:** `[VERIFIED_STATIC]` via REA and PE Header Inspection  

---

## 1. High-Level Inventory Breakdown

| Component Type | Count | Architecture | Description |
| :--- | :--- | :--- | :--- |
| **Main Application** | 1 | `x86_64` (Mixed C++/CLI) | `BarTend.exe` (Designer studio host) |
| **Auxiliary Executables** | 23 | `x86_64` (Managed & Native) | Print Station, Administration Console, License Setup, Batch Maker |
| **Managed .NET Assemblies** | 331 | `MSIL` / `x86_64` (.NET 4.8) | Core business logic, data connectors, UI view models, WCF communication |
| **Native C++ DLLs** | 102 | `x86_64` (Win32 Native) | MFC runtime, Codejock GUI controls, barcode rasterizers, GDI/DirectX renderers |

---

## 2. Core Architectural Subsystems

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BarTend.exe (C++/CLI Mixed-Mode)                     │
├───────────────────────────────────┬─────────────────────────────────────┤
│      Native Subsystems (x64)      │       Managed Subsystems (.NET)     │
├───────────────────────────────────┼─────────────────────────────────────┤
│ • MFC 14.0 Runtime (mfc140u.dll)  │ • PresentationFramework / WPF       │
│ • Codejock Xtreme Toolkit Pro     │ • Seagull.BarTender.Print.dll       │
│ • BtEngine.dll (Geometry/Core)    │ • Seagull.Data.dll (CSV / Queries)  │
│ • BtBarcode.dll (1D/2D Symbology) │ • Seagull.Services.dll (WCF)        │
│ • BtPrint.dll (Spooler / Raw PRN) │ • Seagull.Licensing.dll (SLS Check) │
└───────────────────────────────────┴─────────────────────────────────────┘
```

### 2.1 Presentation & UI Shell
- **Primary Modules:** `BarTend.exe`, `mfc140u.dll`, `XtremeToolkitPro.dll`, `PresentationFramework.dll`.
- **Composition:** Hybrid Win32/MFC ribbon with embedded WPF controls.
- **Evidence:** `BarTend.exe` imports `CWnd.CreateControl`, `CDialog.DoModal`, and hosts MFC docking panes (`XtremeCommandBars`).

### 2.2 Document & Object Model Subsystem
- **Primary Modules:** `BarTend.exe`, `BtEngine.dll`, `BtSystem.dll`.
- **Responsibilities:**
  - In-memory object graph maintaining label layout, text, barcodes, shapes, and pictures.
  - Serialization to/from proprietary `.btw` files using MFC `CArchive` binary streams within OLE Structured Storage containers.
  - Sub-millimeter coordinate transformations (twips to screen pixels to printer dots).

### 2.3 Barcode Processing Engine
- **Primary Modules:** `BtBarcode.dll`, `BtEngine.dll`.
- **Responsibilities:**
  - Mathematical symbology rasterization for linear 1D barcodes (Code 128, Code 39, Interleaved 2 of 5, EAN-13, UPC-A).
  - 2D matrix symbology generation (QR Code, Micro QR, Data Matrix, Aztec, PDF417).
  - Quiet zone enforcement, human-readable text placement, and checksum calculations.

### 2.4 Data Sources & Variable Evaluation
- **Primary Modules:** `Seagull.Data.dll`, `Seagull.Database.dll`, `BtData.dll`.
- **Responsibilities:**
  - Parsing delimited text (CSV, TSV), fixed-width files, and ODBC/OLEDB relational databases.
  - Real-time serialization counter updates (auto-increment, step intervals, rollover limits).
  - Embedded VBScript and JavaScript expression evaluation via COM ScriptControl.

### 2.5 Industrial Printing Pipeline
- **Primary Modules:** `Seagull.BarTender.Print.dll`, `BtPrint.dll`, `winspool.drv`.
- **Responsibilities:**
  - Dual-mode output: Universal Windows GDI/XPS print spooler versus raw byte streaming.
  - Seagull printer driver optimizations (direct thermal ZPL, EPL, DPL pass-through).
