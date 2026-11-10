using LabelForge.Core.Geometry;

namespace LabelForge.Core.Objects;

/// <summary>
/// Configures human-readable text presentation for barcodes.
/// </summary>
public sealed class HumanReadableOptions : IEquatable<HumanReadableOptions>
{
    public bool IsVisible { get; set; } = true;

    public HumanReadablePlacement Placement { get; set; } = HumanReadablePlacement.Below;

    public string FontFamily { get; set; } = "Arial";

    public double FontSizePt { get; set; } = 9.0;

    public bool IsBold { get; set; }

    public bool IsItalic { get; set; }

    public Length MarginFromBarcode { get; set; } = Length.FromMillimeters(1.0);

    public bool Equals(HumanReadableOptions? other)
    {
        if (other is null) return false;
        if (ReferenceEquals(this, other)) return true;
        return IsVisible == other.IsVisible &&
               Placement == other.Placement &&
               FontFamily == other.FontFamily &&
               Math.Abs(FontSizePt - other.FontSizePt) < 1e-4 &&
               IsBold == other.IsBold &&
               IsItalic == other.IsItalic &&
               MarginFromBarcode == other.MarginFromBarcode;
    }

    public override bool Equals(object? obj) => Equals(obj as HumanReadableOptions);

    public override int GetHashCode() => HashCode.Combine(IsVisible, Placement, FontFamily, FontSizePt);
}

/// <summary>
/// Configures margin quiet zones surrounding barcode symbology.
/// </summary>
public sealed class QuietZoneOptions : IEquatable<QuietZoneOptions>
{
    public Length Left { get; set; } = Length.FromMillimeters(2.54); // 0.1 inch default

    public Length Right { get; set; } = Length.FromMillimeters(2.54);

    public Length Top { get; set; } = Length.Zero;

    public Length Bottom { get; set; } = Length.Zero;

    public bool Equals(QuietZoneOptions? other)
    {
        if (other is null) return false;
        if (ReferenceEquals(this, other)) return true;
        return Left == other.Left && Right == other.Right && Top == other.Top && Bottom == other.Bottom;
    }

    public override bool Equals(object? obj) => Equals(obj as QuietZoneOptions);

    public override int GetHashCode() => HashCode.Combine(Left, Right, Top, Bottom);
}
