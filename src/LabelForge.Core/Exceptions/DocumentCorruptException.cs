namespace LabelForge.Core.Exceptions;

/// <summary>
/// Exception thrown when document file bytes are malformed, unreadable, or missing critical root elements.
/// </summary>
public sealed class DocumentCorruptException : Exception
{
    public DocumentCorruptException(string message)
        : base(message)
    {
    }

    public DocumentCorruptException(string message, Exception innerException)
        : base(message, innerException)
    {
    }
}
