namespace LabelForge.Core.Validation;

public sealed class ValidationResult
{
    private readonly List<ValidationError> _errors = [];

    public IReadOnlyList<ValidationError> Errors => _errors;

    public bool IsValid => _errors.All(e => e.Severity != ValidationSeverity.Error);

    public static ValidationResult Success => new();

    public void AddError(string propertyPath, string message)
    {
        _errors.Add(new ValidationError(propertyPath, message, ValidationSeverity.Error));
    }

    public void AddWarning(string propertyPath, string message)
    {
        _errors.Add(new ValidationError(propertyPath, message, ValidationSeverity.Warning));
    }

    public void AddInfo(string propertyPath, string message)
    {
        _errors.Add(new ValidationError(propertyPath, message, ValidationSeverity.Info));
    }

    public void Merge(ValidationResult other)
    {
        _errors.AddRange(other.Errors);
    }
}
