# UI Observations & Clean-Room Behavioral Reference

**Project:** Label-Forge  
**Classification:** `[VERIFIED_DOCUMENTATION]` & `[INDEPENDENT_OBSERVATION]`  
**Purpose:** Purely textual and structural reference documenting observable BarTender Designer 11.4 UI workflows, canvas layout, and object anchors.  

> [!NOTE]
> **Copyright & Legal Compliance:**
> In accordance with clean-room reverse-engineering protocols, all proprietary screenshots, bitmaps, icons, and copyrighted CHM graphic assets previously extracted for inspection have been **permanently removed** from the repository to prevent copyright infringement and unauthorized redistribution.
> 
> This reference preserves only independently authored behavioral descriptions, mathematical models, coordinate anchor specifications, and UI element inventories required for clean-room implementation of Label-Forge.

---

## 1. Main Designer Canvas Layout

### 1.1 Structural Geometry
- **Coordinate Origin:** The top-left corner of the printable label region $(0, 0)$ is the default origin.
- **Ruler Scales:** Horizontal and vertical rulers track the canvas bounds, supporting dual measurement modes:
  - Metric: Millimeters (`mm`) with 1 mm tick marks and 10 mm major divisions.
  - Imperial: Inches (`in`) with 1/16 in subdivisions and 1 in major divisions.
- **Snap-to-Grid:** Configurable grid spacing (default 1 mm or 0.1 in) with optional magnetic snapping for object edges and centerlines.

---

## 2. Nine-Point Object Anchor System

Observed behavior during object transformation and rotation:

```
[Top-Left]       [Top-Center]       [Top-Right]
     ┌─────────────────┬─────────────────┐
     │                 │                 │
[Center-Left]      [Center]       [Center-Right]
     │                 │                 │
     └─────────────────┴─────────────────┘
[Bottom-Left]   [Bottom-Center]   [Bottom-Right]
```

1. **Origin Pinning:** Each design object (Text, Barcode, Shape, Picture) defines an active reference point selected from the 9 positions above.
2. **Expansion Behavior:** When content dynamically expands (e.g. variable-length text or growing barcode widths due to larger data payloads), the object expands away from the pinned anchor point while the anchor's $(X, Y)$ coordinate remains fixed on the canvas.
3. **Rotational Pivot:** Rotation (0°, 90°, 180°, 270°, or arbitrary angles) pivots around the chosen reference anchor point.

---

## 3. Visual Design Objects Inventory

From observable studio inspection:
1. **Single-line Text:** Monospaced or proportional Windows fonts, single line of text with optional auto-fit font size.
2. **Multi-line Text (Paragraph):** Text with word wrapping, alignment (Left, Center, Right, Justified), line spacing, and paragraph indentation.
3. **1D Linear Barcode:** Code 128, Code 39, Interleaved 2 of 5, EAN-13, UPC-A, with optional human-readable text (Below, Above, None) and configurable narrow bar width (X-dimension).
4. **2D Matrix Barcode:** QR Code, Micro QR, Data Matrix (ECC 200), PDF417, Aztec, with configurable module sizes and error correction levels.
5. **Geometric Shapes:** Rectangles, Rounded Rectangles (with corner radius), Ellipses/Circles, Lines (Horizontal, Vertical, Diagonal).
6. **Picture Objects:** Bitmap images (PNG, JPEG, BMP) with options for Embedded Image, Linked File Path, or Database Binary Field.

---

## 4. Eight-Point Selection Adorner Behavior

When an object is selected on the canvas:
- An adorner bounding rectangle is displayed with **8 interactive grab handles** (4 corners, 4 edge midpoints).
- A **rotation handle** extends above the top-center grab handle.
- Corner handles perform proportional or free 2D resizing depending on `Shift` key state.
- Edge handles perform 1D resizing along the respective axis.
- Multi-selection displays a composite bounding box allowing collective movement and alignment.
