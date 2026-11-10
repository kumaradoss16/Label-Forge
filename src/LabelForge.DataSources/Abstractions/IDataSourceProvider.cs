namespace LabelForge.DataSources.Abstractions;

/// <summary>
/// Contract for external data source connectors (CSV, Excel, Database, JSON, Embedded).
/// </summary>
public interface IDataSourceProvider
{
    string ProviderId { get; }
    string DisplayName { get; }

    /// <summary>
    /// Tests connection parameters.
    /// </summary>
    Task<bool> TestConnectionAsync(string connectionString, CancellationToken cancellationToken = default);

    /// <summary>
    /// Opens and returns a record set for reading.
    /// </summary>
    Task<IRecordSet> OpenRecordSetAsync(string connectionString, string? queryOrTable = null, CancellationToken cancellationToken = default);
}
