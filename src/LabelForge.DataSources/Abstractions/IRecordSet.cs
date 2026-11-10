namespace LabelForge.DataSources.Abstractions;

/// <summary>
/// Represents an in-memory or streamed record set from an external data source.
/// </summary>
public interface IRecordSet : IDisposable
{
    /// <summary>
    /// Available field names in the record set.
    /// </summary>
    IReadOnlyList<string> FieldNames { get; }

    /// <summary>
    /// Total record count if known, or -1 for unbounded streams.
    /// </summary>
    long TotalRecords { get; }

    /// <summary>
    /// Advances to the next record. Returns false when exhausted.
    /// </summary>
    bool ReadNext();

    /// <summary>
    /// Gets the string value of a field for the current record.
    /// </summary>
    string? GetFieldValue(string fieldName);
}
