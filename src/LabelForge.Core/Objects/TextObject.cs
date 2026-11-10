using LabelForge.Core.Geometry;

namespace LabelForge.Core.Objects;

/// <summary>
/// Represents a text label object supporting font styling, paragraph wrapping, and alignment.
/// </summary>
public sealed class TextObject : CanvasObject, IEquatable<TextObject>
{
    public TextObject()
    {
        Name = "Text 1";
    }

    public string Text { get; set; } = "Sample Text";

    public string FontFamily { get; set; } = "Segoe UI";

    public double FontSizePt { get; set; } = 12.0;

    [System.Text.Json.Serialization.JsonIgnore]
    public double FontSizePoints
    {
        get => FontSizePt;
        set => FontSizePt = value;
    }

    public bool IsBold { get; set; }

    [System.Text.Json.Serialization.JsonIgnore]
    public bool Bold
    {
        get => IsBold;
        set => IsBold = value;
    }

    public bool IsItalic { get; set; }

    public bool IsUnderline { get; set; }

    public bool IsStrikethrough { get; set; }

    public TextAlignment TextAlignment { get; set; } = TextAlignment.Left;

    public string ForegroundColorHex { get; set; } = "#000000";

    public bool WrapText { get; set; }

    public bool AutoFit { get; set; }

    public double LineSpacingRatio { get; set; } = 1.0;

    public bool Equals(TextObject? other)
    {
        if (!base.Equals(other)) return false;
        return Text == other.Text &&
               FontFamily == other.FontFamily &&
               Math.Abs(FontSizePt - other.FontSizePt) < 1e-4 &&
               IsBold == other.IsBold &&
               IsItalic == other.IsItalic &&
               IsUnderline == other.IsUnderline &&
               IsStrikethrough == other.IsStrikethrough &&
               TextAlignment == other.TextAlignment &&
               ForegroundColorHex == other.ForegroundColorHex &&
               WrapText == other.WrapText &&
               AutoFit == other.AutoFit &&
               Math.Abs(LineSpacingRatio - other.LineSpacingRatio) < 1e-4;
    }

    public override bool Equals(object? obj) => Equals(obj as TextObject);

    public override int GetHashCode() => HashCode.Combine(base.GetHashCode(), Text, FontFamily, FontSizePt);
}
