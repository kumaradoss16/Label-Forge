namespace LabelForge.Core.Objects;

using LabelForge.Core.Geometry;

public enum ShapeType
{
    Rectangle,
    RoundedRectangle,
    Ellipse,
    Line
}

public enum StrokeStyle
{
    Solid,
    Dash,
    Dot,
    DashDot
}

/// <summary>
/// Represents geometric shapes (rectangles, rounded rectangles, ellipses, lines).
/// </summary>
public sealed class ShapeObject : CanvasObject
{
    public ShapeType ShapeType { get; set; } = ShapeType.Rectangle;

    /// <summary>
    /// Corner radius for rounded rectangles.
    /// </summary>
    public Length CornerRadius { get; set; } = Length.Zero;

    /// <summary>
    /// Outline border color in hex (e.g. "#000000").
    /// </summary>
    public string StrokeColorHex { get; set; } = "#000000";

    /// <summary>
    /// Outline thickness.
    /// </summary>
    public Length StrokeThickness { get; set; } = Length.FromMillimeters(0.5);

    /// <summary>
    /// Stroke style (Solid, Dash, Dot, DashDot).
    /// </summary>
    public StrokeStyle StrokeStyle { get; set; } = StrokeStyle.Solid;

    /// <summary>
    /// Interior fill color in hex (e.g. "Transparent", "#FFFFFF", "#FF0000").
    /// </summary>
    public string FillColorHex { get; set; } = "Transparent";

    public ShapeObject()
    {
        Name = "Shape 1";
        Width = Length.FromMillimeters(30.0);
        Height = Length.FromMillimeters(20.0);
    }
}
