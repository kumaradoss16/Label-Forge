# 03. Dependency Map Report: BarTender Designer 11.4

## 1. Overview
This report documents the exhaustive dependency tree of BarTender Designer 11.4 (`BarTend.exe`). It details the operating system prerequisites, native dynamic-link libraries, third-party commercial frameworks, managed .NET assemblies, background Windows services, and database backends.

---

## 2. Native Dynamic-Link Libraries (PE Imports)

### 2.1 Windows Core & System Subsystems (26 DLLs)
`BarTend.exe` links statically to standard Win32 / Win64 system APIs:

| Module | Import Count | Functional Role |
| :--- | :--- | :--- |
| `KERNEL32.dll` | 166 | Process & thread management, memory allocation, file I/O, sync primitives, module loading |
| `USER32.dll` | 180 | Windowing, message loop, mouse/keyboard input, menus, clipboard, dialog management |
| `GDI32.dll` | 134 | Graphics Device Interface: pens, brushes, fonts, device contexts, bitmap blitting, path rendering |
| `ADVAPI32.dll` | 61 | Registry manipulation, Windows service control, security descriptors, token access |
| `WINSPOOL.DRV` | 16 | Windows Print Spooler: `OpenPrinterW`, `StartDocPrinterW`, `WritePrinter`, `ClosePrinter` |
| `COMCTL32.dll` | 16 | Common controls v6.0 (TreeViews, ListViews, Toolbars, UpDown controls) |
| `ole32.dll` | 13 | COM initialization, OLE Structured Storage, CoCreateInstance |
| `OLEAUT32.dll` | 34 | COM Automation (BSTR handling, SafeArray, Variant manipulation) |
| `CRYPT32.dll` / `WINTRUST.dll` | 4 | Certificate validation, Authenticode verification, cryptographic hashing |
| `NETAPI32.dll` / `Secur32.dll` | 4 | Network user identification, domain validation, SSO authentication |
| `USP10.dll` / `IMM32.dll` | 8 | Uniscribe complex script processor, IME international character input |
| `SETUPAPI.dll` | 5 | Hardware device enumeration (printers, serial scale ports, USB devices) |

### 2.2 Microsoft Visual C++ Runtime & MFC (vc142 / VS 2019)
| Module | Import Count | Functional Role |
| :--- | :--- | :--- |
| `mfc140u.dll` | 1,331 | Microsoft Foundation Classes (x64 Unicode): document/view architecture, command routing |
| `MFCM140U.dll` | 1 | MFC Managed Extensions: C++/CLI interop bridge between native MFC and .NET CLR |
| `MSVCP140.dll` | 120 | Visual C++ Standard C++ Library (STL: iostreams, strings, vectors, maps) |
| `VCRUNTIME140.dll` | 27 | Visual C++ CRT base runtime (memcpy, memmove, exception handling) |
| `VCRUNTIME140_1.dll` | 1 | C++ exception handling for x64 (`__CxxFrameHandler4`) |
| `api-ms-win-crt-*.dll` | 167 | Universal CRT (UCRT) modules: heap, math, string, time, stdio, locale |

### 2.3 Commercial Native UI Framework: Codejock Xtreme Toolkit Pro
* **Module:** `ToolkitPro1531vc142x64U.dll`
* **Import Count:** 1,260 functions imported directly by `BarTend.exe`
* **Vendor:** Codejock Software
* **Version:** 15.3.1 (compiled with MSVC 14.2 x64 Unicode)
* **Purpose:** Provides the visual shell:
  * `CXTPRibbonBar` & `CXTPRibbonTab`: Office-style ribbon tabs and quick access toolbars.
  * `CXTPDockingPaneManager`: Multi-panel docking, floating, pinning, and autohide panes.
  * `CXTPPropertyGrid`: Structured property inspector for label and object formatting.
  * `CXTPCommandBars`: Context menus, keyboard accelerators, and customizable toolbars.
  * International satellite resource DLLs: 30 localized DLLs (`ToolkitPro.ResourceDe.dll`, `ToolkitPro.ResourceFr.dll`, `ToolkitPro.ResourceJa.dll`, etc.).

### 2.4 Commercial Native Imaging & PDF Engines
1. **LEADTOOLS Imaging Suite (v20+):**
   * Located in `target\LeadTools\` (over 80 native DLLs).
   * Key modules: `Ltfilx.dll`, `Ltkrnx.dll`, `Ltdisx.dll`, `Ltimgcorx.dll`, `Ltclrx.dll`, `Lfsvgx.dll`, `Lfpngx.dll`, `Lftifx.dll`.
   * Purpose: High-speed raster and vector image decoding, color conversion, image transformations, and support for over 100 graphic formats.
2. **Debenu / Foxit Quick PDF Library & PDFium:**
   * Located in `target\QuickPDF\`.
   * Key modules: `DebenuPDFLibrary64DLL1811.dll`, `DebenuPDFRenderer64DLL1811.dll`, `QPL1811PDFium64.dll`.
   * Purpose: Direct PDF generation, vector PDF importing, and high-fidelity PDF rasterization via Google PDFium.

### 2.5 Native Barcode Engines
Modular native DLLs implementing standard barcode algorithms:
* `BarCode_Aztec.dll`
* `BarCode_Code93i.dll`
* `BarCode_Composite.dll`
* `BarCode_DataMatrix.dll`
* `BarCode_DotCode.dll`
* `BarCode_GridMatrix.dll`
* `BarCode_HanXin.dll`
* `BarCode_QRCode.dll`, `BarCode_iQRCode.dll`, `BarCode_rMQRCode.dll`
* `BarCode_MaxiCode.dll`
* `BarCode_RoyalMail_FourStateMailmark_TypeC.dll` & `TypeL.dll`
* `usps4cb.dll`
* `dlsdk_shared.dll`

---

## 3. Managed .NET Framework Dependencies

### 3.1 Target Framework
* **CLR Version:** .NET Framework 4.8 (`v4.0.30319`)
* **CLR Bridge:** `mscoree.dll` (via `_CorExeMain`)

### 3.2 Microsoft .NET Framework Assemblies
* `mscorlib.dll` (4.0.0.0)
* `PresentationCore.dll` (4.0.0.0) — WPF core composition engine
* `PresentationFramework.dll` (4.0.0.0) — WPF control hierarchy and XAML parser
* `WindowsBase.dll` (4.0.0.0) — WPF dependency properties and threading
* `System.Xaml.dll` (4.0.0.0) — XAML schema reader and object writer
* `System.Windows.Forms.dll` (4.0.0.0) — Legacy dialogs and forms integration
* `System.Drawing.dll` (4.0.0.0) — GDI+ image helpers and printer metrics
* `System.ServiceModel.dll` (4.0.0.0) — WCF client communication with local services
* `System.Data.dll` (4.0.0.0) — ADO.NET database connectivity
* `System.Runtime.Remoting.dll` (4.0.0.0) — Cross-process IPC channels

### 3.3 Third-Party Managed Libraries
| Assembly | Version | Vendor | Architectural Purpose |
| :--- | :--- | :--- | :--- |
| `DevExpress.XtraEditors.v19.1.dll` | 19.1.4.0 | Developer Express | Advanced UI input controls, tree views, and editors |
| `DevExpress.XtraGrid.v19.1.dll` | 19.1.4.0 | Developer Express | High-performance grid for database record browsing |
| `DevExpress.XtraRichEdit.v19.1.dll` | 19.1.4.0 | Developer Express | Embedded RTF formatting and styled text editor |
| `Xceed.Wpf.Toolkit.dll` | 3.x | Xceed Software | ColorPicker, numeric spinners, and WPF dialog adorners |
| `Caliburn.Micro.dll` | 1.5.2.0 | Open Source | MVVM framework (View-ViewModel resolution, action message binding) |
| `Ionic.Zip.dll` | 1.9.1.1006 | DotNetZip | Zip compression for document archiving and template packages |
| `Accord.Video.DirectShow.dll` | 3.8.0 | Accord.NET | USB camera capture for live photo badge printing |
| `YamlDotNet.dll` | 11.x | Open Source | Parsing YAML integration workflow definitions |
| `Newtonsoft.Json.dll` | 13.x | James Newton-King | JSON serialization for database connectors and REST clients |
| `WebView2Loader.dll` | 1.0.x | Microsoft | Chromium-based web browser integration for cloud sign-in |

### 3.4 Seagull Scientific Managed Assemblies (PublicKeyToken: `109ff779a1b4cbc7`)
`BarTend.exe` links to over 80 internal Seagull assemblies. The primary architectural modules include:
* `Seagull.BarTender.Print.dll`: Official .NET Print Engine API (Engine, LabelFormatDocument, PrintSetup).
* `Seagull.Framework.dll`: Core infrastructure, messaging bus, logging, and error handling.
* `Seagull.Framework.Interop.dll`: Native-to-managed marshalers and C++/CLI glue.
* `Seagull.Wpf.dll`, `Seagull.Wpf.Controls.dll`, `Seagull.Wpf.Mvvm.dll`: Seagull WPF MVVM controls and styles.
* `Seagull.Data.*.dll`: Database abstraction layer (Text/CSV, Excel, XML, JSON, ODBC, SAP IDoc).
* `Seagull.Editors.*.dll`: Property dialogs (Database, Metadata, RichText, Script Editor).
* `Seagull.PrintTicket.dll`: Windows PrintTicket configuration and DevMode mapping.
* `Seagull.Scales.*.dll`: Industrial scale IO (RS-232, TCP/IP scale communication).
* `Seagull.Services.*.dll`: WCF client contracts for Licensing, Security, and SystemDatabase.

---

## 4. Supporting Windows Services & Infrastructure

`BarTend.exe` relies on several background Windows services for full enterprise functionality:

```
+--------------------------------------------------------------+
|                         BarTend.exe                          |
+--------------------------------------------------------------+
        |                  |                    |
  (WCF NamedPipe)    (WCF net.tcp)        (WCF IPC)
        v                  v                    v
+------------------+ +------------------+ +--------------------+
| Licensing.Service| | BtSystem.Service | | PrintScheduler.Svc |
| (Port 5160 TCP)  | | (System DB WCF)  | | (Print Spool/Job)  |
+------------------+ +------------------+ +--------------------+
                            |
                     (ADO.NET / TDS)
                            v
             +------------------------------+
             | Microsoft SQL Server         |
             | Instance: MSSQL$BARTENDER    |
             | Database: BarTender          |
             +------------------------------+
```

1. **BarTender Licensing Service (`Licensing.Service.exe`):**
   * Manages printer license counts, edition verification, and network license leases.
2. **BarTender System Service (`BtSystem.Service.exe`):**
   * Coordinates logging to SQL Server, security role resolution, and Librarian file storage.
3. **BarTender Print Scheduler (`PrintScheduler.Service.exe`):**
   * High-throughput queuing engine for automated print integrations.
4. **Microsoft SQL Server Express (`MSSQL$BARTENDER`):**
   * Stores print history, reprint logs, document revisions, and electronic signatures.

---

## 5. Clean-Room Replacement Strategy: Dependency Mapping

To develop an independent Windows desktop application without proprietary licensing or legacy technical debt, every proprietary dependency is mapped to a modern, open-source or standard framework replacement:

| BarTender 11.4 Component | Target Dependency | Independent Clean-Room Alternative | Reason for Selection |
| :--- | :--- | :--- | :--- |
| **Shell & Windowing** | MFC 14.0 + Codejock ToolkitPro | **WPF (C# .NET 8 / 9)** | Modern, DPI-aware, hardware-accelerated, native MVVM support. |
| **MVVM Framework** | Caliburn.Micro 1.5.2 | **CommunityToolkit.Mvvm** | Official Microsoft-backed source-generator MVVM library; high speed, zero reflection. |
| **Docking / Ribbon** | Codejock CXTPRibbon / Docking | **Fluent.Ribbon + AvalonDock** | Production-proven open-source Ribbon and Visual Studio-style docking for WPF. |
| **Barcode Generation** | Proprietary native `BarCode_*.dll` | **ZXing.Net + SkiaSharp / BarcodeLib** | Open-source, supports all standard 1D/2D symbologies, pure managed code, zero C++ glue. |
| **Image Processing** | LEADTOOLS (80+ DLLs) | **SkiaSharp / ImageSharp** | Cross-platform, high performance, handles all modern raster/vector formats cleanly. |
| **PDF Engine** | Debenu QuickPDF / PDFium | **PDFiumCore / QuestPDF** | High-fidelity rendering via Google PDFium; procedural vector generation via QuestPDF. |
| **Database Connectors** | `Seagull.Data.*.dll` | **ADO.NET + Dapper + CsvHelper + System.Text.Json** | High-performance, lightweight, standard .NET data connectivity. |
| **Printing Pipeline** | GDI / `WINSPOOL.DRV` | **WPF `PrintQueue` + `XpsDocumentWriter` + Win32 Spooler** | Standard Windows printing with direct raw printer spooling (`RawPrinterHelper`) for ZPL/TSPL. |
| **Data Storage / Config**| Registry + SQL Server | **SQLite (EF Core / Dapper) + JSON Settings** | Zero server setup, portable, single-file embedded database. |
