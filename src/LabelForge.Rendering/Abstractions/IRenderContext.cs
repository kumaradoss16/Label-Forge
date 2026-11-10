namespace LabelForge.Rendering.Abstractions;

using LabelForge.Core.Geometry;

/// <summary>
/// Abstraction for a drawing surface / render target (WPF DrawingContext, SkiaCanvas, PDF, or DirectPrint).
/// </summary>
public interface IRenderContext
{
    /// <summary>
    /// DPI of the current rendering context (e.g. 96 for screen, 203/300/600 for thermal printers).
    /// </summary>
    double DpiX { get; }
    double DpiY { get; }

    /// <summary>
    /// Current zoom scale factor (1.0 = 100%).
    /// </summary>
    double ZoomFactor { get; }

    /// <summary>
    /// Converts a physical length to render target pixels based on current DPI and zoom.
    /// </summary>
    double ToPixelsX(Length length);
    double ToPixelsY(Length length);
}
