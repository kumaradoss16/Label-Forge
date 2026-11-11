# Phase 1: Feature-Oriented Reverse Engineering Traceability

**Target:** Seagull Scientific BarTender Designer 11.4  
**Project:** LabelForge (Independent C# / WPF Clean-Room Alternative)  
**Classification:** `[VERIFIED_STATIC]`, `[VERIFIED_RUNTIME]`, and `[VERIFIED_DOCUMENTATION]`  

---

## 1. Traceability Matrix

| Feature ID | BarTender 11.4 Feature | Target Subsystem / Modules | Reverse Engineering Evidence | Confidence | LabelForge Clean-Room Implementation | Milestone |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CANV-01** | Sub-millimeter Canvas & Rulers | Presentation / `BtEngine.dll` | Screen coordinates mapped to integer twips (1/1440 inch). Rulers in inch/mm. | `[VERIFIED_STATIC]` | `LabelForge.Core.Geometry.Length` struct (canonical mm double-precision storage, DPI independence). | **M1 (Done)** |
| **CANV-02** | 8-Point Adorner Manipulation | UI Shell / `BarTend.exe` | Mouse drag tracking via `ReleaseCapture` and `GetWindowRect`. 9-point anchor origins. | `[VERIFIED_DOCUMENTATION]` | WPF `Adorner` layer with 8 grab handles and rotation thumb. | **M2** |
| **DOC-01** | Label Page & Stock Dimensions | Document Engine / `BtEngine.dll` | MFC `CArchive` serialization of width, height, margins, orientation, and stock part numbers. | `[VERIFIED_STATIC]` | `PageSetup`, `LabelStock`, and `Thickness2D` domain models. | **M1 (Done)** |
| **DOC-02** | Multi-Layer Object Hierarchy | Document Engine / `BarTend.exe` | MFC `CObList` holding polymorphic `CDesignObject` pointers with z-indices and lock flags. | `[VERIFIED_STATIC]` | `Layer` containing polymorphic `CanvasObject` list with unique IDs and names. | **M1 (Done)** |
| **DOC-03** | Document Serialization (.olb) | Document Engine / `BarTend.exe` | Proprietary `.btw` binary using OLE Structured Storage compound documents. | `[VERIFIED_STATIC]` | Open JSON `.olb` with `$type` polymorphic discriminators, schema version validation, and atomic save. | **M1 (Done)** |
| **BAR-01** | 1D Linear Symbologies | `BtBarcode.dll` / `BtEngine.dll` | Code 128 (Sets A/B/C), Code 39, Interleaved 2 of 5, EAN-13, UPC-A, Codabar. | `[VERIFIED_STATIC]` | `BarcodeObject` domain model + `ZXing.Net` pure C# rendering engine. | **M3** |
| **BAR-02** | 2D Matrix Symbologies | `BtBarcode.dll` | QR Code, Micro QR, Data Matrix (ECC 200), PDF417, Aztec. Error correction levels (L, M, Q, H). | `[VERIFIED_STATIC]` | `BarcodeObject` matrix options + `ZXing.Net` matrix encoders. | **M3** |
| **BAR-03** | Human-Readable Text & Quiet Zones | `BtBarcode.dll` | Placement options (None, Below, Above, Embedded). Font styling and quiet zone margin enforcement. | `[VERIFIED_STATIC]` | `HumanReadableOptions` and `QuietZoneOptions` domain configuration. | **M1 (Done)** |
| **DATA-01** | Delimited Text / CSV Binding | `Seagull.Data.dll` | `TextReaderRecordSet` parsing CSV/TSV with header row field mapping. | `[VERIFIED_STATIC]` | `IDataSourceProvider` & `CsvHelper` implementation in `LabelForge.DataSources`. | **M4** |
| **DATA-02** | Serialization Counters | `Seagull.Data.dll` | Increment/decrement steps, zero-padding, rollover limits, and copy serialized counts. | `[VERIFIED_STATIC]` | Pure C# `SerializationCounterEngine` with integer and alphanumeric base support. | **M4** |
| **PRN-01** | Windows Spooler Printing | `BtPrint.dll` / `winspool.drv` | GDI `HDC` page rendering into EMF/XPS spooler streams with `DEVMODE` copies. | `[VERIFIED_STATIC]` | `IPrintEngine` + WPF `PrintDialog` / `XpsDocumentWriter`. | **M5** |
| **PRN-02** | Direct Industrial Thermal (ZPL) | `BtPrint.dll` / `winspool.drv` | Direct ASCII command emission (`^XA ... ^XZ`) via `WritePrinter` with `DATATYPE="RAW"`. | `[VERIFIED_STATIC]` | Pure C# `ZplCommandBuilder` streaming raw bytes over `RawPrinterHelper`. | **M5** |
| **EXP-01** | Vector PDF Export | LEADTOOLS / Amyuni PDF | Virtual printer driver outputting rasterized or vector PDF. | `[VERIFIED_STATIC]` | `QuestPDF` direct vector document generation. | **M5** |

---

## 2. Synthesis of Architectural Defensibility

Every feature identified in BarTender 11.4 has an established, clean-room technical path in LabelForge that completely avoids:
1. Proprietary DLL dependencies (`BtEngine.dll`, `BtBarcode.dll`, `BtPrint.dll`).
2. Legacy mixed-mode C++/CLI wrappers.
3. Proprietary OLE compound binary files (`.btw`).
4. Network license server gates (SLS).
