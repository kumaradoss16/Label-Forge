# 07. Technical Architecture Report: Independent Clean-Room Replacement

## 1. Executive Summary & Design Principles

This report presents the comprehensive software architecture for an **independent, clean-room Windows desktop label design and printing application** with equivalent core capabilities to BarTender Designer.

### Fundamental Architectural Tenets
1. **Zero Proprietary Entanglement:** Completely independent of Seagull Scientific runtimes, internal DLLs, MFC C++/CLI wrappers, and commercial binary dependencies (Codejock, LEADTOOLS, QuickPDF).
2. **Modern .NET Ecosystem:** Built on C# 12 and .NET 8 LTS (or .NET 9), utilizing modern asynchronous programming, dependency injection, and source-generated MVVM.
3. **High-DPI & Per-Monitor DPI Awareness:** Full vector-based rendering ensuring crisp graphics across $100\%$, $125\%$, $150\%$, and $200\%$ display scalings.
4. **Dual-Path Output Architecture:** Unifies Windows GDI/XPS print spooling for standard office printers with direct raw thermal command streaming (ZPL II / TSPL) for industrial label printers.

---

## 2. Technology Stack Selection & Evaluation

```
+-------------------------------------------------------------------------------+
|                       Independent Technology Stack                             |
+-------------------------------------------------------------------------------+
| Presentation Layer  | WPF (.NET 8/9), Fluent.Ribbon, AvalonDock, Community.Mvvm|
+---------------------+---------------------------------------------------------+
| Document Model      | Pure POCO C# Models, System.Text.Json / XML Serializer  |
+---------------------+---------------------------------------------------------+
| Graphics & Canvas   | WPF DrawingContext (Interactive), SkiaSharp (Headless)  |
+---------------------+---------------------------------------------------------+
| Barcode Subsystem   | ZXing.Net, SkiaSharp.QrCode, BarcodeLib (1D/2D Pure C#) |
+---------------------+---------------------------------------------------------+
| Data Source Engine  | CsvHelper, ClosedXML, Dapper, Microsoft.Data.SqlClient  |
+---------------------+---------------------------------------------------------+
| Printing Pipeline   | System.Printing (WPF XPS), Win32 Spooler (Raw ZPL/TSPL) |
+---------------------+---------------------------------------------------------+
| PDF Export          | QuestPDF / SkiaSharp Vector PDF Pipeline                |
+---------------------+---------------------------------------------------------+
| Local Database      | SQLite (Microsoft.Data.Sqlite)                          |
+-------------------------------------------------------------------------------+
```

### 2.1 Language & Framework: C# 12 / .NET 8 LTS
* **Evaluation:** C# / .NET 8 provides native x64 performance, modern memory efficiency (`Span<T>`, `Memory<T>`), robust threading, and access to the rich Windows desktop ecosystem.

### 2.2 Presentation: WPF + Fluent.Ribbon + AvalonDock
* **Evaluation:** WPF provides native hardware acceleration, vector layout, XAML declarative styling, resolution independence, and mature printing integration via `XpsDocumentWriter`.
* **Ribbon:** `Fluent.Ribbon` delivers an Office-style modern ribbon interface matching BarTender's workflow without proprietary MFC/Codejock licenses.
* **Docking:** `Dirkster.AvalonDock` provides flexible multi-panel docking, pinning, floating windows, and workspace layout persistence.
* **MVVM:** `CommunityToolkit.Mvvm` provides compile-time source-generated observable properties, relay commands, and weak messaging bus with zero reflection overhead.

### 2.3 Vector & Raster Rendering: SkiaSharp & WPF Visuals
* **Canvas Display:** WPF `Canvas` with custom `FrameworkElement` using `DrawingContext` renders sub-millimeter geometry, interactive adorners, and guidelines at 60 FPS.
* **Headless High-DPI Rendering:** `SkiaSharp` (Google Skia C# binding) provides 203, 300, and 600 DPI bitmap generation for thermal preview rasterization and web/service integrations.

### 2.4 Barcode Engine: ZXing.Net & BarcodeLib
* **Evaluation:** Replaces all 12 proprietary `BarCode_*.dll` modules with 100% managed C# libraries.
* **Symbologies Covered:** Code 128, Code 39, Code 93, Interleaved 2 of 5, EAN-13, EAN-8, UPC-A, UPC-E, GS1-128, Data Matrix (ECC 200), QR Code, Micro QR, Aztec, PDF417, Codabar.

### 2.5 PDF Export: QuestPDF / SkiaSharp
* **Evaluation:** Eliminates the commercial Foxit/Debenu QuickPDF dependency. `QuestPDF` or `SkiaSharp.SKDocument.CreatePdf` generates crisp vector PDF documents with embedded TrueType font subsets, zero raster distortion, and minimal file sizes.

---

## 3. Subsystem Architecture & Component Breakdown

```
+-------------------------------------------------------------------------------+
|                            OpenLabel.App (WPF Shell)                          |
|  +- Views: MainWindow, RibbonView, CanvasView, PropertiesView, Toolboxes      |
|  +- ViewModels: MainViewModel, CanvasViewModel, ObjectPropertyViewModel       |
+-------------------------------------------------------------------------------+
                                      │
+-------------------------------------------------------------------------------+
|                     OpenLabel.Core (Domain & Document Engine)                 |
|  +- Models: LabelDocument, PageSetup, LabelStock, Layer, CanvasObject         |
|  +- Objects: TextObject, BarcodeObject, ShapeObject, PictureObject, Table     |
|  +- DataSources: DataSource, DatabaseField, CounterDataSource, TimeStamp     |
|  +- Transforms: TextTransformPipeline (Prefix, Suffix, Regex, Truncation)     |
|  +- Serialization: JsonDocumentSerializer (.olb / .json format)               |
+-------------------------------------------------------------------------------+
           │                                               │
+------------------------------------+  +---------------------------------------+
|        OpenLabel.DataSources       |  |          OpenLabel.Rendering          |
|  +- Readers: ICsvReader, ISqlReader|  |  +- IRenderer: WpfCanvasRenderer      |
|  +- Schema: ColumnDefinition, Row  |  |  +- IRenderer: SkiaRasterRenderer     |
|  +- Connectors: SQLite, Postgres   |  |  +- BarcodeEngine: ZXingBarcodeService|
+------------------------------------+  +---------------------------------------+
                                                           │
                                        +---------------------------------------+
                                        |          OpenLabel.Printing           |
                                        |  +- IPrintEngine: WindowsSpoolerEngine|
                                        |  +- IPrintEngine: RawThermalPrinter   |
                                        |  +- CommandGenerators: ZplGenerator   |
                                        |  +- Exporters: PdfExporter            |
                                        +---------------------------------------+
```

---

## 4. Independent Label Document Model Specification

### 4.1 Schema Definition (`OpenLabel` JSON Format)
The new application will use a clean, transparent, human-readable JSON document schema (`.olb` - Open Label):

```json
{
  "formatVersion": "1.0",
  "documentInfo": {
    "title": "Shipping Label",
    "author": "OpenLabel Designer",
    "units": "Inches"
  },
  "pageSetup": {
    "paperWidth": 4.0,
    "paperHeight": 6.0,
    "orientation": "Portrait",
    "labelsAcross": 1,
    "labelsDown": 1,
    "margins": { "top": 0.0, "left": 0.0, "right": 0.0, "bottom": 0.0 },
    "shape": "RoundedRectangle",
    "cornerRadius": 0.125
  },
  "dataSources": [
    {
      "id": "ds_tracking",
      "type": "DatabaseField",
      "connectionId": "conn_orders",
      "fieldName": "TrackingNumber"
    },
    {
      "id": "ds_serial",
      "type": "SerializationCounter",
      "startValue": 10001,
      "step": 1,
      "format": "D8"
    }
  ],
  "layers": [
    {
      "name": "Base Layer",
      "visible": true,
      "locked": false,
      "objects": [
        {
          "type": "Barcode",
          "name": "Barcode_Tracking",
          "x": 0.5,
          "y": 1.0,
          "width": 3.0,
          "height": 1.25,
          "angle": 0,
          "symbology": "Code128",
          "xDimensionMils": 15,
          "humanReadable": {
            "visible": true,
            "placement": "Below",
            "fontFamily": "Segoe UI",
            "fontSize": 10.0
          },
          "binding": { "dataSourceId": "ds_tracking" }
        },
        {
          "type": "Text",
          "name": "Txt_Serial",
          "x": 0.5,
          "y": 2.5,
          "width": 3.0,
          "height": 0.5,
          "text": "SN: ",
          "font": {
            "family": "Segoe UI",
            "size": 12.0,
            "bold": true
          },
          "binding": {
            "dataSourceId": "ds_serial",
            "prefix": "SN: "
          }
        }
      ]
    }
  ]
}
```

---

## 5. Printing Pipeline Design

### 5.1 Dual Output Architecture

```
                       [ Document + PrintJob Options ]
                                      │
                         ┌────────────┴────────────┐
                         │ Target Printer Type?    │
                         ▼                         ▼
             [ Standard Windows Driver ]   [ Thermal Direct (ZPL/TSPL) ]
                         │                         │
                         ▼                         ▼
                 WPF FixedDocument         ZPL Template Generator
             (System.Printing / XPS)       (^XA...^FO...^BC...^XZ)
                         │                         │
                         ▼                         ▼
                 Windows PrintQueue        Win32 RawPrinterHelper
               (Office / Laser / PDF)      (Zebra, TSC, Intermec)
```

1. **Windows Driver Spooler Pipeline:**
   * Converts the label layout into a WPF `FixedPage` containing vector paths, glyph runs, and images.
   * Dispatches via `PrintDialog.PrintDocument()` or `XpsDocumentWriter`.
   * Universally compatible with every printer that has a Windows driver installed.
2. **Direct Thermal Printer Pipeline:**
   * Generates direct ASCII command strings (e.g., Zebra Programming Language II):
     ```zpl
     ^XA
     ^PW812
     ^LL1218
     ^FO100,200^BY3,2.5,120^BCN,120,Y,N,N^FD12345678^FS
     ^FO100,360^A0N,30,30^FDSN: 10001^FS
     ^XZ
     ```
   * Emits raw byte arrays directly to the Windows Spooler via `OpenPrinter` / `WritePrinter` (`RawPrinterHelper`), bypassing graphics rasterization completely for blazing fast industrial line-speed printing.

---

## 6. Architectural Validation & Risk Mitigation

| Risk Area | BarTender Challenge | Independent Replacement Solution |
| :--- | :--- | :--- |
| **DPI Scaling** | BarTender 11.4 uses `<dpiAware>false</dpiAware>`, relying on legacy GDI bitmap stretch. | Pure vector WPF architecture ensures automatic, crystal-clear rendering across any display DPI (100%–300%). |
| **Licensing Hassles** | Strict network license server locks execution if port 5160 is blocked. | Independent architecture runs standalone with zero external daemon requirements. |
| **Thermal Printer Speed**| Generic GDI drivers print slowly due to large full-page bitmap transmission. | Direct ZPL / TSPL command builder prints instantly at native 203/300 DPI printer speeds. |
| **Code Bloat** | Target executable is 20MB mixed-mode C++/CLI + 80 MFC/Codejock DLLs. | Modular, trimming-friendly .NET 8 solution with compact self-contained deployment. |
