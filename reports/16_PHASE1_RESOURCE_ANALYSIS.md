# Phase 1: Resource & UI Asset Investigation

**Target:** Seagull Scientific BarTender Designer 11.4  
**Audit Scope:** Embedded PE Resources in `BarTend.exe` and External Application Assets  
**Classification:** `[VERIFIED_STATIC]` via Resource Enumeration and Decompiled CHM Inspection  

---

## 1. Embedded PE Resources (`.rsrc` Section)

The `.rsrc` section of `BarTend.exe` measures **3,835,392 bytes** (3.65 MB) at virtual address `0x106f000`:

| Resource Type | Resource ID / Name | Description & Usage |
| :--- | :--- | :--- |
| **`RT_ICON` / `RT_GROUP_ICON`** | `IDI_MAINFRAME`, `IDI_DOCUMENT` | Application icons (16x16 up to 256x256 PNG-compressed icons) |
| **`RT_DIALOG`** | `IDD_PAGESETUP`, `IDD_OBJ_PROPERTIES` | Win32 MFC modal dialog templates (Page Setup, Text Properties, Barcode Properties) |
| **`RT_MENU`** | `IDR_MAINFRAME`, `IDR_LABEL_DOC` | Fallback Win32 menus used prior to Codejock Ribbon initialization |
| **`RT_ACCELERATOR`** | `IDR_ACCELERATOR` | Standard Windows keyboard accelerators (`Ctrl+N`, `Ctrl+O`, `Ctrl+S`, `Ctrl+P`, `F5`) |
| **`RT_STRING`** | String Tables (Blocks 1..120) | UI error messages, command tooltips, status bar prompts |
| **`RT_MANIFEST`** | Manifest ID `1` | Per-Monitor V2 DPI awareness, Windows 10/11 Common Controls v6 |
| **`RT_VERSION`** | `VS_VERSION_INFO` | Build `11.4.238.365`, Copyright Seagull Scientific |

---

## 2. External Documentation & UI Reference Assets

From `D:\BarTender\Help\BarTender.chm`, **83 official high-resolution reference UI graphics and dialog screenshots** were extracted to `screenshots/`:

1. **Main Designer Canvas (`screenshots/Canvas_Example.png`):**
   - Shows active label canvas, horizontal and vertical rulers in inches/mm, and snap-to-grid indicators.
2. **Design Object Toolbox (`screenshots/AllObjects.png`):**
   - Documents the complete inventory of visual design objects: Single-line Text, Multi-line Text, 1D Barcodes, 2D Matrix Codes, Shapes (Rectangles, Rounded Rectangles, Ellipses, Lines), Pictures, and Tables.
3. **Object Reference Points (`screenshots/ObjectReferencePoints.png`):**
   - Illustrates the 9-point reference anchor system (Top-Left, Top-Center, Top-Right, Center-Left, Center, Center-Right, Bottom-Left, Bottom-Center, Bottom-Right) controlling object expansion and rotational origins.
4. **Data Source Integration (`screenshots/ObjectValueSource.gif`):**
   - Documents the 5 primary data source types: Embedded Data, Clock / Timestamp, Database Field, Serial Number (Counter), and Visual Basic Script Expression.

---

## 3. Clean-Room Asset Compliance Boundary

In strict compliance with Clean-Room engineering rules:

- **Zero Asset Duplication:** No copyrighted icons, proprietary graphics, or trademarked logos from BarTender are copied or embedded into `LabelForge`.
- **Reference-Only Use:** Extracted screenshots serve strictly as observable behavioral specifications to ensure functional equivalence.
- **Independent Design System:** `LabelForge` uses custom modern vector iconography and standard Microsoft Fluent / WPF vector styling.
