namespace LabelForge.Core.Models;

using System.Text.Json.Serialization;
using LabelForge.Core.Objects;

/// <summary>
/// Root domain aggregate representing an independent LabelForge label document.
/// </summary>
public sealed class LabelDocument
{
    /// <summary>
    /// Schema format version indicator. Version 1.0 is current.
    /// </summary>
    public const string CurrentFormatVersion = "1.0";

    /// <summary>
    /// Unique document instance identifier.
    /// </summary>
    public Guid Id { get; set; } = Guid.NewGuid();

    /// <summary>
    /// Document file schema format version.
    /// </summary>
    public string FormatVersion { get; set; } = CurrentFormatVersion;

    /// <summary>
    /// Document metadata and timestamps.
    /// </summary>
    public DocumentInfo Info { get; set; } = new();

    /// <summary>
    /// Page layout, label dimensions, margins, and stock settings.
    /// </summary>
    public PageSetup PageSetup { get; set; } = new();

    /// <summary>
    /// Visual layers containing design objects.
    /// </summary>
    public List<Layer> Layers { get; set; } = [];

    public LabelDocument()
    {
    }

    /// <summary>
    /// Creates a standard new label document with a default background layer.
    /// </summary>
    public static LabelDocument CreateDefault(string title = "New Label")
    {
        var doc = new LabelDocument();
        doc.Info.Title = title;
        doc.Layers.Add(new Layer("Background", 0));
        return doc;
    }

    /// <summary>
    /// Returns a flat sequence of all objects across all layers.
    /// </summary>
    [JsonIgnore]
    public IEnumerable<CanvasObject> AllObjects
        => Layers.SelectMany(l => l.Objects);

    /// <summary>
    /// Finds a canvas object by its stable identifier.
    /// </summary>
    public CanvasObject? FindObjectById(Guid id)
        => AllObjects.FirstOrDefault(o => o.Id == id);

    /// <summary>
    /// Finds a canvas object by its unique name (case-insensitive).
    /// </summary>
    public CanvasObject? FindObjectByName(string name)
        => AllObjects.FirstOrDefault(o => string.Equals(o.Name, name, StringComparison.OrdinalIgnoreCase));
}
