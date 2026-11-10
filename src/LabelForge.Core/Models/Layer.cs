namespace LabelForge.Core.Models;

using System.Text.Json.Serialization;
using LabelForge.Core.Objects;

/// <summary>
/// Represents a discrete drawing layer on the label canvas containing design objects.
/// </summary>
public sealed class Layer
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public string Name { get; set; } = "Layer 1";

    public bool IsVisible { get; set; } = true;

    public bool IsLocked { get; set; } = false;

    public int ZIndex { get; set; } = 0;

    /// <summary>
    /// Conditional printing expression (e.g. for variable printing logic).
    /// </summary>
    public string? PrintWhenCondition { get; set; }

    /// <summary>
    /// Ordered list of objects residing on this layer.
    /// </summary>
    public List<CanvasObject> Objects { get; set; } = [];

    public Layer()
    {
    }

    public Layer(string name, int zIndex = 0)
    {
        Name = name;
        ZIndex = zIndex;
    }
}
