# Phase 1: Resource & UI Asset Investigation

**Target:** Seagull Scientific BarTender Designer 11.4  
**Audit Scope:** Embedded PE Resources in `BarTend.exe` and External Application Assets  
**Classification:** `[VERIFIED_STATIC]` via Resource Enumeration and Decompiled CHM Inspection  
**Reconciled Baseline:** Phase 1.1 Authoritative Verification  

---

## 1. Embedded PE Resources (`.rsrc` Section)

The authoritative `.rsrc` section of `BarTend.exe` measures **1,264,272 bytes** (virtual size) / **1,264,640 bytes** (raw size) at virtual address `0x126e000` (file offset `0x122c600`):

| Resource Type | Resource ID / Name | Description & Usage | Status |
| :--- | :--- | :--- | :--- |
| **`RT_ICON` / `RT_GROUP_ICON`** | `IDI_MAINFRAME`, `IDI_DOCUMENT` | Application icons (16x16 up to 256x256 PNG-compressed icons) | `[VERIFIED_STATIC]` |
| **`RT_DIALOG`** | `IDD_PAGESETUP`, `IDD_OBJ_PROPERTIES` | Win32 MFC modal dialog templates (Page Setup, Text, Barcode) | `[VERIFIED_STATIC]` |
| **`RT_MENU`** | `IDR_MAINFRAME`, `IDR_LABEL_DOC` | Fallback Win32 menus prior to Codejock Ribbon initialization | `[VERIFIED_STATIC]` |
| **`RT_ACCELERATOR`** | `IDR_ACCELERATOR` | Standard Windows keyboard accelerators (`Ctrl+N`, `Ctrl+O`, `Ctrl+S`, `Ctrl+P`) | `[VERIFIED_STATIC]` |
| **`RT_STRING`** | String Tables (Blocks 1..120) | UI error messages, command tooltips, status bar prompts | `[VERIFIED_STATIC]` |
| **`RT_MANIFEST`** | Manifest ID `1` | Per-Monitor V2 DPI awareness, Windows Common Controls v6 | `[VERIFIED_STATIC]` |
| **`RT_VERSION`** | `VS_VERSION_INFO` | Build `11.4.238.365`, Copyright Seagull Scientific, LLC | `[VERIFIED_STATIC]` |

---

## 2. External Documentation & UI Reference Assets

From `D:\BarTender\Help\BarTender.chm`, **83 official reference UI graphics and dialog assets** were extracted for functional behavior analysis (including 40 curated files in `screenshots/`):

1. **Main Designer Canvas (`screenshots/Canvas_Example.png`):**
   - Shows active label canvas, horizontal and vertical rulers in inches/mm, and snap-to-grid indicators.
2. **Design Object Toolbox (`screenshots/AllObjects.png`):**
   - Documents visual design objects: Single-line Text, Multi-line Text, 1D Barcodes, 2D Matrix Codes, Shapes (Rectangles, Rounded Rectangles, Ellipses, Lines), Pictures, and Tables.
3. **Object Reference Points (`screenshots/ObjectReferencePoints.png`):**
   - Illustrates the 9-point reference anchor system (Top-Left, Top-Center, Top-Right, Center-Left, Center, Center-Right, Bottom-Left, Bottom-Center, Bottom-Right) controlling object expansion and rotational origins.
4. **Data Source Integration (`screenshots/ObjectValueSource.gif`):**
   - Documents the 5 primary data source types: Embedded Data, Clock / Timestamp, Database Field, Serial Number (Counter), and Visual Basic Script Expression.

---

## 3. Clean-Room Asset Compliance & Copyright Review

> [!CAUTION]
> **Mandatory Legal Boundary:** The extracted screenshots, CHM graphics, and dialog templates are copyrighted proprietary assets of Seagull Scientific, LLC.
> 
> 1. **No Binary Embedding:** No extracted BarTender bitmaps, PNGs, ICOs, or dialog templates may be bundled, embedded, or redistributed within the Label-Forge application, installer, or NuGet packages.
> 2. **Analytical Use Only:** Extracted media are strictly preserved under fair-use reverse-engineering doctrines to serve as an observable functional specification.
> 3. **Independent UI Implementation:** Label-Forge must implement its own UI using pure XAML, open-source or custom vector icons (e.g. Lucide/Material vector geometries), and modern WPF MVVM controls.
