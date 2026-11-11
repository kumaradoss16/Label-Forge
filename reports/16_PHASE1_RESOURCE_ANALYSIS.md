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

From `D:\BarTender\Help\BarTender.chm`, 83 official reference UI graphics and dialog assets were audited for functional behavior analysis:
- 25 dialog templates and layouts (Page Setup, Print Setup, Database Setup, Serialization)
- 58 visual UI icons and toolbar elements

### 2.1 Behavioral Synthesis (Preserved Independently)
All functional behavior, layout geometry, coordinate origins, and adorner manipulation rules observed from these assets have been synthesized into **independent, clean-room textual specifications** in:
- [`screenshots/UI_OBSERVATIONS_REFERENCE.md`](file:///E:/ReverseEngineering/Label-Forge-clone/screenshots/UI_OBSERVATIONS_REFERENCE.md)
- [`reports/05_UI_REFERENCE_SPECIFICATION.md`](file:///E:/ReverseEngineering/Label-Forge-clone/reports/05_UI_REFERENCE_SPECIFICATION.md)

---

## 3. Clean-Room Asset Compliance & Copyright Enforcement

> [!CAUTION]
> **Mandatory Legal Boundary & Asset Removal:**
> 
> 1. **Zero Proprietary Binary Distribution:** In accordance with copyright law and clean-room engineering guidelines, all 40 extracted proprietary graphic assets (PNGs, GIFs, JPEGs) previously located in `screenshots/` have been **permanently deleted from repository version control**.
> 2. **Analytical Metadata Only:** The repository retains only non-infringing structural metadata, coordinate models, and independently written observational logs.
> 3. **Clean-Room Implementation:** Label-Forge must use original vector icons (e.g., custom XAML vector geometries or open-source permissive icon sets) and modern WPF MVVM controls.
