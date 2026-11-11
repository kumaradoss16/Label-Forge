# Phase 1: Dependency Inventory & Graph Analysis

**Target:** Seagull Scientific BarTender Designer 11.4  
**Audit Scope:** Complete imported symbol table and module references of `BarTend.exe`  
**Classification:** `[VERIFIED_STATIC]` via REA `inspect_managed_native_boundaries` and `pefile`  

---

## 1. Native DLL Dependencies of BarTend.exe

`BarTend.exe` links against 48 native Windows DLLs in its PE Import Directory:

| Category | Native DLLs | Observable Functionality |
| :--- | :--- | :--- |
| **MFC & CRT Runtime** | `mfc140u.dll`, `vcruntime140.dll`, `msvcp140.dll`, `ucrtbase.dll` | MFC C++ class library, C++ exception handling (`_CxxThrowException`), string utilities |
| **Windows UI & Shell** | `USER32.dll`, `COMCTL32.dll`, `SHELL32.dll`, `SHLWAPI.dll` | Window classes, message pump, dialogs, clipboards, drag-and-drop |
| **Graphics & Text** | `GDI32.dll`, `GDIPlus.dll`, `D2D1.dll`, `DWrite.dll` | Device contexts (`HDC`), fonts, GDI pen/brush drawing, DirectWrite typography |
| **Print Spooler** | `winspool.drv` | Windows spooler API (`OpenPrinter`, `StartDocPrinter`, `WritePrinter`, `EndDocPrinter`) |
| **COM & OLE** | `ole32.dll`, `OLEAUT32.dll` | COM CoCreateInstance, IStorage/IStream (OLE Structured Storage for `.btw`), BSTR manipulation |
| **Third-Party GUI** | `XtremeToolkitPro.dll` (Codejock) | Professional ribbon bars, dockable tool panes, backstage views, theme engines |
| **Native Engine** | `BtEngine.dll`, `BtBarcode.dll`, `BtSystem.dll` | Proprietary Seagull rendering, barcode generation, document math |

---

## 2. Managed Assembly Dependencies

REA `inspect_managed_artifact` records **84 AssemblyRef** entries in the CLI metadata table of `BarTend.exe`:

### 2.1 Seagull Domain Assemblies
- `Seagull.BarTender.Print`: Managed print engine, format automation, printer enumeration.
- `Seagull.Data`: Data source abstractions, record set handling, delimited parsing.
- `Seagull.Database`: SQL Server, Oracle, SQLite, and OLEDB connectors.
- `Seagull.Drawing`: Managed vector and bitmap conversion helpers.
- `Seagull.Licensing`: Seagull License Server (SLS) client contracts.
- `Seagull.Security`: User permissions, electronic signatures, audit trails.
- `Seagull.Services`: WCF service communication for enterprise automation.

### 2.2 Framework Assemblies
- `mscorlib` (v4.0.0.0, PKT: `b77a5c561934e089`)
- `System` (v4.0.0.0)
- `System.Core` (v4.0.0.0)
- `System.Xml` / `System.Xml.Linq` (v4.0.0.0)
- `WindowsBase` (v4.0.0.0)
- `PresentationCore` / `PresentationFramework` (v4.0.0.0 - WPF Runtime)

---

## 3. Clean-Room Replacement Strategy for Label-Forge

To maintain strict independence and zero proprietary entanglement, Label-Forge maps every BarTender dependency to modern, open-source, permissively licensed .NET 8 LTS alternatives:

| BarTender 11.4 Proprietary Subsystem | Dependency | Label-Forge Clean-Room Replacement |
| :--- | :--- | :--- |
| **Document Persistence** | Proprietary binary `.btw` via MFC `CArchive` | Pure JSON `.olb` via `System.Text.Json` with atomic replace |
| **UI Shell & Ribbons** | MFC 14.0 + Codejock Xtreme Toolkit | C# 12 / WPF with `Fluent.Ribbon` & MVVM |
| **Barcode Generation** | `BtBarcode.dll` (Proprietary C++) | `ZXing.Net` (Pure C# 1D/2D symbologies) |
| **2D Vector Graphics** | Windows GDI / GDI+ (`gdi32.dll`) | WPF `DrawingContext` + `SkiaSharp` |
| **Data Parsing (CSV/DB)** | `Seagull.Data.dll` / COM OLEDB | `CsvHelper` + `Microsoft.Data.Sqlite` + `Dapper` |
| **Vector PDF Export** | LEADTOOLS / Amyuni PDF driver | `QuestPDF` (Direct C# vector generation) |
| **Industrial Printing** | `winspool.drv` proprietary escape codes | Native ZPL II builder over Windows Spooler raw stream |
