# ADR-003: Domain Model Decoupling from UI and Output Runtimes

## Status
Accepted

## Context
In legacy desktop tools like BarTender, document objects often inherit directly from GUI display controls or contain embedded printer driver handles (`DEVMODE`, GDI `HDC`, driver esc sequences). This tight coupling prevents headless batch printing, cross-platform cloud rendering, automated unit testing, and clean architecture boundaries.

## Decision
1. **Pure Domain Library (`LabelForge.Core`)**: The core domain package has zero dependencies on WPF (`PresentationCore`, `PresentationFramework`), WinForms, or Windows printing APIs. It targets clean `.NET 8.0` without Windows Desktop extensions.
2. **Abstract Rendering (`LabelForge.Rendering`)**: Visual rendering is abstracted behind `ICanvasRenderer` and `IRenderContext`. The core domain objects describe *what* is on the label, not *how* pixels are drawn.
3. **Abstract Data Sources (`LabelForge.DataSources`)**: External data integration is abstracted through `IDataSourceProvider` and `IRecordSet`, completely isolated from document definitions.
4. **Abstract Printing (`LabelForge.Printing`)**: Physical printing is managed by `IPrintEngine`, which receives a domain snapshot and printer settings, decoupling spooler interactions from label state.
5. **WPF UI Shell (`LabelForge.App`)**: The GUI application acts strictly as a presentation layer consuming domain models through MVVM and standard Dependency Injection (`Microsoft.Extensions.DependencyInjection`).

## Consequences
- **Positive**: 100% testable domain logic using standard unit test runners (`dotnet test`) without needing an active desktop UI or printer queue.
- **Positive**: Enables future headless CLI tools, web APIs, or Linux-based batch rendering services using the exact same `LabelForge.Core` library.
- **Positive**: Prevents proprietary vendor leaks or framework lock-in.
