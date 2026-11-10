# ADR-001: Canonical Physical Coordinate System

## Status
Accepted

## Context
Label design applications produce outputs for varied physical media and display devices. Screen previews render on raster displays (typically 96 DPI or standard high-DPI scaling), while industrial label printers operate at fixed hardware resolutions (e.g. 203.2 DPI / 8 dots per mm, 300 DPI / 12 dots per mm, or 600 DPI / 24 dots per mm).

In legacy systems such as BarTender, internal coordinates often suffer from confusion between device pixels, printer dots, twips, and millimeters, or couple the object model to GDI mapping modes.

To ensure high-precision placement and zero rounding drift across screens and printers, LabelForge requires a single, unambiguous canonical coordinate representation throughout its core domain model.

## Decision
1. **Canonical Metric Unit**: All coordinates, dimensions, margins, and line thicknesses in `LabelForge.Core` are stored internally in millimeters (`mm`) as 64-bit floating-point numbers (`double`) encapsulated within an immutable value type `Length`.
2. **Explicit Conversions**: `Length` exposes explicit factory methods (`FromMillimeters`, `FromInches`, `FromPoints`) and conversion properties (`Millimeters`, `Inches`, `Points`).
3. **Decoupled Rasterization**: Device pixel conversions are calculated only at the rendering/printing boundary using `Length.ToDevicePixels(dpi)` or `Length.ToScreenPixels()`. Neither the domain model nor serialization format ever stores raw pixel values.
4. **Serialization Precision**: In `.olb` files, lengths are serialized as clean metric numeric values with a dedicated converter, avoiding floating-point inaccuracies.

## Consequences
- **Positive**: Complete portability across 96 DPI monitors, 203 DPI thermal printers, 300 DPI laser engines, and 72 DPI PDF vectors without precision loss or DPI skew.
- **Positive**: Clean separation of domain logic from WPF (`System.Windows`) and GDI/DirectX drawing targets.
- **Trade-off**: Rendering engines must perform a float multiplication (`mm * dpi / 25.4`) when generating visual glyphs and paths.
