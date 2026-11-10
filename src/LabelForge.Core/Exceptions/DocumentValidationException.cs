namespace LabelForge.Core.Exceptions;

using LabelForge.Core.Validation;

/// <summary>
/// Exception thrown when a document fails domain validation rules.
/// </summary>
public sealed class DocumentValidationException : Exception
{
    public ValidationResult Result { get; }

    public DocumentValidationException(ValidationResult result)
        : base($"Document validation failed with {result.Errors.Count} error(s): {string.Join("; ", result.Errors.Select(e => e.Message))}")
    {
        Result = result;
    }
}
