namespace LabelForge.Core.Objects;

using LabelForge.Core.Geometry;

/// <summary>
/// Represents a 1D linear or 2D matrix barcode object placed on a label.
/// </summary>
public sealed class BarcodeObject : CanvasObject
{
    public BarcodeSymbology Symbology { get; set; } = BarcodeSymbology.Code128;

    /// <summary>
    /// Encoded payload data or expression.
    /// </summary>
    public string Data { get; set; } = "12345678";

    /// <summary>
    /// Nominal narrow bar / module width in mils (1 mil = 1/1000 inch).
    /// Typically 5 to 20 mils.
    /// </summary>
    public double XDimensionMils { get; set; } = 10.0;

    /// <summary>
    /// Nominal bar height for 1D barcodes. For 2D barcodes, height is dictated by module matrix.
    /// </summary>
    public Length BarHeight { get; set; } = Length.FromMillimeters(12.0);

    /// <summary>
    /// Wide to narrow bar ratio (applicable for two-width symbologies like Code 39 or Interleaved 2 of 5).
    /// Typically 2.0 to 3.0.
    /// </summary>
    public double WideToNarrowRatio { get; set; } = 2.5;

    /// <summary>
    /// Error correction level (e.g. for QR Code 'L', 'M', 'Q', 'H', or Data Matrix levels).
    /// </summary>
    public string ErrorCorrectionLevel { get; set; } = "M";

    /// <summary>
    /// Human readable text interpretation settings.
    /// </summary>
    public HumanReadableOptions HumanReadable { get; set; } = new();

    /// <summary>
    /// Quiet zone margins surrounding the symbol.
    /// </summary>
    public QuietZoneOptions QuietZone { get; set; } = new();

    /// <summary>
    /// Color of bars / modules in hex format (e.g. "#000000").
    /// </summary>
    public string BarColorHex { get; set; } = "#000000";

    /// <summary>
    /// Background color in hex format (e.g. "#FFFFFF" or "Transparent").
    /// </summary>
    public string BackgroundColorHex { get; set; } = "#FFFFFF";

    public BarcodeObject()
    {
        Name = "Barcode 1";
        Width = Length.FromMillimeters(40.0);
        Height = Length.FromMillimeters(18.0);
    }
}
