# 08. MVP Scope Specification: Independent Label Designer

## 1. Executive Summary
This document establishes the Minimum Viable Product (MVP) scope for the independent Windows desktop label design application. It defines functional boundaries, feature prioritization, acceptance criteria, and explicit non-goals to deliver a production-ready, clean-room solution with equivalent core capabilities to BarTender Designer 11.4.

---

## 2. In-Scope vs. Out-of-Scope Matrix

```
+---------------------------------------------------------------------------------------+
|                                    Scope Boundary                                     |
+---------------------------------------------------+-----------------------------------+
|               IN-SCOPE (MVP Phase 1)              |       POST-MVP (Future Phases)    |
+---------------------------------------------------+-----------------------------------+
| [x] Interactive Vector Canvas & Precision Rulers  | [ ] RFID / EPC Gen2 Encoding      |
| [x] Dynamic Zoom (25% - 800%) & Snapping Grid     | [ ] Magnetic Stripe Encoding      |
| [x] Text Objects (Fonts, Alignment, Word Wrap)    | [ ] Full VBScript Scripting Host  |
| [x] 1D Barcodes: Code 128, Code 39, EAN-13, UPC-A | [ ] SAP IDoc Enterprise Client    |
| [x] 2D Barcodes: QR Code, Data Matrix (ECC 200)   | [ ] Centralized Librarian Server  |
| [x] Shapes: Rectangles, Rounded Rects, Lines, Oval| [ ] USB Video Camera Frame Grabber|
| [x] Image Objects: PNG, JPEG, BMP, SVG            | [ ] PANTONE Color Calibration     |
| [x] CSV / Delimited Text Database Data Binding    | [ ] Complex SQL Query Builder     |
| [x] Serialization Counters (Numeric/Alpha Step)   | [ ] Custom Data Entry Form UI     |
| [x] Multi-Label Sheet Layout (Rows, Cols, Gaps)   | [ ] Print Scheduler Service Queue |
| [x] Multi-Page Print Preview Window               | [ ] Electronic Signatures & 21 CFR|
| [x] Windows Spooler Printing (GDI/XPS)            | [ ] Cloud SaaS Storage Connectors |
| [x] Direct Zebra ZPL II Thermal Printer Output    |                                   |
| [x] Vector PDF Export via QuestPDF                |                                   |
| [x] Native JSON Document Format (.olb) Save/Open  |                                   |
+---------------------------------------------------+-----------------------------------+
```

---

## 3. Detailed MVP Functional Requirements

### 3.1 Document & Canvas Management (REQ-DOC)
* **REQ-DOC-01: Page Setup Dialog:** Allows setting paper dimensions (Inches or Millimeters), orientation (Portrait/Landscape), and label count (Rows × Columns).
* **REQ-DOC-02: Predefined Stock Library:** Includes preconfigured templates for common industry formats:
  * Shipping Label (4.0″ × 6.0″ continuous roll)
  * Address Sheet (Avery 5160: 3 columns × 10 rows on 8.5″ × 11″)
  * Asset Tag (2.0″ × 1.0″ roll)
* **REQ-DOC-03: Interactive Canvas:**
  * Real-time horizontal and vertical rulers with tracking hairline indicators.
  * Drag-and-drop object placement, 8-point adorner resizing, and orthogonal rotation (90°, 180°, 270°).
  * Snap-to-grid and snap-to-neighbor alignment guides.
  * Multi-level Undo/Redo stack (`Ctrl+Z`, `Ctrl+Y`).

### 3.2 Label Object Capabilities (REQ-OBJ)
* **REQ-OBJ-01: Text Objects:**
  * Single-line text with auto-fit font sizing.
  * Multi-line text with word wrapping.
  * System font picker (Family, Point Size, Bold, Italic, Color, Alignment: Left/Center/Right).
* **REQ-OBJ-02: Barcode Objects:**
  * Core 1D Symbologies: Code 128 (Auto subset A/B/C), Code 39, EAN-13, UPC-A, Interleaved 2 of 5.
  * Core 2D Symbologies: QR Code (Model 2, Error Correction L/M/Q/H), Data Matrix (ECC 200).
  * Configurable narrow bar width (X Dimension in mils), height, and quiet zones.
  * Optional human-readable text placement (Below, Above, or None).
* **REQ-OBJ-03: Vector Shapes & Images:**
  * Rectangle and Rounded Rectangle (configurable corner radius).
  * Line (stroke thickness, solid/dash styles).
  * Ellipse / Circle.
  * Bitmap image import (PNG, JPEG, BMP) with preserve aspect ratio.

### 3.3 Data Sources & Dynamic Evaluation (REQ-DAT)
* **REQ-DAT-01: Embedded Data:** Static literal string content.
* **REQ-DAT-02: Serialization Counter:** Auto-incrementing or decrementing counter with configurable start value, step increment, and zero-padding format (`001`, `002`).
* **REQ-DAT-03: Clock / TimeStamp:** System date and time evaluation with format strings (`yyyy-MM-dd`, `HH:mm:ss`).
* **REQ-DAT-04: CSV / Delimited Text Binding:**
  * File picker for `.csv` or `.txt` files with header row detection.
  * Field list treeview allowing field binding to any text or barcode object.
  * Record navigator allowing stepping through records directly on the design canvas.

### 3.4 Printing, Preview & Export (REQ-PRN)
* **REQ-PRN-01: Multi-Page Print Preview:**
  * High-fidelity WYSIWYG preview window.
  * Interactive page stepper and zoom controls.
* **REQ-PRN-02: Windows Spooler Printing:**
  * Standard print execution to any installed Windows printer.
  * Supports multiple identical copies and multi-record printing.
* **REQ-PRN-03: Direct Thermal Printer Output (ZPL II):**
  * Direct ASCII ZPL generation for Zebra thermal printers, transmitted over Windows raw spooler.
* **REQ-PRN-04: Vector PDF Export:**
  * High-resolution, crisp vector PDF export for digital distribution.

---

## 4. BarTender 11.4 Traceability Matrix

| BarTender 11.4 Feature | BarTender Component | Independent MVP Capability | Equivalence Rating |
| :--- | :--- | :--- | :--- |
| **New / Open / Save** | MFC Document/View (`BarTend.exe`) | `OpenLabel.Core` JSON Storage | 100% Equivalent |
| **Page Setup** | `HIDD_PAGESETUP.htm` | `PageSetupDialog` (WPF) | 100% Core Layout Equiv. |
| **Rulers & Snapping** | `proc_desktop_ruler.htm` | WPF Vector Rulers & Adorners | 100% Equivalent |
| **Barcode Generation**| `BarCode_*.dll` (Aztec, QR, DM) | `ZXing.Net` Managed Barcode Engine | 100% Core Symbology Equiv. |
| **Text & Fonts** | MFC Uniscribe GDI Text | WPF DirectWrite Typography | Superior (Full DPI Aware) |
| **Database Setup** | `Seagull.Data.*.dll` | CSV / Delimited Reader | 100% CSV/Text Equiv. |
| **Serialization** | `XMLLabel_2.0.xsd` Counters | `SerializationCounter` Engine | 100% Equivalent |
| **Print Preview** | `HID_FILE_PRINTPREVIEW.htm` | `PrintPreviewWindow` (WPF) | 100% Equivalent |
| **Thermal Printing** | Seagull Printer Code Templates | `ZplGenerator` Raw Thermal Pipeline| 100% Zebra Equiv. |
| **PDF Export** | Debenu QuickPDF / PDFium | `QuestPDF` Clean-Room Pipeline | 100% Equivalent |

---

## 5. Acceptance Criteria (User Story Level)

1. **US-01 (Label Authoring):**
   * *Given* an empty designer window, *when* the user creates a 4″ × 6″ template and adds a Code 128 barcode and two text fields, *then* the objects must be freely selectable, movable, and resizable with visual snapping.
2. **US-02 (Data Binding):**
   * *Given* a 50-row CSV file containing customer addresses, *when* the user links the CSV file and maps columns to text objects, *then* the design canvas must display the values of Record 1 and allow browsing subsequent records.
3. **US-03 (Serialization):**
   * *Given* a serialization counter starting at `1001` with step `1`, *when* printing 10 serialized copies, *then* 10 distinct labels must be emitted with counters from `1001` to `1010`.
4. **US-04 (Thermal Printing):**
   * *Given* a Zebra ZPL-compatible thermal printer, *when* the user executes a print job, *then* valid ZPL commands (`^XA...^XZ`) must be sent directly to the printer spooler without graphic distortion.
5. **US-05 (Persistence):**
   * *Given* a configured label with barcodes, text, and database links, *when* the user saves to `.olb` and reopens the file, *then* the design must restore with 100% spatial and data-source fidelity.
