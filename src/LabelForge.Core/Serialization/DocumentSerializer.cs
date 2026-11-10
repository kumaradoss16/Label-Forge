namespace LabelForge.Core.Serialization;

using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using LabelForge.Core.Exceptions;
using LabelForge.Core.Geometry;
using LabelForge.Core.Models;

/// <summary>
/// Serializes and deserializes LabelForge .olb documents to and from versioned polymorphic JSON.
/// </summary>
public sealed class DocumentSerializer
{
    private readonly JsonSerializerOptions _options;

    public DocumentSerializer()
    {
        _options = CreateDefaultOptions();
    }

    public static JsonSerializerOptions CreateDefaultOptions()
    {
        var options = new JsonSerializerOptions
        {
            WriteIndented = true,
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            PropertyNameCaseInsensitive = true
        };

        options.Converters.Add(new JsonStringEnumConverter());
        options.Converters.Add(new LengthJsonConverter());
        return options;
    }

    /// <summary>
    /// Serializes a LabelDocument into formatted JSON string.
    /// </summary>
    public string Serialize(LabelDocument document)
    {
        ArgumentNullException.ThrowIfNull(document);
        return JsonSerializer.Serialize(document, _options);
    }

    /// <summary>
    /// Serializes a LabelDocument into a stream.
    /// </summary>
    public void Serialize(LabelDocument document, Stream destinationStream)
    {
        ArgumentNullException.ThrowIfNull(document);
        ArgumentNullException.ThrowIfNull(destinationStream);
        JsonSerializer.Serialize(destinationStream, document, _options);
    }

    /// <summary>
    /// Deserializes a LabelDocument from a JSON string with format version validation.
    /// </summary>
    public LabelDocument Deserialize(string json)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            throw new DocumentCorruptException("Document JSON payload is empty.");
        }

        try
        {
            // Validate version header before full deserialization
            ValidateFormatVersion(json);

            var document = JsonSerializer.Deserialize<LabelDocument>(json, _options);
            if (document == null)
            {
                throw new DocumentCorruptException("Failed to deserialize document: resulting object was null.");
            }

            return document;
        }
        catch (UnsupportedSchemaVersionException)
        {
            throw;
        }
        catch (JsonException ex)
        {
            throw new DocumentCorruptException($"Document JSON structure is invalid or corrupted: {ex.Message}", ex);
        }
        catch (Exception ex) when (ex is not DocumentCorruptException)
        {
            throw new DocumentCorruptException($"Unexpected error reading document: {ex.Message}", ex);
        }
    }

    /// <summary>
    /// Deserializes a LabelDocument from a stream with format version validation.
    /// </summary>
    public LabelDocument Deserialize(Stream stream)
    {
        ArgumentNullException.ThrowIfNull(stream);

        using var reader = new StreamReader(stream, leaveOpen: true);
        var json = reader.ReadToEnd();
        return Deserialize(json);
    }

    private static void ValidateFormatVersion(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;

            if (root.ValueKind != JsonValueKind.Object)
            {
                throw new DocumentCorruptException("Document root must be a JSON object.");
            }

            string? version = null;
            if (root.TryGetProperty("formatVersion", out var versionProp) ||
                root.TryGetProperty("FormatVersion", out versionProp))
            {
                version = versionProp.GetString();
            }

            if (string.IsNullOrWhiteSpace(version))
            {
                throw new DocumentCorruptException("Document is missing the mandatory 'formatVersion' identifier.");
            }

            // Check version compatibility (Only 1.x is supported in 1.0)
            if (version != LabelDocument.CurrentFormatVersion)
            {
                // Parse major version
                var parts = version.Split('.');
                if (parts.Length > 0 && int.TryParse(parts[0], out var major))
                {
                    if (major > 1)
                    {
                        throw new UnsupportedSchemaVersionException(version, LabelDocument.CurrentFormatVersion);
                    }
                }
                else
                {
                    throw new UnsupportedSchemaVersionException(version, LabelDocument.CurrentFormatVersion);
                }
            }
        }
        catch (JsonException ex)
        {
            throw new DocumentCorruptException($"Unable to parse document JSON header: {ex.Message}", ex);
        }
    }
}
