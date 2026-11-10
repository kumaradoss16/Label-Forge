namespace LabelForge.Core.Models;

/// <summary>
/// Predefined or custom label stock metadata (e.g., Avery 5160, Zebra 4x6).
/// </summary>
public sealed class LabelStock
{
    public string Name { get; set; } = "Custom";
    public string Manufacturer { get; set; } = "User Defined";
    public string PartNumber { get; set; } = string.Empty;
    public string Category { get; set; } = "General";
    public bool IsContinuousRoll { get; set; } = false;

    public static LabelStock Custom => new()
    {
        Name = "Custom",
        Manufacturer = "Custom",
        PartNumber = "CUSTOM-01"
    };

    public static LabelStock StandardShipping4x6 => new()
    {
        Name = "Shipping 4x6",
        Manufacturer = "Standard Thermal",
        PartNumber = "TH-4060",
        Category = "Shipping",
        IsContinuousRoll = true
    };
}
