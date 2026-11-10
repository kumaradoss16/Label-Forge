namespace LabelForge.Core.Models;

using LabelForge.Core.Geometry;

/// <summary>
/// Defines physical page dimensions, margins, orientation, and multi-label sheet layout.
/// </summary>
public sealed class PageSetup
{
    /// <summary>
    /// Total width of the individual label (or sheet if multi-label).
    /// Default: 101.6 mm (4 inches).
    /// </summary>
    public Length Width { get; set; } = Length.FromMillimeters(101.6);

    /// <summary>
    /// Total height of the individual label.
    /// Default: 152.4 mm (6 inches).
    /// </summary>
    public Length Height { get; set; } = Length.FromMillimeters(152.4);

    /// <summary>
    /// Orientation of the label design (Portrait or Landscape).
    /// </summary>
    public LabelOrientation Orientation { get; set; } = LabelOrientation.Portrait;

    /// <summary>
    /// Geometry shape of the label boundary (Rectangle, RoundedRectangle, Ellipse).
    /// </summary>
    public LabelShape Shape { get; set; } = LabelShape.Rectangle;

    /// <summary>
    /// Corner radius when Shape is RoundedRectangle.
    /// </summary>
    public Length CornerRadius { get; set; } = Length.Zero;

    /// <summary>
    /// Margins inside which printable content should reside.
    /// </summary>
    public Thickness2D Margins { get; set; } = Thickness2D.Zero;

    /// <summary>
    /// Associated label stock catalog entry.
    /// </summary>
    public LabelStock Stock { get; set; } = LabelStock.Custom;

    /// <summary>
    /// Number of labels across on a multi-label sheet or page.
    /// </summary>
    public int LabelsAcross { get; set; } = 1;

    /// <summary>
    /// Number of labels down on a multi-label sheet or page.
    /// </summary>
    public int LabelsDown { get; set; } = 1;

    /// <summary>
    /// Horizontal gap / pitch spacing between adjacent labels.
    /// </summary>
    public Length HorizontalGap { get; set; } = Length.Zero;

    /// <summary>
    /// Vertical gap / pitch spacing between adjacent labels.
    /// </summary>
    public Length VerticalGap { get; set; } = Length.Zero;

    /// <summary>
    /// Effective printable width accounting for left and right margins.
    /// </summary>
    public Length PrintableWidth => Width - Margins.Left - Margins.Right;

    /// <summary>
    /// Effective printable height accounting for top and bottom margins.
    /// </summary>
    public Length PrintableHeight => Height - Margins.Top - Margins.Bottom;
}
