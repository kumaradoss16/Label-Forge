# 08. Workflow Catalog: BarTender Designer 11.4

## 1. Overview
This catalog details 10 end-to-end operator workflows observed in BarTender Designer 11.4. Each workflow contains an objective, prerequisites, step-by-step reproduction instructions, expected observable results, verification status, and clean-room implementation blueprints.

---

## 2. Workflows Catalog

### WF-01: Blank Template & Page Setup Workflow
* **Verification Status:** `[VERIFIED]` (`HIDD_PAGESETUP.htm`, `New Document Wizard`)
* **Objective:** Create a new custom 4.0″ × 6.0″ single-label document for thermal shipping labels.
* **Prerequisites:** BarTender Designer open.
* **Step-by-Step Reproduction Steps:**
  1. Click `File -> New` or press `Ctrl+N`.
  2. In the `New Document Wizard`, choose `Blank Template` and click `Next`.
  3. Select target printer (e.g. `Zebra ZT410 (203 dpi)`) and click `Next`.
  4. Under Stock Selection, choose `Specify Custom Settings` and click `Next`.
  5. Select Shape: `Rounded Rectangle` (Radius: `0.125 in`) and click `Next`.
  6. Specify Page Size: Width = `4.00 in`, Height = `6.00 in`, Orientation = `Portrait`. Click `Next`.
  7. Set Margins: Left = `0.00`, Right = `0.00`, Top = `0.00`, Bottom = `0.00`. Click `Next`.
  8. Click `Finish`.
* **Observable Behavior:** A new canvas tab titled `Document1.btw` opens, displaying a 4″ × 6″ rounded rectangle label outline with zero margins and rulers initialized from 0 to 4 inches (top) and 0 to 6 inches (left).

---

### WF-02: Predefined Stock Label Workflow (Multi-Label Sheet)
* **Verification Status:** `[VERIFIED]` (`HIDD_PAGESETUP.htm`, `Stock Tab`)
* **Objective:** Configure a standard 30-up address label sheet (Avery 5160) on Letter paper.
* **Prerequisites:** Standard desktop laser printer available.
* **Step-by-Step Reproduction Steps:**
  1. Press `Ctrl+N`.
  2. In the Wizard, select `Blank Template` -> Choose standard laser printer.
  3. Under Stock Selection, select `Select a predefined stock` and click `Next`.
  4. Set Category = `Avery Standard`, Stock Type = `5160 Address`. Click `Next`.
  5. Click `Finish`.
* **Observable Behavior:** The canvas initializes with an 8.5″ × 11″ sheet containing a 3-column × 10-row matrix. The active label editor focuses on cell (Row 1, Column 1) with individual dimensions `2.625 in` width × `1.00 in` height.

---

### WF-03: Barcode Insertion & Formatting Workflow
* **Verification Status:** `[VERIFIED]` (`Objects_BarcodePropertiesDialog.htm`, `Toolbar_Object.htm`)
* **Objective:** Insert a Code 128 barcode and configure its dimensions, human-readable text, and narrow bar width.
* **Prerequisites:** Open label document.
* **Step-by-Step Reproduction Steps:**
  1. Click `Create -> Barcode -> Linear -> Code 128` (or click Barcode icon on Object Toolbar).
  2. Click near coordinate (1.0″, 1.5″) on the design canvas.
  3. Object is placed showing default sample bars and human-readable text "12345678".
  4. Double-click the barcode object to open `Barcode Properties Dialog`.
  5. Select `Symbology and Size` in the left tree:
     * Set `X Dimension` = `15.0 mils` (0.015 in).
     * Set `Bar Height` = `0.75 in`.
     * Set `Quiet Zones`: Check Left (`0.15 in`) and Right (`0.15 in`).
  6. Select `Human Readable` in the left tree:
     * Set Placement = `Below`.
     * Click `Font` child page: Select `Arial`, Size = `10 pt`, Style = `Bold`.
  7. Click `Close`.
* **Observable Behavior:** Barcode re-renders interactively on the canvas with matching dimensions and sharp vector bars.

---

### WF-04: QR Code & 2D Matrix Configuration Workflow
* **Verification Status:** `[VERIFIED]` (`BarCode_QRCode.dll`, `Objects_BarcodePropertiesDialog.htm`)
* **Objective:** Insert a 2D QR Code with High Error Correction (Level H) and encode a URL.
* **Prerequisites:** Open label document.
* **Step-by-Step Reproduction Steps:**
  1. Click `Create -> Barcode -> 2D -> QR Code`.
  2. Click on the canvas at (2.0″, 3.0″).
  3. Double-click the QR code object.
  4. In `Symbology and Size`:
     * Set `Error Correction Level` = `High (30%)`.
     * Set `Module Size` = `20 mils`.
  5. Under `Data Sources` in the left tree, select the default substring.
  6. On the right panel, enter the URL string: `https://example.com/asset/10001`.
  7. Click `Close`.
* **Observable Behavior:** QR Code matrix re-generates with denser cell grid reflecting Error Correction Level H.

---

### WF-05: Serialization Counter Setup Workflow
* **Verification Status:** `[VERIFIED]` (`XMLLabel_2.0.xsd`, `PrintSetup.cs`)
* **Objective:** Create an auto-incrementing serial number field with zero padding (e.g. `SN-0001`).
* **Prerequisites:** Open label document.
* **Step-by-Step Reproduction Steps:**
  1. Click `Create -> Text -> Single Line` and place text on canvas.
  2. Double-click the text object to open Properties.
  3. In the left tree, select the default substring.
  4. On the right panel, enter initial value: `0001`.
  5. Select the `Transforms` tab (or sub-page) -> Click `Serialization`:
     * Check `Serialize`.
     * Set Method = `Numeric`.
     * Set Direction = `Increment`.
     * Set Step Value = `1`.
     * Set Event = `Every Label`.
     * Check `Preserve leading zeros` (Length: `4`).
  6. Add a second static substring at Position 1 with text `SN-`. Reorder static substring to Position 1 and serialized substring to Position 2.
  7. Click `Close`.
* **Observable Behavior:** Canvas displays `SN-0001`. During print execution, successive labels render `SN-0002`, `SN-0003`, etc.

---

### WF-06: CSV / Delimited Text Data Binding Workflow
* **Verification Status:** `[VERIFIED]` (`Seagull.Data.TextFileClient.dll`, `Toolbox_DataSources_Pane.htm`)
* **Objective:** Connect an external CSV file and dynamically bind database fields to label objects.
* **Prerequisites:** A valid CSV file (e.g. `Products.csv` with headers `SKU,Description,Price,Barcode`).
* **Step-by-Step Reproduction Steps:**
  1. Click `File -> Database Connection Setup...`.
  2. Select `Text File` in the wizard and click `Next`.
  3. Browse and select `Products.csv`.
  4. Set Delimitation = `Comma`, Format = `First row contains field names`. Click `Next`.
  5. The preview table displays parsed records. Click `Finish`.
  6. In the left dockable `Toolbox`, click the `Data Sources` tab.
  7. Expand `Database Fields -> Products`.
  8. Drag the `Barcode` field from the Toolbox onto the canvas: choose `Create as Barcode`.
  9. Drag the `Description` field onto the canvas: choose `Create as Text`.
* **Observable Behavior:** Objects appear populated with data from Record 1 of the CSV file. Bottom status bar displays record navigator controls (`<`, `>`, `1 of 500`).

---

### WF-07: Alignment & Distribution Workflow
* **Verification Status:** `[VERIFIED]` (`HID_ARRANGE_GROUP.htm`, `Toolbar_Arrange.htm`)
* **Objective:** Align multiple disparate objects along their left margins with equal vertical spacing.
* **Prerequisites:** At least 3 objects on canvas (e.g., Header Text, Barcode, Footer Text).
* **Step-by-Step Reproduction Steps:**
  1. Marquee drag over all 3 objects (or hold `Shift` and click each object).
  2. Ensure the desired anchor object (e.g. Header Text) is clicked last so it displays solid selection handles.
  3. Click `Arrange -> Align -> Left` (or click Align Left on toolbar).
  4. Click `Arrange -> Distribute -> Vertically`.
* **Observable Behavior:** All 3 objects snap to the exact Left X-coordinate of the anchor object, with equal vertical gap between object 1-to-2 and object 2-to-3.

---

### WF-08: Print Preview & Record Navigation Workflow
* **Verification Status:** `[VERIFIED]` (`HID_FILE_PRINTPREVIEW.htm`, `PrintPreview.cs`)
* **Objective:** Inspect WYSIWYG pagination and verify dynamic database record rendering before printing.
* **Prerequisites:** Label document connected to database.
* **Step-by-Step Reproduction Steps:**
  1. Click `File -> Print Preview` or press `F10`.
  2. The modal `Print Preview Window` opens, rendering Page 1 at 100% DPI.
  3. Click `Next Page` (`>`) on the preview toolbar to advance through records.
  4. Adjust Zoom slider to `Fit Page` or `200%` to verify barcode quiet zones.
  5. Click `Close` to return to design canvas.
* **Observable Behavior:** Exact raster representations of each record render without printing physical paper.

---

### WF-09: Print Execution Workflow (Copies vs. Serialization)
* **Verification Status:** `[VERIFIED]` (`CmdLine_Printing.htm`, `PrintSetup.cs`)
* **Objective:** Print 2 serialized numbers with 3 identical copies each (Total: 6 labels).
* **Prerequisites:** Configured label with serialization counter.
* **Step-by-Step Reproduction Steps:**
  1. Click `File -> Print` or press `Ctrl+P`.
  2. In the Print Dialog:
     * Select Target Printer.
     * Set `Copies` = `3`.
     * Set `Serialized Copies` = `2`.
  3. Click `Print`.
* **Observable Behavior:** The print engine generates 6 labels in sequence: Serial A (copy 1, 2, 3), followed by Serial B (copy 1, 2, 3), and dispatches the job to the Windows Spooler.

---

### WF-10: Document Save & Version Compatibility Workflow
* **Verification Status:** `[VERIFIED]` (`HIDD_BARTENDER_DOCUMENT_SETUP_DIALOG.htm`, `01_TARGET_IDENTITY.md`)
* **Objective:** Save document format with backward compatibility for older BarTender versions.
* **Prerequisites:** Open label document.
* **Step-by-Step Reproduction Steps:**
  1. Click `File -> Save As...`.
  2. Enter file name: `ShippingLabel_v10.btw`.
  3. In `Document Version` selector, choose `BarTender 10.1`.
  4. Click `Save`.
* **Observable Behavior:** File is saved to disk. If any features incompatible with 10.1 were utilized, a warning report lists the features before confirming the save operation.
