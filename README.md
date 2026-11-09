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
