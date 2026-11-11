# Label-Forge

An independent, clean-room Windows desktop label design and printing application engineered as a modern alternative with equivalent core capabilities to Seagull Scientific's BarTender Designer.

---

## Project Overview

**Label-Forge** is designed from the ground up using **C# 12 / .NET 8**, **WPF**, and **CommunityToolkit.Mvvm**. It provides an open, modern, high-DPI-aware desktop label design studio with:
* Native vector canvas with sub-millimeter precision, interactive rulers, snapping guides, and 8-point adorner manipulation.
* Full 1D & 2D barcode generation (Code 128, Code 39, QR Code, Data Matrix, EAN-13, UPC-A) via managed C# engines.
* Serialization counters and dynamic data evaluation (auto-incrementing, custom steps, zero-padding, rollover).
* Delimited text / CSV data binding and field mapping.
* Dual-path output architecture:
  * Universal Windows Spooler printing (GDI/XPS) for office, laser, and inkjet printers.
  * Direct high-speed industrial thermal printing via raw ASCII Zebra Programming Language (ZPL II) command streaming.
  * Native vector PDF export via QuestPDF.
* Zero proprietary dependencies: 100% clean-room architecture independent of proprietary MFC wrappers, Codejock, LEADTOOLS, or QuickPDF binaries.

---

## Investigation & Architecture Specifications

All technical specifications, reverse engineering reports, behavior models, and architectural blueprints produced during the investigation of BarTender 11.4 (`BarTend.exe`, build `11.4.238.365`) are documented in the [`reports/`](reports/) directory:

| Report | Description |
| :--- | :--- |
| [**01. Target Identity**](reports/01_TARGET_IDENTITY.md) | File hashes (MD5, SHA-256), PE x64 architecture, C++/CLI mixed-mode classification, manifest, and Authenticode signature. |
| [**02. Executable Analysis**](reports/02_EXECUTABLE_ANALYSIS.md) | Application startup sequence, MFC / Codejock UI shell, `.btw` binary structure, XML schemas, printing pipeline, and confirmed/inferred/unknown findings. |
| [**03. Dependency Map**](reports/03_DEPENDENCY_MAP.md) | Comprehensive audit of 48 native DLLs, 80+ managed assemblies, Windows services, and replacement mappings to modern open-source alternatives. |
| [**04. Component Architecture**](reports/04_COMPONENT_ARCHITECTURE.md) | Multi-tier architectural decomposition: DOM hierarchy, affine coordinate transformations, data evaluation pipeline, and design patterns. |
| [**05. UI Reference Specification**](reports/05_UI_REFERENCE_SPECIFICATION.md) | Detailed specification of main window layout, 9 menu hierarchies, 6 dockable toolbars, canvas, rulers, toolbox panes, and configuration dialogs. |
| [**06. Behavioural Specification**](reports/06_BEHAVIOURAL_SPECIFICATION.md) | State machines, hit-testing rules, drag/resize/rotate math, serialization counters, multi-label pagination, and error handling. |
| [**07. Feature Inventory**](reports/07_FEATURE_INVENTORY.md) | Classified inventory of 40+ observable features with verification tags (`[VERIFIED]`) and clean-room implementation feasibility. |
| [**07. Technical Architecture**](reports/07_TECHNICAL_ARCHITECTURE.md) | Complete engineering blueprint for the independent C# / WPF / MVVM replacement, POCO JSON document model (`.olb`), and dual print engines. |
| [**08. MVP Scope Specification**](reports/08_MVP_SCOPE.md) | Clear definition of in-scope MVP features vs. post-MVP capabilities, traceability matrix, and user story acceptance criteria. |
| [**08. Workflow Catalog**](reports/08_WORKFLOW_CATALOG.md) | 10 end-to-end operator reproduction workflows (page setup, barcodes, QR codes, serialization, CSV binding, printing). |
| [**09. Build Readiness Report**](reports/09_BUILD_READINESS_REPORT.md) | Engineering prerequisites, project hierarchy, NuGet package manifest, legal safeguards, and 5-milestone roadmap. |
| [**09. Runtime Evidence Report**](reports/09_RUNTIME_EVIDENCE.md) | Empirical runtime tests, service inspections, exception traces, visual screenshot evidence catalog, and file validations. |
| [**10. M0 & M1 Execution Report**](reports/10_M0_M1_EXECUTION_REPORT.md) | Completion report for M0 (Engineering Foundation) and M1 (Core Document Engine), domain model, geometry, and test validation. |
| [**11. Phase 1: Target Identity**](reports/11_PHASE1_TARGET_IDENTITY.md) | Confirmed executable identity, PE architecture, hashes, CLI headers, sections, and Authenticode signature. |
| [**12. Phase 1: Application Structure**](reports/12_PHASE1_APPLICATION_STRUCTURE.md) | Component inventory (24 EXEs, 331 managed DLLs, 102 native DLLs), subsystem boundaries, and architecture model. |
| [**13. Phase 1: Dependency Analysis**](reports/13_PHASE1_DEPENDENCY_ANALYSIS.md) | Complete audit of native imports, 84 managed AssemblyRefs, and clean-room replacement mappings. |
| [**14. Phase 1: .NET Assembly Analysis**](reports/14_PHASE1_DOTNET_ASSEMBLY_ANALYSIS.md) | CLI metadata tables (TypeDefs, MethodDefs), P/Invoke mappings (`CArchive`, `CObList`, `CWnd`), and managed core DLLs. |
| [**15. Phase 1: Native Binary Analysis**](reports/15_PHASE1_NATIVE_BINARY_ANALYSIS.md) | Native DLL inventory (`BtEngine.dll`, `BtBarcode.dll`, `BtPrint.dll`), exported functions, and tooling mitigations. |
| [**16. Phase 1: Resource Analysis**](reports/16_PHASE1_RESOURCE_ANALYSIS.md) | Win32 `.rsrc` section, dialog templates, string tables, extracted UI reference graphics, and clean-room asset boundary. |
| [**17. Phase 1: Runtime & Windows Integration**](reports/17_PHASE1_RUNTIME_AND_WINDOWS_INTEGRATION.md) | Empirical runtime tests, license enforcement exceptions, Windows Spooler GDI vs. raw thermal pass-through. |
| [**18. Phase 1: Feature Traceability**](reports/18_PHASE1_FEATURE_TRACEABILITY.md) | Comprehensive feature traceability matrix connecting BarTender evidence to LabelForge clean-room components. |
| [**19. Phase 1: Reverse Engineering Summary**](reports/19_PHASE1_REVERSE_ENGINEERING_SUMMARY.md) | Master Phase 1 summary, Gates A-G evaluation, confirmed facts, inferences, unknowns, and roadmap. |
| [**20. Phase 1.1: Evidence Reconciliation Report**](reports/20_PHASE1_1_EVIDENCE_RECONCILIATION.md) | Comprehensive 20-section authoritative baseline reconciliation, PE verification, and component census. |
| [**21. Phase 1.1: Correction Log & Register**](reports/21_PHASE1_1_CORRECTION_LOG.md) | Itemized audit log of historical claim corrections, discrepancy root causes, and justifications. |

---

## Architecture Decision Records (ADRs)

Key architectural choices are documented under [`docs/adr/`](docs/adr/):

* [**ADR-001: Canonical Physical Coordinate System**](docs/adr/ADR-001-canonical-physical-coordinate-system.md) — Double-precision millimeter (`mm`) physical coordinate system decoupled from screen and printer DPI.
* [**ADR-002: Versioned JSON Open Label (.olb) Document Format**](docs/adr/ADR-002-versioned-json-olb-document-format.md) — Open, human-readable, schema-versioned file format with atomic save and corruption protection.
* [**ADR-003: Domain Model Decoupling from UI and Output Runtimes**](docs/adr/ADR-003-domain-model-decoupling.md) — Pure .NET 8 core domain isolated from WPF, GDI, and printer spooler dependencies.

---

## Solution & Project Structure

```
LabelForge/
├── LabelForge.sln                    # Root solution file
├── Directory.Build.props              # Shared build settings (C# 12, Nullable, WarningsAsErrors)
├── nuget.config                      # Package source configuration
├── docs/adr/                         # Architecture Decision Records (ADR-001, ADR-002, ADR-003)
├── src/
│   ├── LabelForge.Core/              # Domain entities, geometry, validation, and JSON serialization (net8.0)
│   ├── LabelForge.Rendering/         # Canvas rendering abstractions and contracts (net8.0-windows)
│   ├── LabelForge.DataSources/       # External data connectors (CSV, database) contracts (net8.0)
│   ├── LabelForge.Printing/          # Windows spooler & direct printing contracts (net8.0-windows)
│   └── LabelForge.App/               # WPF Desktop Application Host & MVVM presentation (net8.0-windows)
└── tests/
    └── LabelForge.Core.Tests/        # Automated test suite (xUnit, FluentAssertions) (net8.0)
```

---

## Build and Test Instructions

### Prerequisites
* Windows 10/11 (x64)
* [.NET 8.0 SDK](https://dotnet.microsoft.com/download/dotnet/8.0) (v8.0.404 or newer)

### Build Solution
```powershell
dotnet build LabelForge.sln -c Release
```

### Run Automated Tests
```powershell
dotnet test tests/LabelForge.Core.Tests/LabelForge.Core.Tests.csproj -c Release
```

### Run Phase 1.1 Automated Evidence Validation
```powershell
python scripts/validate-phase1-evidence.py
# Or via PowerShell wrapper:
.\scripts\validate-phase1-evidence.ps1
```
*Deterministic exit codes:* `0` (PASS), `1` (FAIL), `2` (PREREQUISITE_ERROR).

### Launch Application
```powershell
dotnet run --project src/LabelForge.App/LabelForge.App.csproj -c Release
```

---

## Supporting Evidence & Screenshots

* [`evidence/`](evidence/): PE analysis summaries (`bartend_pe_summary.json`), imported symbol maps (`bartend_imports.json`), embedded manifest (`BarTend.exe.manifest`), and PowerShell diagnostic scripts.
* [`screenshots/`](screenshots/): 83 extracted official UI reference screenshots, dialog templates, toolbar diagrams, and workflow guides.

---

## Technology Stack

* **Platform:** .NET 8 LTS (C# 12) / Windows Desktop
* **UI Framework:** Windows Presentation Foundation (WPF) with `Fluent.Ribbon` and `Dirkster.AvalonDock`
* **MVVM:** `CommunityToolkit.Mvvm` (Source generators)
* **Barcode Engine:** `ZXing.Net` (Pure C# 1D/2D symbologies)
* **2D Graphics:** WPF `DrawingContext` & `SkiaSharp`
* **Data Sources:** `CsvHelper`, `Microsoft.Data.Sqlite`, `Dapper`
* **PDF Output:** `QuestPDF`
* **Industrial Thermal Printing:** Native ZPL II command builder over Windows Spooler (`RawPrinterHelper`)

---

## License & Compliance

This repository contains independent clean-room specifications and architectural documentation. It contains no proprietary source code, copyrighted binary executables, or protected commercial assets.
