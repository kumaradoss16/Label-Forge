namespace LabelForge.Core.Exceptions;

/// <summary>
/// Exception thrown when opening a document formatted with an unsupported or future schema version.
/// </summary>
public sealed class UnsupportedSchemaVersionException : Exception
{
    public string DetectedVersion { get; }
    public string SupportedVersion { get; }

    public UnsupportedSchemaVersionException(string detectedVersion, string supportedVersion)
        : base($"Document schema version '{detectedVersion}' is not supported. This application version supports up to schema '{supportedVersion}'.")
    {
        DetectedVersion = detectedVersion;
        SupportedVersion = supportedVersion;
    }
}
