namespace LabelForge.Core.Models;

/// <summary>
/// Metadata describing the label document, author, creation timestamps, and comments.
/// </summary>
public sealed class DocumentInfo
{
    public string Title { get; set; } = "Untitled Label";
    public string Author { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Comments { get; set; } = string.Empty;
    public DateTimeOffset CreatedAtUtc { get; set; } = DateTimeOffset.UtcNow;
    public DateTimeOffset ModifiedAtUtc { get; set; } = DateTimeOffset.UtcNow;
    public string ApplicationName { get; set; } = "LabelForge";
    public string ApplicationVersion { get; set; } = "1.0.0";
}
