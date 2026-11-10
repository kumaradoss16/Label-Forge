namespace LabelForge.Core.Objects;

using LabelForge.Core.Geometry;

public enum PictureSourceType
{
    EmbeddedBase64,
    FileReference,
    VariableExpression
}

public enum PictureSizingMode
{
    Stretch,
    PreserveAspectFit,
    PreserveAspectFill,
    Center
}

/// <summary>
/// Represents a static or dynamic raster image placed on the label.
/// </summary>
public sealed class PictureObject : CanvasObject
{
    public PictureSourceType SourceType { get; set; } = PictureSourceType.EmbeddedBase64;

    /// <summary>
    /// Base64 payload, file path URI, or variable expression.
    /// </summary>
    public string SourceData { get; set; } = string.Empty;

    /// <summary>
    /// Image format mime-type or file extension hint (e.g. "image/png").
    /// </summary>
    public string MimeType { get; set; } = "image/png";

    /// <summary>
    /// Sizing mode when rendering inside the bounding box.
    /// </summary>
    public PictureSizingMode SizingMode { get; set; } = PictureSizingMode.PreserveAspectFit;

    /// <summary>
    /// Brightness adjustment (-1.0 to 1.0, 0 = default).
    /// </summary>
    public double Brightness { get; set; } = 0.0;

    /// <summary>
    /// Contrast adjustment (-1.0 to 1.0, 0 = default).
    /// </summary>
    public double Contrast { get; set; } = 0.0;

    /// <summary>
    /// Whether to render in monochrome / threshold mode for direct thermal printers.
    /// </summary>
    public bool Monochrome { get; set; } = false;

    public PictureObject()
    {
        Name = "Picture 1";
        Width = Length.FromMillimeters(25.0);
        Height = Length.FromMillimeters(25.0);
    }
}
