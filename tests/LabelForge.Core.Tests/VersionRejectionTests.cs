namespace LabelForge.Core.Tests;

using FluentAssertions;
using LabelForge.Core.Exceptions;
using LabelForge.Core.Serialization;
using Xunit;

public class VersionRejectionTests
{
    private readonly DocumentSerializer _serializer = new();

    [Fact]
    public void UnsupportedMajorVersion_ThrowsUnsupportedSchemaVersionException()
    {
        var futureJson = """
        {
          "formatVersion": "2.0",
          "id": "11111111-1111-1111-1111-111111111111",
          "info": { "title": "Future Label" },
          "pageSetup": { "width": 100, "height": 150 },
          "layers": []
        }
        """;

        var act = () => _serializer.Deserialize(futureJson);

        var ex = act.Should().Throw<UnsupportedSchemaVersionException>().Which;
        ex.DetectedVersion.Should().Be("2.0");
        ex.SupportedVersion.Should().Be("1.0");
    }

    [Fact]
    public void MissingFormatVersion_ThrowsDocumentCorruptException()
    {
        var missingVersionJson = """
        {
          "id": "11111111-1111-1111-1111-111111111111",
          "info": { "title": "No Version" }
        }
        """;

        var act = () => _serializer.Deserialize(missingVersionJson);

        act.Should().Throw<DocumentCorruptException>()
           .WithMessage("*missing the mandatory 'formatVersion'*");
    }

    [Fact]
    public void CorruptedJsonSyntax_ThrowsDocumentCorruptException()
    {
        var malformedJson = "{ formatVersion: '1.0', NOT_VALID_JSON";

        var act = () => _serializer.Deserialize(malformedJson);

        act.Should().Throw<DocumentCorruptException>();
    }
}
