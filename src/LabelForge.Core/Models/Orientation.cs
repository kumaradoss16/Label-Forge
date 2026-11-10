namespace LabelForge.Core.Models;

/// <summary>
/// Specifies the orientation of the label or physical media.
/// </summary>
public enum LabelOrientation
{
    Portrait = 0,
    Landscape = 1,
    Portrait180 = 2,
    Landscape180 = 3
}

/// <summary>
/// Specifies the geometric contour of the label die-cut shape.
/// </summary>
public enum LabelShape
{
    Rectangle = 0,
    RoundedRectangle = 1,
    Ellipse = 2,
    Circle = 3
}
