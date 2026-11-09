# 09. Build Readiness Report: Independent Label Designer

## 1. Executive Summary
This report evaluates the engineering readiness, development tooling, project scaffolding, NuGet dependencies, legal boundaries, and phased milestone schedule required to construct the independent clean-room label designer application.

---

## 2. Engineering Prerequisites & Tooling

### 2.1 Developer Environment Requirements
* **Operating System:** Windows 10 (Build 19041+) or Windows 11 (64-bit).
* **SDK:** .NET 8.0 SDK (LTS) or .NET 9.0 SDK.
* **IDE / Tooling:**
  * Microsoft Visual Studio 2022 (Community / Professional / Enterprise) with ".NET desktop development" workload, OR
  * Visual Studio Code with the official "C# Dev Kit" extension.
* **Source Control:** Git 2.40+.

---

## 3. Recommended Solution & Project Hierarchy

The project will be scaffolded in `E:\ReverseEngineering\bartender-investigation\replacement\` as `OpenLabel.sln`:

```
OpenLabel/
 │
 ├── OpenLabel.sln
 ├── Directory.Build.props            (Shared compiler flags, Nullable enabled)
 ├── README.md
 │
 ├── src/
 │    ├── OpenLabel.Core/             (Class Library - net8.0)
 │    │    ├── Models/                (LabelDocument, PageSetup, Layer, CanvasObject)
 │    │    ├── Objects/               (TextObject, BarcodeObject, ShapeObject, PictureObject)
 │    │    ├── DataSources/           (DataSource, Embedded, Counter, TimeStamp, DbField)
 │    │    ├── Transforms/            (PrefixSuffixTransform, TruncateTransform, RegexTransform)
 │    │    └── Serialization/         (JsonDocumentSerializer, XmlDocumentSerializer)
 │    │
 │    ├── OpenLabel.Rendering/        (Class Library - net8.0-windows)
 │    │    ├── Abstractions/          (IRenderer, IBarcodeRenderer, ICanvasSurface)
 │    │    ├── Barcodes/              (ZXingBarcodeRenderer, BarcodeOptions)
 │    │    ├── Wpf/                   (WpfCanvasRenderer, DrawingVisualFactory)
 │    │    └── Skia/                  (SkiaRasterRenderer, SkiaPreviewGenerator)
 │    │
 │    ├── OpenLabel.DataSources/      (Class Library - net8.0)
 │    │    ├── Abstractions/          (IDataSourceReader, IRecordCursor)
 │    │    ├── Csv/                   (CsvDataSourceReader using CsvHelper)
 │    │    └── Relational/            (SqliteDataSourceReader, SqlServerReader)
 │    │
 │    ├── OpenLabel.Printing/         (Class Library - net8.0-windows)
 │    │    ├── Abstractions/          (IPrintEngine, IThermalCommandGenerator)
 │    │    ├── Spooler/               (WindowsSpoolerEngine, XpsDocumentBuilder)
 │    │    ├── Thermal/               (ZplCommandGenerator, RawPrinterHelper)
 │    │    └── Pdf/                   (QuestPdfExporter)
 │    │
 │    └── OpenLabel.App/              (WPF Application - net8.0-windows)
 │         ├── App.xaml / App.xaml.cs (Dependency Injection Host, ServiceProvider)
 │         ├── ViewModels/            (MainViewModel, CanvasViewModel, PropertiesViewModel)
 │         ├── Views/                 (MainWindow, CanvasView, PageSetupDialog, PrintDialog)
 │         ├── Controls/              (RulerControl, SelectionAdorner, ZoomBorder)
 │         └── Resources/             (Icons, Themes, Styles)
 │
 └── tests/
      ├── OpenLabel.Core.Tests/       (xUnit: Unit tests for DOM, serialization, math)
      ├── OpenLabel.Rendering.Tests/  (xUnit: Barcode verification, Skia raster tests)
      └── OpenLabel.Printing.Tests/   (xUnit: ZPL command validation, pagination tests)
```

---

## 4. NuGet Package Manifest

All components utilize mature, permissive open-source licenses (MIT, Apache 2.0, BSD):

| Project | NuGet Package ID | Version | License | Functional Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **OpenLabel.App** | `CommunityToolkit.Mvvm` | `8.2.2` | MIT | Source-generated MVVM, ObservableProperty, RelayCommand |
| **OpenLabel.App** | `Fluent.Ribbon` | `10.0.4` | MIT | Office-style modern Ribbon bar and Quick Access Toolbar |
| **OpenLabel.App** | `Dirkster.AvalonDock` | `4.72.1` | MIT | Multi-pane Visual Studio-style docking and floating windows |
| **OpenLabel.App** | `Microsoft.Extensions.DependencyInjection` | `8.0.0` | MIT | Inversion of Control (IoC) and dependency container |
| **OpenLabel.Rendering**| `ZXing.Net` | `0.16.9` | Apache 2.0 | Pure C# 1D/2D barcode generation engine |
| **OpenLabel.Rendering**| `SkiaSharp` | `2.88.8` | MIT | High-performance 2D vector & bitmap graphics engine |
| **OpenLabel.Rendering**| `SkiaSharp.Views.WPF`| `2.88.8` | MIT | High-speed Skia surface hosting within WPF elements |
| **OpenLabel.DataSources**| `CsvHelper` | `32.0.3` | Apache 2.0 | Robust delimited text (CSV/TSV) parsing and header mapping |
| **OpenLabel.DataSources**| `Microsoft.Data.Sqlite` | `8.0.4` | MIT | Embedded SQLite database support |
| **OpenLabel.Printing** | `QuestPDF` | `2024.3.0` | MIT / Quest | High-fidelity vector PDF generation |
| **OpenLabel.Printing** | `System.Printing` | `8.0.0` | MIT | WPF Windows PrintQueue and Spooler APIs |
| **Tests** | `xunit` / `FluentAssertions` | Latest | Apache/MIT | Unit test assertion and execution frameworks |

---

## 5. Clean-Room Legal & Architectural Safeguards

To maintain absolute legal and copyright integrity:
1. **Black-Box Specification Conformity:** Development must strictly follow the specifications established in Reports `01` through `08`.
2. **Zero Code Decompilation / Re-use:** No proprietary source code, IL disassembly, or internal strings from BarTender's binaries (`BarTend.exe`, `Seagull.*.dll`, `BarCode_*.dll`) shall be copied, disassembled into source code, or linked into the replacement project.
3. **No Commercial Asset Copying:** Icons, clip-art libraries, and proprietary sample `.btw` files must not be distributed. The replacement must use open-source glyphs (e.g., Lucide Icons, Segoe Fluent Icons, Material Symbols).
4. **Standard File Format:** Use the independent `.olb` (JSON) format as the primary native storage format.

---

## 6. Phased Implementation Roadmap

```
+-------------------------------------------------------------------------------+
|                        Implementation Roadmap                                 |
+-------------------------------------------------------------------------------+
| Milestone 1: Core DOM & Serialization Engine (Weeks 1-2)                      |
|  - Solution scaffolding, POCO data models, JSON serialization, unit tests.    |
+-------------------------------------------------------------------------------+
| Milestone 2: Vector Canvas & Interactive UI (Weeks 3-4)                       |
|  - WPF shell, Ribbon, AvalonDock, rulers, adorner handles, snap-to-grid.      |
+-------------------------------------------------------------------------------+
| Milestone 3: Barcode Engine & Object Rendering (Weeks 5-6)                    |
|  - ZXing.Net integration, 1D/2D symbologies, text formatting, shape drawing.  |
+-------------------------------------------------------------------------------+
| Milestone 4: Data Binding & Serialization Pipeline (Weeks 7-8)                |
|  - CSV reader, field treeview, counter serialization, dynamic canvas update.  |
+-------------------------------------------------------------------------------+
| Milestone 5: Printing, Preview & Thermal Output (Weeks 9-10)                  |
|  - Windows Spooler engine, Print Preview dialog, ZPL generator, PDF export.   |
+-------------------------------------------------------------------------------+
```

---

## 7. Readiness Assessment Conclusion
The reverse-engineering and architectural investigation phases are **100% complete**. All required technical models, spatial math, UI specifications, barcode algorithms, and output pathways have been identified, classified, and mapped to verified modern open-source equivalents. 

The project is **Ready for Build Execution** upon user approval of the reports and MVP scope.
