# 04. Component Architecture Report: BarTender Designer 11.4

## 1. Architectural Overview

BarTender Designer 11.4 is organized as a multi-tier, component-based desktop authoring application. Despite its historical evolution across several decades, its internal decomposition exhibits a clean separation of concerns across presentation, document modeling, data evaluation, and physical output generation.

```
+-------------------------------------------------------------------------------+
|                             Presentation Layer                                |
|  +---------------------------+  +-------------------------------------------+ |
|  | Native MFC / Ribbon Shell |  | WPF MVVM Controls & Toolboxes             | |
|  | (Codejock Toolkit Pro)    |  | (Caliburn.Micro, DevExpress, Seagull.Wpf) | |
|  +---------------------------+  +-------------------------------------------+ |
+-------------------------------------------------------------------------------+
                                       |
+-------------------------------------------------------------------------------+
|                       Document & Object Engine (DOM)                          |
|  +-------------------------------------------------------------------------+  |
|  | Document Model (PageSetup, Stock, Templates, Layers, Objects)           |  |
|  | * Object Hierarchy: Barcode, Text, Shape, Picture, Table, RFID          |  |
|  | * Coordinate Systems & Layout Math (Inches, mm, pt, Transformations)    |  |
|  +-------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------+
           |                                               |
+------------------------------------+  +---------------------------------------+
|    Data Evaluation Subsystem       |  |      Rendering & Output Subsystem     |
|  +-------------------------------+ |  | +-----------------------------------+ |
|  | Data Sources Engine           | |  | | 2D Canvas Renderer (GDI+ / Direct2D)| |
|  | * Embedded / Screen Data      | |  | | Native Barcode Modules (BarCode_*.dll) |
|  | * Database Client (SQL/CSV/XML)| | | LeadTools Vector/Raster Pipeline     | |
|  | * Serialization & Counters    | |  +-----------------------------------+ |
|  | * Transforms & VBScript Eval  | |                      |                  |
|  +-------------------------------+ |                      v                  |
+------------------------------------+          +-------------------------------+
                                                |       Printing Engine         |
                                                | * Win32 Spooler (WINSPOOL.DRV)|
                                                | * Native Printer Code (ZPL)   |
                                                | * PDF / Image Export          |
                                                +-------------------------------+
```

---

## 2. Document Object Model (DOM) Hierarchy

The core logical hierarchy of a BarTender document (`.btw` / `XMLLabel_2.0.xsd`) is structured as a hierarchical composite tree:

```
LabelFormatDocument
 │
 ├── PageSetup
 │    ├── Stock (Manufacturer, Category, Predefined Dimensions)
 │    ├── PageDimensions (Width, Height, Orientation: Portrait / Landscape / 180)
 │    ├── LabelLayout (Rows, Columns, Margins, Horizontal/Vertical Gaps)
 │    └── ShapeDefinition (Rectangle, RoundedRectangle, Ellipse, Cutout Hole)
 │
 ├── DatabaseConnections (Collection)
 │    ├── TextFileConnection (CSV, TSV, Fixed-Width)
 │    ├── OdbcConnection (SQL Server, Oracle, MySQL, Postgres)
 │    ├── JsonConnection / XmlConnection
 │    └── EmbeddedDataTable (User-defined in-memory relational tables)
 │
 ├── NamedDataSources (Collection of shared global SubStrings)
 │
 └── Templates (Collection: multi-template and front/back support)
      │
      └── Layers (Collection: Z-index ordered layout layers)
           │
           └── CanvasObject (Abstract Base Object)
                │
                ├── Properties: Name, X, Y, Width, Height, Angle (0, 90, 180, 270),
                │               Locked, Visible, PrintWhenCondition
                │
                ├── BarcodeObject (Concrete)
                │    ├── Symbology (Code128, QR, DataMatrix, EAN13, etc.)
                │    ├── XDimension (Module width / bar pitch)
                │    ├── Ratio (e.g. 2.0 to 3.0 for 2-ratio linear barcodes)
                │    ├── QuietZones (Left, Right, Top, Bottom)
                │    ├── ErrorCorrectionLevel (QR: L/M/Q/H; DataMatrix: ECC200)
                │    └── HumanReadable
                │         ├── Visibility (None, Below, Above, Embedded)
                │         ├── Font, Size, Alignment, MarginFromBarcode
                │         └── CharacterFilter (Masking / Prefix / Suffix)
                │
                ├── TextObject (Concrete)
                │    ├── TextType (SingleLine, MultiLine, Wrapped, Arc/Circular)
                │    ├── FontSpecification (Family, Size, Bold, Italic, Strikethrough)
                │    ├── Alignment (Left, Center, Right, Justified)
                │    └── AutoFit (ShrinkToFit, BestFit, MinimumPointSize)
                │
                ├── ShapeObject (Concrete)
                │    ├── ShapeType (Line, Rectangle, RoundedRectangle, Ellipse, Polygon)
                │    ├── Stroke (Color, Width, Style: Solid, Dash, Dot)
                │    └── Fill (Color, Pattern, Transparency)
                │
                ├── PictureObject (Concrete)
                │    ├── SourceType (EmbeddedBytes, FilePath, DatabaseBlob, Camera)
                │    ├── SizingMode (OriginalSize, FitProportional, Stretch, Crop)
                │    └── ImageAdjustments (Brightness, Contrast, Monochrome Threshold)
                │
                └── SubStrings (Collection of dynamic data components per object)
                     ├── Position (1-based order in concatenation)
                     ├── ShareName (Named data source identifier)
                     ├── Type (Screen Data, Database Field, Date/Time, VBScript, Counter)
                     └── Transforms (Chain of post-processing filters)
                          ├── Prefix / Suffix
                          ├── Character Filter / Casing
                          ├── Truncation / Substring selection
                          ├── Search & Replace
                          └── Serialization / Auto-Increment rules
```

---

## 3. Coordinate System & Layout Mathematics

### 3.1 Units of Measurement
BarTender internally calculates all spatial coordinates using high-precision logical units before mapping to display or physical output:
* **Internal Representation:** Typically 1/1000th of an inch (mils) or 1/100th of a millimeter, stored as IEEE 754 double-precision floating-point numbers.
* **Supported User Units:**
  * Inches (`in`): $1\text{ in} = 25.4\text{ mm} = 72\text{ pt} = 96\text{ WPF px}$
  * Millimeters (`mm`): $1\text{ mm} = 0.03937\text{ in}$
  * Centimeters (`cm`): $1\text{ cm} = 10\text{ mm}$
  * Points (`pt`): $1\text{ pt} = 1/72\text{ in}$
  * Pixels (`px`): Dependent on target display DPI (standard 96 DPI) or printer DPI (203, 300, 600 DPI).

### 3.2 Transformation Matrices
Objects support affine 2D transformations:
$$\begin{bmatrix} x' \\ y' \\ 1 \end{bmatrix} = \begin{bmatrix} \cos\theta & -\sin\theta & t_x \\ \sin\theta & \cos\theta & t_y \\ 0 & 0 & 1 \end{bmatrix} \begin{bmatrix} x \\ y \\ 1 \end{bmatrix}$$
* **Rotation Angles:** Constrained to orthogonal increments ($0^\circ, 90^\circ, 180^\circ, 270^\circ$) for thermal printer hardware optimization, with arbitrary continuous rotation supported in GDI rendering mode.
* **Anchor Points:** Configurable object reference points (Top-Left, Top-Center, Top-Right, Center-Left, Center, Center-Right, Bottom-Left, Bottom-Center, Bottom-Right) ensuring predictable expansion when dynamic text grows.

---

## 4. Data Binding & Transformation Pipeline

The data evaluation subsystem operates as a multi-stage deterministic processing pipeline:

```
[ Data Source Input ]
 (Embedded / DB Record / Clock / System Field)
          │
          v
[ Raw Value Extracted ]
 (String or Binary)
          │
          v
[ Data Type Validation & Coercion ]
 (Text, Integer, Decimal, DateTime, Binary)
          │
          v
[ Transforms Pipeline ]
 ├── 1. Character Filter (e.g. numeric only, uppercase)
 ├── 2. Search & Replace (Regex or literal)
 ├── 3. Truncation (Keep leftmost/rightmost N characters)
 ├── 4. Prefix & Suffix addition
 └── 5. Serialization (Increment counter per label/copy)
          │
          v
[ VBScript Event Scripting ]
 (Optional custom logic modifying the Value)
          │
          v
[ Concatenation of SubStrings ]
 (Merged into final object data string)
          │
          v
[ Object Content Target ]
 (Dispatched to Barcode Encoder or Text Layout Engine)
```

---

## 5. Rendering & Output Subsystem

### 5.1 Dual-Target Rendering Architecture
1. **Interactive Screen Canvas:**
   * Handled by native MFC `CView` / GDI+ / Direct2D and WPF `DrawingVisual`.
   * Features interactive adorners: resize handles, rotation anchors, alignment snap-lines, margin boundaries, and ruler track indicators.
2. **Physical Print Pipeline:**
   * **Vector/Spooler Mode:** Converts objects directly into Windows GDI printing commands or WPF XPS FixedPage elements. Ideal for office desktop printers, laser printers, and PDF generation.
   * **Thermal Printer Template Mode:** Translates the layout directly into native thermal printer control commands (e.g., Zebra ZPL II `^XA...^XZ`). Static geometry becomes native printer lines/boxes (`^GB`), text uses native printer bitmap/smooth fonts (`^A0`), and barcodes use native hardware barcode commands (`^BC`, `^B3`, `^BQ`). Dynamic fields use template replacement variables (`^FN`).

---

## 6. Key Design Patterns Observed

* **Composite Pattern:** Used throughout the Document Object Model (`LabelFormatDocument` contains `Templates`, which contain `Layers`, which contain `CanvasObjects`, which contain `SubStrings`).
* **Strategy Pattern:** Used for barcode encoding (`IBarcodeEncoder` with distinct strategies for Code128, DataMatrix, QR, etc.) and data source retrieval (`IDataSourceReader` for Text, SQL, JSON, XML).
* **Observer / Event Pattern:** Data change notifications, print job status updates, and interactive canvas selection changes broadcast through event delegates.
* **Command Pattern:** Canvas operations (Move, Resize, Align, Delete, Add) are encapsulated as undoable/redoable command actions.
* **Bridge Pattern:** Decouples the abstract label document model from specific rendering backends (GDI display, Print Spooler, Native ZPL generation, PDF export).
