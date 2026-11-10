namespace LabelForge.Core.Validation;

public enum ValidationSeverity
{
    Error,
    Warning,
    Info
}

public sealed record ValidationError(
    string PropertyPath,
    string Message,
    ValidationSeverity Severity = ValidationSeverity.Error);
