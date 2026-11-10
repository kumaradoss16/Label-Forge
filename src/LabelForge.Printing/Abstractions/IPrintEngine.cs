namespace LabelForge.Printing.Abstractions;

using LabelForge.Core.Models;
using LabelForge.Printing.Models;

/// <summary>
/// Contract for printing LabelForge documents via Windows PrintDocument, XPS, or thermal raw streams.
/// </summary>
public interface IPrintEngine
{
    /// <summary>
    /// Gets list of available Windows installed printers.
    /// </summary>
    IReadOnlyList<string> GetInstalledPrinters();

    /// <summary>
    /// Gets the system default printer name.
    /// </summary>
    string? GetDefaultPrinter();

    /// <summary>
    /// Prints a label document using the specified settings.
    /// </summary>
    Task PrintDocumentAsync(LabelDocument document, PrintJobSettings settings, CancellationToken cancellationToken = default);
}
