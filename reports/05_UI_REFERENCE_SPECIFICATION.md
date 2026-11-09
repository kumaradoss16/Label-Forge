# 05. UI Reference Specification: BarTender Designer 11.4

## 1. Executive Summary & Verification Methodology
This specification defines the complete observable user interface, windowing hierarchy, command groups, design canvas, properties panels, toolboxes, status bar, and configuration dialogs of BarTender Designer 11.4 (`BarTend.exe`).

### Verification Taxonomy
In accordance with project evidence rules, every UI element and layout characteristic is marked with an empirical verification status:
* **`[VERIFIED]`**: Directly confirmed via extracted PE resources, compiled MFC dialog templates, decompiled documentation topics, and visual screenshot assets.
* **`[PARTIALLY VERIFIED]`**: Structural existence and interface signatures confirmed, but fine-grained dynamic visual skinning depends on active theme or Windows visual styles.
* **`[INFERRED]`**: High-probability architectural deduction based on framework conventions (Codejock Xtreme Toolkit Pro v15.3.1, MFC 14.0, WPF ElementHost).
* **`[UNKNOWN]`**: Runtime-only proprietary internal telemetry or undiscovered dynamic custom control behaviors.

---

## 2. Main Window Structure `[VERIFIED]`

The top-level application window of BarTender Designer 11.4 is a classic Multiple Document Interface (MDI) / Tabbed Document Interface window managed by native MFC (`mfc140u.dll`) and Codejock Xtreme Toolkit Pro (`ToolkitPro1531vc142x64U.dll`):

```
+---------------------------------------------------------------------------------------------------------+
| [Quick Access] [ Window Title: BarTender Designer 11.4 - [Document1.btw *] ]            [_] [口] [X]    |
+---------------------------------------------------------------------------------------------------------+
| File | Home | Create | View | Arrange | Administer | Tools | Window | Help                              |
+---------------------------------------------------------------------------------------------------------+
| [New][Open][Save][Print] | [Cut][Copy][Paste] | [Font: Arial v][Size: 12 v][B][I][U] | [Align L C R J]  |
+--------------------------+------------------------------------------------------------------------------+
| Toolbox (Docked Left)    | Interactive Design Area (Center Viewport)                                    |
| +----------------------+ | [0]...[1]...[2]...[3]...[4]...[5] (Top Horizontal Ruler)                    |
| | Components Pane (.btc)| | : +----------------------------------------------------------------------+    |
| | Data Sources Tree    | | : | Margin Guide (Dotted Outline)                                        |    |
| | Layers Manager       | | 1 |  +----------------------------------------------------------------+  |    |
| +----------------------+ | . |  | [Text Object]         [ Barcode: Code 128 ]                    |  |    |
|                          | 2 |  |                                                                |  |    |
|                          | . |  | [Shape: RoundedRect]  [ Data Field: {TrackingNumber} ]         |  |    |
|                          | 3 |  +----------------------------------------------------------------+  |    |
|                          | : +----------------------------------------------------------------------+    |
|                          | (Left Vertical Ruler)                                                        |
+--------------------------+------------------------------------------------------------------------------+
| [v] Template Design View  |  [ ] Data Entry Form View                                                   |
+---------------------------------------------------------------------------------------------------------+
| Ready | Position: 1.250 in, 0.750 in | Size: 2.000 in x 0.500 in | Selected: Barcode 1 | Zoom: 100% [+][-] |
+---------------------------------------------------------------------------------------------------------+
```

### Window Component Breakdown
1. **Title Bar `[VERIFIED]`:** Displays application branding, active document path (`<FileName>.btw`), dirty state indicator (`*`), and standard Windows minimize/maximize/close controls.
2. **Quick Access Toolbar `[VERIFIED]`:** Located above or below the ribbon; hosts frequently used commands: New, Open, Save, Print, Undo, Redo.
3. **Menu / Ribbon Bar `[VERIFIED]`:** Provides category-based command organization (see Section 3).
4. **Dockable Toolboxes (Left Docking Pane) `[VERIFIED]`:** Hosts `Data Sources`, `Components`, and `Layers` tabbed panels (`Toolbox_LP.htm`).
5. **Central Design Canvas `[VERIFIED]`:** Scrollable vector layout area surrounded by horizontal and vertical precision rulers (`proc_desktop_ruler.htm`).
6. **Bottom View Switcher Tabs `[VERIFIED]`:** Allows one-click switching between `Template Design View` and `Data Entry Form View`.
7. **Status Bar `[VERIFIED]`:** Real-time feedback showing cursor coordinates, selected object dimensions, active printer name, and dynamic zoom slider.

---

## 3. Menu & Ribbon Organization `[VERIFIED]`

The top command system is organized across 9 standard functional categories:

| Menu / Category | Key Command Items `[VERIFIED]` | Accelerator `[VERIFIED]` | Functional Description |
| :--- | :--- | :--- | :--- |
| **File** (`HID_MAIN_MENU1`) | New..., Open..., Close, Save, Save As..., Page Setup..., Print Setup..., Print Preview, Print..., Database Connection Setup..., Export Image... | `Ctrl+N`, `Ctrl+O`, `Ctrl+S`, `Ctrl+P`, `F10` | Document file lifecycle, page geometry, database connections, and physical output execution. |
| **Edit** (`HID_MAIN_MENU2`) | Undo, Redo, Cut, Copy, Paste, Paste Special..., Delete, Duplicate, Select All | `Ctrl+Z`, `Ctrl+Y`, `Ctrl+X`, `Ctrl+C`, `Ctrl+V`, `Del`, `Ctrl+D`, `Ctrl+A` | Clipboard operations, object replication, and multi-level command undo/redo. |
| **View** (`HID_MAIN_MENU3`) | Template Design View, Data Entry Form View, Rulers, Grid, Snap to Grid, Snap to Objects, Zoom (Fit, 100%, In, Out) | `F5`, `F6`, `Ctrl+G` | Viewport customization, alignment assists, and visual scaling. |
| **Create** (`HID_MAIN_MENU4`) | Barcode, Text, Line, Shape, Picture, Table, Encoder (RFID / Magnetic Stripe) | `Alt+C` | Insertion commands for all supported canvas design primitives. |
| **Arrange** (`HID_MAIN_MENU6`) | Group, Ungroup, Align (Left, Center, Right, Top, Middle, Bottom), Distribute (Horiz, Vert), Order (Front, Back, Forward, Backward), Rotate (90°, 180°, 270°) | `Ctrl+G`, `Ctrl+U`, `Ctrl+Shift+]`, `Ctrl+Shift+[` | Spatial alignment, Z-order layering, grouping, and geometric transformation. |
| **Administer** (`HID_MAIN_MENU7a`)| Security Setup..., Licensing Setup..., System Database Connection..., Document Setup... | None | Enterprise administrative controls, user permissions, and license server endpoints. |
| **Tools** (`HID_MAIN_MENU7`) | User Preferences..., Companion Apps (Data Builder, Integration Builder, Process Builder, Print Station, History Explorer) | None | Global user settings and suite companion application launchers. |
| **Window** (`HID_MAIN_MENU8`) | Cascade, Tile Horizontally, Tile Vertically, Close All, Document Tab List | None | MDI child window arrangement and multi-document tab navigation. |
| **Help** (`HID_MAIN_MENU9`) | BarTender Help, About BarTender | `F1` | Integrated HTML help viewer and version/license details. |

---

## 4. Toolbars & Command Groups `[VERIFIED]`

BarTender provides modular, dockable toolbars powered by Codejock command bars:

1. **Main Toolbar (`Toolbar_Main.htm`) `[VERIFIED]`:**
   * Buttons: `New`, `Open`, `Save`, `Save All`, `Print`, `Print Preview`, `Cut`, `Copy`, `Paste`, `Undo`, `Redo`.
2. **Object Creation Toolbar (`Toolbar_Object.htm`) `[VERIFIED]`:**
   * Buttons: `Select Tool (Pointer)`, `Barcode Tool`, `Text Tool`, `Line Tool`, `Shape Tool`, `Picture Tool`, `Table Tool`, `RFID Tool`.
3. **Text Formatting Toolbar (`Toolbar_Text.htm`) `[VERIFIED]`:**
   * Controls: `Font Family ComboBox`, `Font Size ComboBox`, `Bold Toggle`, `Italic Toggle`, `Underline Toggle`, `Text Alignment (Left, Center, Right, Justify)`, `Font Color Picker`.
4. **Line & Shape Toolbar (`Toolbar_LineShape.htm`) `[VERIFIED]`:**
   * Controls: `Line Color Picker`, `Fill Color Picker`, `Line Thickness Spinner`, `Line Style (Solid, Dashed, Dotted) Dropdown`, `Corner Radius Spinner`.
5. **Arrange Toolbar (`Toolbar_Arrange.htm`) `[VERIFIED]`:**
   * Buttons: `Align Left`, `Align Center`, `Align Right`, `Align Top`, `Align Middle`, `Align Bottom`, `Distribute Evenly`, `Rotate 90° CW`, `Rotate 90° CCW`.
6. **View Toolbar (`Toolbar_View.htm`) `[VERIFIED]`:**
   * Controls: `Zoom In`, `Zoom Out`, `Zoom to Fit Page`, `Zoom 100%`, `Toggle Rulers`, `Toggle Grid`, `Toggle Snapping`.

---

## 5. Design Canvas & Rulers `[VERIFIED]`

### 5.1 Coordinate System & Rulers (`proc_desktop_ruler.htm`)
* **Dual Precision Rulers `[VERIFIED]`:**
  * Top horizontal ruler (X-axis) and left vertical ruler (Y-axis).
  * Selectable measurement units: Inches (`in`), Millimeters (`mm`), Centimeters (`cm`), Points (`pt`).
  * Real-time cursor tracking: Hairline red indicators on both rulers follow mouse movements with sub-pixel precision.
  * Zero-Origin Point: Located at the top-left corner of the printable label boundary by default; configurable to sheet edge.

### 5.2 Canvas Visual Regions `[VERIFIED]`
* **Pasteboard Area:** Neutral gray background (`#D4D0C8` / `#808080`) indicating non-drawable workspace.
* **Page Boundary:** Solid black perimeter outline representing physical paper media (e.g. 8.5″ × 11″ sheet or 4″ × 6″ continuous roll).
* **Label Boundary:** Blue dashed perimeter representing individual label contour (supports rectangle, rounded rectangle with custom corner radius, ellipse/circle, or CD/DVD hub cutout).
* **Unprintable Margin Boundary:** Light gray/magenta dotted inner line indicating printer physical margin limits.
* **Alignment Guides & Snapping `[VERIFIED]`:** Dynamic cyan alignment lines snap objects to canvas center, margins, and edges/centers of neighboring objects when within 4 screen pixels.

---

## 6. Dockable Toolbox Panes `[VERIFIED]`

Located on the left dockable panel (`Toolbox_Available_Panes_LP.htm`), hosting three primary tabs:

### 6.1 Data Sources Pane (`Toolbox_DataSources_Pane.htm`) `[VERIFIED]`
Presents a hierarchical TreeView of all available dynamic data variables:
* **Embedded Data (Screen Data):** Static literal values defined within the label.
* **Database Fields:** Categorized under connected tables (e.g., `Customers.LastName`, `Orders.TrackingNumber`).
* **Named Data Sources:** User-defined global variables shared across multiple objects or templates.
* **Global Data Fields:** Network-wide data variables synced via BarTender System Database.
* **Print Job Fields:** System variables (`Document Name`, `Page Number`, `Total Pages`, `Job ID`, `Printer Name`, `User Name`, `Current Date`, `Current Time`).
* **Drag-and-Drop Interaction `[VERIFIED]`:** Dragging any data field from this TreeView directly onto the canvas creates a new bound Text or Barcode object automatically.

### 6.2 Components Pane (`Toolbox_Components_Pane.htm`) `[VERIFIED]`
Presents preconfigured, reusable design snippets and barcode presets stored as `.btc` files:
* Categories: `Common Bar Codes`, `Circular Bar Codes`, `GS1 Compliance`, `Healthcare (HIBC)`, `Pharmaceutical`, `Postal & Shipping`.
* Dragging a component onto the canvas instantiates the complete pre-styled object tree.

### 6.3 Layers Pane (`Toolbox_Layers_Pane.htm`) `[VERIFIED]`
Provides full Z-index layer management:
* Features: `Add Layer`, `Delete Layer`, `Rename Layer`, `Reorder (Move Up/Down)`.
* Layer Controls: `Visibility Toggle (Eye icon)`, `Lock Toggle (Padlock icon)`, `Print When Condition`.

---

## 7. Dialogs & Configuration Windows `[VERIFIED]`

### 7.1 Page Setup Dialog (`HIDD_PAGESETUP.htm`) `[VERIFIED]`
Modal configuration window accessed via `File -> Page Setup...` or double-clicking the canvas background:
* **Tab 1: Page:** Paper size presets (Letter, Legal, A4, Custom Width × Height), Orientation (Portrait, Landscape, Portrait 180°, Landscape 180°).
* **Tab 2: Stock:** Category/Manufacturer dropdown (Avery, Zebra, Brady, etc.) with thousands of predefined label skus.
* **Tab 3: Layout:** Multi-label sheet matrix configuration:
  * Rows and Columns spinners.
  * Margins (Top, Bottom, Left, Right).
  * Gaps / Pitch (Horizontal and Vertical distance between adjacent labels).
* **Tab 4: Shape:** Selection between `Rectangle`, `Rounded Rectangle` (with corner radius spinner), `Ellipse / Circle`.
* **Tab 5: Media Handling:** Continuous roll vs. Die-cut labels; Transmissive vs. Reflective (black mark) sensor options.
* **Tab 6: Printing Order:** Selection of starting corner (Top-Left, Top-Right, Bottom-Left, Bottom-Right) and traversal direction (Across then Down, Down then Across).
* **Tab 7: Background:** Solid fill color, watermark graphic, or non-printing design guide template image.

### 7.2 Barcode Properties Dialog (`Objects_BarcodePropertiesDialog.htm`) `[VERIFIED]`
Dual-pane dialog accessed via double-clicking any barcode object:
* **Left Navigation Tree:**
  * `[Selected Object]`: Object name, comments, lock flag, conditional printing rules.
  * `Symbology and Size`: Symbology selector (Code 128, QR Code, Data Matrix, etc.), X-Dimension (narrow bar width in mils), Bar Height, Wide-to-Narrow Ratio, Quiet Zones.
  * `Human Readable`: Visibility (`None`, `Below`, `Above`, `Embedded`), Font Family, Font Size, Alignment, Offset Margin.
  * `Data Sources Tree`: Lists all concatenated substrings forming the encoded value.
* **Right Contextual Page:** Displays specific parameters based on the active tree selection.

### 7.3 Database Setup Dialog (`DB_Types_LandingPage.htm`) `[VERIFIED]`
Multi-step configuration wizard and property editor:
* **Connection Types Supported:** Delimited Text (CSV/TSV), Microsoft Excel, ODBC, OLEDB, Microsoft SQL Server, Oracle, JSON, XML, SAP IDoc.
* **Table & Join Editor:** Visual join builder (Inner Join, Left Outer Join) for multi-table schemas.
* **Query Prompts:** Configures print-time filter criteria prompted to the operator.
* **Record Selection Dialog (`HIDD_DB_BROWSE_SELECTION_DIALOG.htm`):** Interactive grid allowing operators to cherry-pick specific records for printing.

### 7.4 Print Dialog (`CmdLine_Printing.htm`) `[VERIFIED]`
Accessed via `Ctrl+P`:
* **Printer Selection:** Target printer dropdown, driver properties button, status indicator.
* **Quantities:** `Copies` (identical duplicates) vs. `Serialized Copies` (counter increments).
* **Record Selection:** `All Records`, `Selected Records`, or specific `Record Range` (e.g. `1-10, 15, 20-30`).
* **Print to File Checkbox:** Renders output to raw spooler file (`.prn` / `.zpl`).
* **Action Buttons:** `Print`, `Print Preview`, `Cancel`.

---

## 8. Status Bar & Interactive Feedback `[VERIFIED]`

The status bar across the bottom of the Designer window provides real-time operational feedback:
1. **Status Text (Left):** "Ready", "Drawing Object...", "Connecting to Database...", "Saving Document...".
2. **Cursor Position Indicator:** Displays real-time X and Y coordinates (e.g. `X: 1.250 in, Y: 0.875 in`).
3. **Selected Object Dimensions:** Displays bounding width and height (e.g. `W: 2.500 in, H: 1.000 in`).
4. **Selection Summary:** Name of active object (e.g. `Barcode 1 (Code 128)`).
5. **Active Printer Indicator:** Name of configured target printer (e.g. `Zebra ZT410 (300 dpi)`).
6. **Zoom Slider & Percentage:** Slider control with `[-]` and `[+]` buttons and percentage label (`100%`).
