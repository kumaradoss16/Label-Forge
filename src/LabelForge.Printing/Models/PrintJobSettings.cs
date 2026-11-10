namespace LabelForge.Printing.Models;

/// <summary>
/// Execution parameters for dispatching print jobs to Windows spooler or raw printer ports.
/// </summary>
public sealed class PrintJobSettings
{
    public string PrinterName { get; set; } = string.Empty;
    public int Copies { get; set; } = 1;
    public int SerializedCopies { get; set; } = 1;
    public bool Collate { get; set; } = true;
    public string JobTitle { get; set; } = "LabelForge Print Job";
    public bool UseRawPrinterCommands { get; set; } = false;
    public int StartRecordIndex { get; set; } = 0;
    public int RecordCount { get; set; } = int.MaxValue;
}
