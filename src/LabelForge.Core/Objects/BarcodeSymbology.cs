namespace LabelForge.Core.Objects;

/// <summary>
/// Supported 1D and 2D barcode symbologies.
/// </summary>
public enum BarcodeSymbology
{
    Code128 = 0,
    Code39 = 1,
    Code93 = 2,
    Ean13 = 3,
    Ean8 = 4,
    UpcA = 5,
    UpcE = 6,
    Interleaved2Of5 = 7,
    Codabar = 8,
    QrCode = 100,
    MicroQrCode = 101,
    DataMatrix = 102,
    Aztec = 103,
    Pdf417 = 104,
    UspsIntelligentMail = 200
}

/// <summary>
/// Placement of human-readable text relative to barcode symbology.
/// </summary>
public enum HumanReadablePlacement
{
    None = 0,
    Below = 1,
    Above = 2,
    Embedded = 3
}

/// <summary>
/// Text horizontal alignment.
/// </summary>
public enum TextAlignment
{
    Left = 0,
    Center = 1,
    Right = 2,
    Justify = 3
}

/// <summary>
/// Reference point anchor for object transformations and growth.
/// </summary>
public enum AnchorPoint
{
    TopLeft = 0,
    TopCenter = 1,
    TopRight = 2,
    CenterLeft = 3,
    Center = 4,
    CenterRight = 5,
    BottomLeft = 6,
    BottomCenter = 7,
    BottomRight = 8
}
