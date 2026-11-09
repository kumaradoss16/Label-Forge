# 06. Behavioural Specification: BarTender Designer 11.4

## 1. Overview & Verification Status
This specification defines the runtime interaction semantics, event dispatching sequences, manipulation math, serialization rules, print processing pipelines, and error-handling behaviors of BarTender Designer 11.4.

All behaviors documented herein have been verified against compiled MFC message maps, documentation procedures, schema definitions, and SDK automation samples.

---

## 2. Document Lifecycle Behaviors

### 2.1 Create New Document `[VERIFIED]`
* **Trigger:** `File -> New` or `Ctrl+N`.
* **Observable Behavior:**
  1. The `New Document Wizard` dialog launches modally.
  2. Prompts user to choose between:
     * `Blank Template`: Custom dimensions and layout.
     * `Existing BarTender Document`: Clones an existing `.btw` template.
  3. Prompts for target printer (determines printable boundaries and hardware font metrics).
  4. Prompts for Stock selection (Predefined manufacturer SKU vs. User-defined dimensions).
  5. Prompts for Page shape (Rectangle, Rounded Rectangle, Ellipse/Circle).
  6. Prompts for Label margins and layout (Rows, Columns, Gaps).
  7. On clicking `Finish`, instantiates a new document tab titled `DocumentN.btw` in `Unmodified` state.
* **Reproduction Steps:**
  1. Launch BarTender.
  2. Press `Ctrl+N`.
  3. Step through Wizard: Select `Blank Template` -> Choose Printer -> Select `Specify Custom Settings` -> Enter `4.0 in` width, `6.0 in` height -> Click `Finish`.
  4. Verify design canvas initializes with matching 4″ × 6″ boundary.

### 2.2 Save & Save As Behaviors `[VERIFIED]`
* **Trigger:** `File -> Save` (`Ctrl+S`) or `File -> Save As...`.
* **Observable Behavior:**
  1. If document is new, opens standard Windows Common File Dialog filtered to `BarTender Documents (*.btw)`.
  2. In `Save As`, provides version compatibility selection via `Document Setup Dialog`:
     * Can save as BarTender 11.4, 11.3, 11.2, 11.1, 11.0, 10.1 (`HIDD_BARTENDER_DOCUMENT_SETUP_DIALOG.htm`).
  3. Generates the binary `.btw` package: writes ASCII header with version/build info, embeds active PNG preview thumbnail, serializes document DOM binary streams, and terminates with `0x1A`.
  4. Clears dirty state indicator (`*` removed from title bar; `IsModified = false`).
* **Auto-Save Behavior `[VERIFIED]`:**
  * When enabled in `User Preferences`, writes a hidden shadow copy at configured intervals (default: 10 minutes) to `%LocalAppData%\Seagull Scientific\AutoSave\`.

### 2.3 Open & Reopen Behaviors `[VERIFIED]`
* **Trigger:** `File -> Open` (`Ctrl+O`) or MRU (Most Recently Used) list in File menu.
* **Observable Behavior:**
  1. Validates file header for `Bar Tender Format File`.
  2. If file was created in an older version, loads seamlessly and prompts warning only upon saving back if newer features were added.
  3. If file references an external database connection that is missing or inaccessible, displays a warning dialog and retains the last-known cached schema and field names.
  4. Reconstructs all layers, canvas objects, fonts, and data bindings with 100% geometric fidelity.

---

## 3. Object Manipulation Behaviors

### 3.1 Object Insertion Workflow `[VERIFIED]`
* **Trigger:** Click tool button on `Create` toolbar (e.g. `Barcode`, `Text`, `Shape`).
* **Observable Behavior:**
  1. Mouse cursor transforms into an insertion crosshair with tool icon.
  2. Clicking on the canvas places the object with default dimensions (e.g., Barcode: 2.0″ × 0.75″; Text: single line with "Sample Text").
  3. Alternatively, clicking and dragging defines the initial bounding box.
  4. The newly created object automatically gains focus, displaying 8 resizing handles and 1 rotation handle.

### 3.2 Selection & Hit-Testing Rules `[VERIFIED]`
* **Single Click:**
  * Clicking an unselected object deselects previous objects and selects target.
  * Clicking empty pasteboard clears selection.
* **Marquee / Rubberband Selection:**
  * Dragging on canvas background creates a selection rectangle.
  * Objects whose bounding box intersects the marquee are selected upon mouse release.
* **Multi-Selection:**
  * `Shift+Click` or `Ctrl+Click` toggles individual object inclusion.
  * Primary Selection ("Key Object"): The last clicked object displays filled square handles; secondary objects display hollow handles. Alignment operations align relative to the key object.

### 3.3 Move & Geometric Transformations `[VERIFIED]`
* **Translation (Move):**
  * Dragging inside an object's boundary moves the object ($X' = X + \Delta x, Y' = Y + \Delta y$).
  * Keyboard arrow keys nudge by 1 grid unit (or 1 pixel); `Shift + Arrow` nudges by 10 units.
* **Resize:**
  * Dragging corner handles scales Width and Height simultaneously.
  * Holding `Shift` during corner drag enforces aspect ratio lock ($W/H = \text{constant}$).
  * Dragging edge handles resizes along a single dimension (Width or Height).
* **Rotation:**
  * Dragging the green/circular rotation handle above the object rotates the object around its anchor center.
  * Holding `Shift` snaps rotation to 15° increments.
  * Standard commands: `Arrange -> Rotate 90° CW`, `Rotate 90° CCW`, `Rotate 180°`.

### 3.4 Alignment & Distribution `[VERIFIED]`
* **Alignment Actions (`HID_ARRANGE_GROUP.htm`):**
  * `Align Left`: Sets all selected objects' Left coordinate to the key object's Left.
  * `Align Center`: Centers all selected objects horizontally on the key object.
  * `Align Right`: Sets all selected objects' Right coordinate to the key object's Right.
  * `Align Top`: Sets all selected objects' Top coordinate to the key object's Top.
  * `Align Middle`: Centers all selected objects vertically on the key object.
  * `Align Bottom`: Sets all selected objects' Bottom coordinate to the key object's Bottom.
* **Distribution:**
  * Horizontally / Vertically spaces 3 or more selected objects with equal gaps between adjacent boundaries.

### 3.5 Grouping & Z-Order Layering `[VERIFIED]`
* **Group (`Ctrl+G`) / Ungroup (`Ctrl+U`):**
  * Selected objects are encapsulated in a single composite `GroupObject`.
  * Moves, scales, and rotates as a single rigid body.
* **Z-Order Ordering:**
  * `Bring to Front` (`Ctrl+Shift+]`): Moves object to the highest Z-index within its layer.
  * `Send to Back` (`Ctrl+Shift+[`): Moves object to the lowest Z-index within its layer.
  * `Bring Forward` / `Send Backward`: Steps object one position up or down in Z-order.

---

## 4. Data-Source Evaluation & Serialization Engine `[VERIFIED]`

### 4.1 Serialization Rules (Auto-Increment / Counter)
Serialization parameters configure dynamic incrementation across printed labels:

| Parameter | Options / Semantics `[VERIFIED]` | Observable Rule |
| :--- | :--- | :--- |
| **Direction** | `Increment` (+Step) or `Decrement` (-Step) | Determines arithmetic addition or subtraction. |
| **Base / Method** | `Numeric` (0-9), `Alphanumeric` (0-9, A-Z), `Hexadecimal` (0-F), `Custom Character Set` | Controls rollover sequence (e.g. `09` -> `10`, `0Z` -> `1A`). |
| **Step Value** | Integer value (e.g. `1`, `2`, `5`) | Added to counter per cycle. |
| **Trigger Frequency** | `Every Label`, `Every Record`, `Every Page`, `After Specified Copies (N)` | Governs counter advance timing. |
| **Preserve Leading Zeros** | Fixed width padding (e.g. `0001`, `0002`) | Pads string with `0` up to specified character length. |
| **Rollover / Reset** | Resets upon reaching maximum value or on database record change | Prevents overflow and resets batch runs. |

### 4.2 Data Transformation Pipeline `[VERIFIED]`
Data assigned to a substring undergoes a deterministic sequential transformation chain:
1. **Raw Value Ingestion:** From static text, database column, or system clock.
2. **Character Filtering:** Numeric only, Uppercase only, Lowercase only, or custom regex mask.
3. **Truncation:** Truncate left $N$ characters, truncate right $N$ characters.
4. **Search and Replace:** Literal or regular expression string replacement.
5. **Prefix and Suffix:** Appends static headers and footers to substring.
6. **VBScript / Custom Expression:** Executes user-defined script to modify `Value`.
7. **SubString Concatenation:** Merges multiple substrings into final object data string.

---

## 5. Printing & Spooling Behaviors `[VERIFIED]`

### 5.1 Copies vs. Serialized Copies
* **Identical Copies (`IdenticalCopiesOfLabel`):** Multiplies output of the identical label without advancing serialization counters.
* **Serialized Copies (`NumberOfSerializedLabels`):** Advances the serialization counter for each individual label output.
* **Example Matrix:**
  * If `Identical Copies = 2` and `Serialized Copies = 3` (Start = `101`):
  * Emitted labels: `101`, `101`, `102`, `102`, `103`, `103` (Total: 6 labels).

### 5.2 Multi-Label Sheet Pagination
For sheet media (e.g., 3 columns × 10 rows):
1. **Starting Position Selection:** Operator can pick an arbitrary cell (e.g. Row 2, Column 3) to print on partially used label sheets.
2. **Traversal Trajectory:**
   * `Across then Down`: Fills row 1 (columns 1, 2, 3), then row 2, etc.
   * `Down then Across`: Fills column 1 (rows 1–10), then column 2, etc.
3. **Sheet Eject:** Upon completing cell (10, 3), emits page break (`EndPage()`) and starts cell (1, 1) on next sheet.

### 5.3 Thermal Printer Direct Output (ZPL II) `[VERIFIED]`
When printing to thermal printers via Seagull drivers:
* Bypasses raster image generation.
* Emits ASCII ZPL commands:
  * Label dimensions: `^PW812^LL1218`
  * Text using printer fonts: `^FO50,100^A0N,30,30^FD...^FS`
  * Barcodes using printer firmware: `^FO50,200^BCN,100,Y,N,N^FD...^FS`
  * Serialized counter commands: `^SN` (allows the printer's onboard firmware to increment counters without resending data packets over the network).

---

## 6. Error Handling & Boundary Conditions `[VERIFIED]`

| Condition | Observable Behavior `[VERIFIED]` | Recovery Action |
| :--- | :--- | :--- |
| **Barcode Data Overflow** | If data string exceeds symbology capacity (e.g. 15 digits in UPC-A), canvas displays red cross-hatching and a warning glyph. | Truncate data or switch to dynamic symbology (e.g. Code 128 / QR). |
| **Missing Database Connection** | Displays warning dialog on open: "Database connection failed: File not found." Retains schema structure and cached sample values. | Re-link path in `File -> Database Connection Setup...`. |
| **Printer Unreachable** | Windows Print Spooler queues job in local spool directory; status bar reports "Printer Offline / Error". | Job resumes automatically when printer comes back online. |
| **Unlicensed Runtime API** | If COM or .NET Print Engine is invoked without active license, throws `Seagull.BarTender.Print.LicenseException: You must activate BarTender with a valid product key code...`. | Enter valid Product Key Code via Activation Wizard (`ActivationWizard.exe`). |
