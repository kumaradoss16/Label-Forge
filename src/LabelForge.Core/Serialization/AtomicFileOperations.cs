namespace LabelForge.Core.Serialization;

using LabelForge.Core.Exceptions;
using LabelForge.Core.Models;
using LabelForge.Core.Validation;

/// <summary>
/// Provides safe atomic file I/O operations for LabelForge (.olb) documents.
/// Prevents file corruption by writing to a temporary file before atomically swapping.
/// </summary>
public sealed class AtomicFileOperations
{
    public const string DefaultDocumentExtension = ".olb";
    private readonly DocumentSerializer _serializer;
    private readonly DocumentValidator _validator;

    public AtomicFileOperations(DocumentSerializer? serializer = null, DocumentValidator? validator = null)
    {
        _serializer = serializer ?? new DocumentSerializer();
        _validator = validator ?? new DocumentValidator();
    }

    /// <summary>
    /// Atomically saves a LabelDocument to disk at the designated file path.
    /// </summary>
    /// <param name="document">The document to save.</param>
    /// <param name="destinationPath">Target file path.</param>
    /// <param name="validateBeforeSave">If true, validates document before saving and aborts on error.</param>
    /// <param name="createBackup">If true and file exists, creates a .bak copy.</param>
    public void SaveAtomic(
        LabelDocument document,
        string destinationPath,
        bool validateBeforeSave = true,
        bool createBackup = false)
    {
        ArgumentNullException.ThrowIfNull(document);
        ArgumentException.ThrowIfNullOrWhiteSpace(destinationPath);

        if (validateBeforeSave)
        {
            var validationResult = _validator.Validate(document);
            if (!validationResult.IsValid)
            {
                throw new DocumentValidationException(validationResult);
            }
        }

        // Update modification timestamp
        document.Info.ModifiedAtUtc = DateTimeOffset.UtcNow;

        var fullPath = Path.GetFullPath(destinationPath);
        var dir = Path.GetDirectoryName(fullPath);
        if (!string.IsNullOrEmpty(dir))
        {
            Directory.CreateDirectory(dir);
        }

        var tempFilePath = Path.Combine(dir ?? string.Empty, $".{Path.GetFileName(fullPath)}.{Guid.NewGuid():N}.tmp");

        try
        {
            // Write to temporary file first
            using (var fs = new FileStream(tempFilePath, FileMode.CreateNew, FileAccess.Write, FileShare.None, 4096, FileOptions.WriteThrough))
            {
                _serializer.Serialize(document, fs);
                fs.Flush(flushToDisk: true);
            }

            // Atomically swap
            if (File.Exists(fullPath))
            {
                string? backupPath = createBackup ? fullPath + ".bak" : null;
                File.Replace(tempFilePath, fullPath, backupPath, ignoreMetadataErrors: true);
            }
            else
            {
                File.Move(tempFilePath, fullPath);
            }
        }
        catch
        {
            // Clean up temporary file on failure to leave working directory clean
            if (File.Exists(tempFilePath))
            {
                try { File.Delete(tempFilePath); } catch { /* best effort cleanup */ }
            }
            throw;
        }
    }

    /// <summary>
    /// Loads a LabelDocument from disk.
    /// </summary>
    public LabelDocument Load(string filePath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(filePath);

        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"Label document file not found: '{filePath}'", filePath);
        }

        using var fs = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.Read);
        return _serializer.Deserialize(fs);
    }
}
