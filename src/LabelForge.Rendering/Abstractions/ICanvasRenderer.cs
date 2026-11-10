namespace LabelForge.Rendering.Abstractions;

using LabelForge.Core.Models;
using LabelForge.Core.Objects;

/// <summary>
/// Core contract for rendering LabelForge documents and individual canvas objects.
/// </summary>
public interface ICanvasRenderer
{
    /// <summary>
    /// Renders an entire label document onto the target render context.
    /// </summary>
    void RenderDocument(LabelDocument document, IRenderContext context);

    /// <summary>
    /// Renders an individual canvas object onto the target render context.
    /// </summary>
    void RenderObject(CanvasObject obj, IRenderContext context);
}
