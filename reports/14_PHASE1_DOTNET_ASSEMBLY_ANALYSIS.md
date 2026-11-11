# Phase 1: .NET Assembly & Metadata Investigation

**Target:** Seagull Scientific BarTender Designer 11.4 Managed Components  
**Investigation Tools:** REA MCP Server (`inspect_managed_artifact`, `inspect_managed_native_boundaries`)  
**Target CLR:** .NET Framework 4.8 (`v4.0.30319`)  
**Classification:** `[VERIFIED_STATIC]`  

---

## 1. Managed Assembly Metadata Overview

Static extraction from `BarTend.exe` CLI metadata tables:

| Metadata Table | Rows | Significance |
| :--- | :--- | :--- |
| **`TypeDef`** | `2,421` | Declared managed and mixed C++/CLI types |
| **`TypeRef`** | `1,034` | External referenced types from .NET framework and Seagull assemblies |
| **`MethodDef`** | `17,547` | Method implementations (both IL and mixed native thunks) |
| **`MemberRef`** | `4,179` | Referenced external methods and properties |
| **`Field`** | `17,769` | Declared fields and static constants |
| **`ImplMap`** | `662` | P/Invoke mappings to native Win32/MFC functions |
| **`ClassLayout`** | `2,210` | Explicit struct layouts marshaled across the native/managed boundary |
| **`AssemblyRef`** | `84` | External managed assemblies linked at compile time |

---

## 2. Native Interoperability & P/Invoke Boundaries

REA `inspect_managed_native_boundaries` reveals how BarTender crosses the unmanaged/managed boundary:

```
[Managed .NET Presentation / UI Layer]
         │
         ▼  (P/Invoke via ImplMap & C++/CLI Thunks)
┌────────────────────────────────────────────────────────┐
│ 1. CDialog.DoModal        → Modal Dialog Loop (Win32)  │
│ 2. CArchive.Write / Read  → Binary Stream I/O (MFC)    │
│ 3. CObList.AddTail        → Document Object Graph      │
│ 4. CWnd.CreateControl     → Native Window Embedding    │
│ 5. SysAllocString         → COM BSTR Memory Marshaling │
└────────────────────────────────────────────────────────┘
         │
         ▼
[Unmanaged MFC / Native C++ x64 Engine]
```

### 2.1 Critical MFC Boundaries Identified

1. **`CArchive.WriteCount` & `CArchive.ReadCount` (Tokens `0x06002c7e`, `0x06002c7f`):**
   - Implements MFC schema-versioned object stream serialization.
   - *Finding:* Proves `.btw` is an MFC serialization format rather than open XML or JSON.
2. **`CObList.AddTail` & `CObList.RemoveAll` (Tokens `0x06002cd6`, `0x06002ce6`):**
   - Manages lists of label objects (`CDesignObject`).
3. **`CWnd.CreateControl`, `ShowWindow`, `SetWindowPos` (Tokens `0x06002d43`, `0x06002d47`, `0x06002d46`):**
   - Coordinates window layout and controls within the designer canvas.
4. **`AfxmEnsureManagedInitialization` (Token `0x06002d44`):**
   - Standard MSVC mixed-mode initialization ensuring CLR AppDomain is bound before MFC window creation.

---

## 3. Key Seagull Managed Assemblies

Inspection of `D:\BarTender\` identifies 331 managed assemblies. The core application logic resides in:

1. **`Seagull.BarTender.Print.dll`:**
   - Exposes `Seagull.BarTender.Print.Engine`, `LabelFormatDocument`, and `Printers`.
   - Primary programmatic API for label printing automation.
2. **`Seagull.Data.dll`:**
   - Implements delimited text reader (`TextReaderRecordSet`), serialization counters, and field token replacement (`[Field_Name]`).
3. **`Seagull.Database.dll`:**
   - Wraps ADO.NET and OLEDB connections to external databases.
4. **`Seagull.Licensing.dll`:**
   - Enforces Seagull License Server (SLS) heartbeats and feature entitlement checks.

---

## 4. Architectural Implications for Label-Forge

- **Zero Mixed-Mode Complexity:** BarTender's reliance on C++/CLI and MFC introduces fragile runtime boundaries and Windows-only legacy dependencies.
- **Pure Managed Core:** LabelForge avoids all mixed-mode overhead by implementing `LabelForge.Core` in **pure C# 12 / .NET 8**, eliminating P/Invoke marshalling bugs and ensuring cross-platform portability.
- **Open Document Model:** Instead of opaque `CArchive` binary streams, LabelForge uses **human-readable polymorphic JSON** (`.olb`) via `System.Text.Json`.
