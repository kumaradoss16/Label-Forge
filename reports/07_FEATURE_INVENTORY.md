# 07. Feature Inventory: BarTender Designer 11.4

## 1. Overview
This report provides an exhaustive, classified inventory of all functional capabilities, design tools, document features, data sources, and output options identified in BarTender Designer 11.4.

Each capability is categorized and assigned an empirical verification status (`[VERIFIED]`, `[PARTIALLY VERIFIED]`, `[INFERRED]`, or `[UNKNOWN]`) along with its clean-room implementation feasibility.

---

## 2. Shell & Workspace Features

| Feature ID | Feature Name | Description | Verification Status | Evidence Source | Clean-Room Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SHL-01** | Ribbon / Command Bar | Categorized command organization (File, Edit, View, Create, Arrange, Tools, Administer). | `[VERIFIED]` | `HID_MAIN_MENU1-9.htm`, `ToolkitPro1531vc142x64U.dll` | High (`Fluent.Ribbon`) |
| **SHL-02** | Multi-Panel Docking | Dockable, floating, auto-hiding toolbox panes (Data Sources, Components, Layers). | `[VERIFIED]` | `Toolbox_LP.htm`, `ToolkitPro1531vc142x64U.dll` | High (`AvalonDock`) |
| **SHL-03** | Dual Rulers (X & Y) | Precision rulers with sub-millimeter markings and real-time red hairline tracking guides. | `[VERIFIED]` | `proc_desktop_ruler.htm`, `screenshot_ruler.png` | High (WPF Custom Controls) |
| **SHL-04** | Dual View Tabs | Bottom tabs switching between `Template Design View` and `Data Entry Form View`. | `[VERIFIED]` | `HID_VIEW_PROMPT_DESIGN.htm` | High (WPF TabControl) |
| **SHL-05** | Real-Time Status Bar | Shows cursor coordinates, object size, active printer name, and dynamic zoom slider. | `[VERIFIED]` | Status bar strings in `BarTend.exe` resources | High (WPF StatusBar) |
| **SHL-06** | Interactive Zoom | Smooth zooming (25% to 800%), Zoom to 100%, Zoom to Fit Page. | `[VERIFIED]` | `Toolbar_View.htm` | High (WPF ScaleTransform) |
| **SHL-07** | Alignment Snapping | Snapping to grid dots/lines and dynamic alignment guides to adjacent object bounds. | `[VERIFIED]` | `proc_desktop_ruler.htm` | High (Vector Snap Engine) |

---

## 3. Document & Page Layout Features

| Feature ID | Feature Name | Description | Verification Status | Evidence Source | Clean-Room Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DOC-01** | Custom Dimensions | Arbitrary width and height definition in Inches, Millimeters, Centimeters, or Points. | `[VERIFIED]` | `HIDD_PAGESETUP.htm`, `XMLLabel_2.0.xsd` | High (`OpenLabel.Core`) |
| **DOC-02** | Predefined Stocks | Stock selector library containing commercial SKUs (Avery, Zebra, Brady, Uline). | `[VERIFIED]` | `HIDD_PAGESETUP.htm`, `target\*.stk` files | High (JSON Stock Catalog) |
| **DOC-03** | Multi-Label Sheets | Grid matrix configuration: Rows, Columns, Top/Bottom/Left/Right Margins, Gaps. | `[VERIFIED]` | `HIDD_PAGESETUP.htm`, `PageSetup.cs` | High (Pagination Math) |
| **DOC-04** | Label Contour Shapes | Rectangle, Rounded Rectangle (with adjustable corner radius), Ellipse / Circle. | `[VERIFIED]` | `HIDD_PAGESETUP.htm`, `Shape.cs` | High (WPF Vector Geometry) |
| **DOC-05** | Media Sensors | Gap (transmissive) vs. Black Mark (reflective) continuous vs. die-cut media handling. | `[VERIFIED]` | `HIDD_PAGESETUP.htm` | High (ZPL `^MN` command) |
| **DOC-06** | Multi-Template Duplex | Front and back label templates per document for duplex printing. | `[VERIFIED]` | `XMLLabel_2.0.xsd` (`PageTemplateType`) | High (Multi-template DOM) |
| **DOC-07** | Background Watermarks| Solid color fill, background template graphic, or non-printing design guide image. | `[VERIFIED]` | `HIDD_PAGESETUP.htm` | High (Canvas background brush) |

---

## 4. Design Objects & Styling Features

| Feature ID | Feature Name | Description | Verification Status | Evidence Source | Clean-Room Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OBJ-01** | Single-Line Text | Single-line text with system font styling (Family, Size, Bold, Italic, Color, Underline). | `[VERIFIED]` | `Objects_DataEntry_TextPropertiesDialog.htm` | High (WPF `FormattedText`) |
| **OBJ-02** | Multi-Line Wrapped | Paragraph text with automatic word wrapping and full justification options. | `[VERIFIED]` | `Seagull.Editors.RichText.dll` | High (WPF `TextBlock`) |
| **OBJ-03** | Arc / Circular Text | Text flowing along an adjustable circular curve or arc. | `[VERIFIED]` | `angle_text_horizontal.jpg`, `ArcAlignCenter.jpg` | High (WPF PathGeometry) |
| **OBJ-04** | 1D Barcodes | Code 128, Code 39, Interleaved 2 of 5, EAN-13, EAN-8, UPC-A, UPC-E, Codabar. | `[VERIFIED]` | `BarCode_Composite.dll`, `target\Barcodes\` | High (`ZXing.Net`) |
| **OBJ-05** | 2D Matrix Barcodes | QR Code, Micro QR, Data Matrix (ECC 200), Aztec, PDF417, MaxiCode. | `[VERIFIED]` | `BarCode_QRCode.dll`, `BarCode_DataMatrix.dll` | High (`ZXing.Net`) |
| **OBJ-06** | Postal Barcodes | USPS Intelligent Mail (4-State), Royal Mail Mailmark, KIX, Australia Post. | `[VERIFIED]` | `usps4cb.dll`, `BarCode_RoyalMail_*.dll` | High (`ZXing.Net` / Custom 4CB) |
| **OBJ-07** | Barcode Human Readable | Automatic human-readable character rendering (Below, Above, Embedded, or None). | `[VERIFIED]` | `Objects_BarcodePropertiesDialog.htm` | High (Managed Barcode Formatter)|
| **OBJ-08** | Vector Shapes | Rectangles, Rounded Rectangles, Ellipses, Lines, Polygons, Stars. | `[VERIFIED]` | `Toolbar_LineShape.htm` | High (WPF `Shape` primitives) |
| **OBJ-09** | Image Objects | Import of raster graphics (PNG, JPEG, BMP, TIFF) with aspect ratio lock. | `[VERIFIED]` | `LeadTools` DLLs, `Objects_DataEntry_Picture` | High (WPF `BitmapImage`) |
| **OBJ-10** | Table Grids | Multi-row, multi-column tabular grid with cell-level text/barcode binding. | `[VERIFIED]` | `Toolbar_Object.htm` | High (WPF `Grid` layout) |
| **OBJ-11** | RFID & Encoders | UHF Gen2 RFID tag encoding and Magnetic Stripe tracks 1/2/3. | `[VERIFIED]` | `Toolbar_Object.htm`, `Seagull.BarTender.Print` | Medium (ZPL `^RF` command) |

---

## 5. Object Manipulation Features

| Feature ID | Feature Name | Description | Verification Status | Evidence Source | Clean-Room Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MAN-01** | 8-Point Resize | Eight interactive resizing handles for corner and edge scaling. | `[VERIFIED]` | `proc_desktop_ruler.htm` | High (WPF Custom Adorners) |
| **MAN-02** | Rotation Handle | Circular rotation handle supporting continuous and 15°-constrained rotation. | `[VERIFIED]` | `Toolbar_Arrange.htm` | High (WPF `RotateTransform`) |
| **MAN-03** | Alignment Suite | Align Left, Center, Right, Top, Middle, Bottom relative to dominant selection. | `[VERIFIED]` | `HID_ARRANGE_GROUP.htm` | High (Vector Bounding Math) |
| **MAN-04** | Even Distribution | Equalize horizontal and vertical gaps between multiple selected objects. | `[VERIFIED]` | `HID_ARRANGE_GROUP.htm` | High (Geometric Math) |
| **MAN-05** | Object Grouping | Group (`Ctrl+G`) and Ungroup (`Ctrl+U`) treating objects as single rigid composite. | `[VERIFIED]` | `HID_ARRANGE_GROUP.htm` | High (`CompositeObject` Model) |
| **MAN-06** | Z-Order Management | Bring to Front, Send to Back, Bring Forward, Send Backward. | `[VERIFIED]` | `HID_ARRANGE_MOVE_TO_FRONT.htm` | High (ObservableCollection order) |
| **MAN-07** | Duplicate & Nudge | Duplicate (`Ctrl+D`), Arrow key nudge (1px), Shift+Arrow key nudge (10px). | `[VERIFIED]` | `HID_MAIN_MENU2.htm` | High (WPF InputBindings) |
| **MAN-08** | Multi-Level Undo | 100-level atomic undo/redo command stack (`Ctrl+Z`, `Ctrl+Y`). | `[VERIFIED]` | `HID_EDIT_UNDO.htm` | High (Command Pattern Stack) |

---

## 6. Data Integration & Serialization Features

| Feature ID | Feature Name | Description | Verification Status | Evidence Source | Clean-Room Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DAT-01** | Embedded Data | Static literal values stored directly in template substrings. | `[VERIFIED]` | `XMLLabel_2.0.xsd` | High (Literal String Model) |
| **DAT-02** | Delimited Text (CSV) | Connects to CSV, TSV, and custom-delimited text files with header detection. | `[VERIFIED]` | `Seagull.Data.TextFileClient.dll` | High (`CsvHelper`) |
| **DAT-03** | Relational Database | ODBC / OLEDB / SQL Server / Oracle / SQLite connection and query builder. | `[VERIFIED]` | `Seagull.Data.dll`, `Seagull.Editors.Database`| High (`Dapper` / ADO.NET) |
| **DAT-04** | JSON & XML Clients | Direct data binding to hierarchical JSON arrays and XML XPath nodes. | `[VERIFIED]` | `Seagull.Data.JsonDatabaseClient.dll` | High (`System.Text.Json` / `XDoc`)|
| **DAT-05** | Serialization Counter | Auto-incrementing/decrementing numeric/alphanumeric counters with zero padding. | `[VERIFIED]` | `XMLLabel_2.0.xsd`, `PrintSetup.cs` | High (`SerializationCounter`) |
| **DAT-06** | Clock / TimeStamp | Real-time system date and time evaluation with format strings. | `[VERIFIED]` | `XMLLabel_2.0.xsd` | High (`DateTime.ToString`) |
| **DAT-07** | Substring Concatenation| Merging multiple data sources (static prefix + counter + DB field) into one object. | `[VERIFIED]` | `XMLLabel_2.0.xsd` | High (Composite Substring Model) |
| **DAT-08** | Data Transforms | Casing, character masks, truncation, regex search and replace. | `[VERIFIED]` | `XMLLabel_2.0.xsd`, `Data_Source_DataType` | High (Regex & String Filters) |
| **DAT-09** | VBScript Scripting | In-line VBScript event scripts modifying substring values. | `[VERIFIED]` | `Seagull.Editors.Script.dll` | Medium (C# Scripting / Roslyn) |

---

## 7. Output & Printing Features

| Feature ID | Feature Name | Description | Verification Status | Evidence Source | Clean-Room Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PRN-01** | Windows Spooler Print| High-DPI GDI/XPS print output to any standard Windows printer driver. | `[VERIFIED]` | `WINSPOOL.DRV`, `Seagull.BarTender.Print` | High (`System.Printing`) |
| **PRN-02** | Multi-Page Preview | Interactive WYSIWYG print preview window with record stepper and zoom. | `[VERIFIED]` | `HID_FILE_PRINTPREVIEW.htm`, SDK sample | High (WPF `PrintPreviewWindow`) |
| **PRN-03** | Direct Thermal (ZPL) | High-speed direct ASCII ZPL II command generation for Zebra industrial printers. | `[VERIFIED]` | `PrintSetup.cs`, Seagull driver architecture| High (`ZplCommandGenerator`) |
| **PRN-04** | Copies vs Serialization| Distinct control over identical duplicate copies vs. advancing serialized counters. | `[VERIFIED]` | `PrintSetup.cs` | High (Print Loop Orchestration) |
| **PRN-05** | Partial Sheet Reuse | Starting position picker for reusing partially peeled multi-label sheets. | `[VERIFIED]` | `PageSetup.cs` (`StartingPosition`) | High (Grid Cell Offset Math) |
| **PRN-06** | Vector PDF Export | Direct vector PDF export preserving TrueType text and 2D barcode vectors. | `[VERIFIED]` | `DebenuPDFLibrary64DLL1811.dll` | High (`QuestPDF` / `SkiaSharp`) |
| **PRN-07** | Raster Image Export | Exports rendered labels as PNG, JPEG, BMP, or TIFF at configurable DPI. | `[VERIFIED]` | `Export_Options_Dialog.htm` | High (`SkiaSharp` / WPF Bitmap) |
