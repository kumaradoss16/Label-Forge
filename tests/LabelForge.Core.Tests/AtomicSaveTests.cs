namespace LabelForge.Core.Tests;

using FluentAssertions;
using LabelForge.Core.Exceptions;
using LabelForge.Core.Geometry;
using LabelForge.Core.Models;
using LabelForge.Core.Objects;
using LabelForge.Core.Serialization;
using Xunit;

public class AtomicSaveTests : IDisposable
{
    private readonly string _testDir;
    private readonly AtomicFileOperations _fileOps = new();

    public AtomicSaveTests()
    {
        _testDir = Path.Combine(Path.GetTempPath(), "LabelForgeTests_" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(_testDir);
    }

    public void Dispose()
    {
        try
        {
            if (Directory.Exists(_testDir))
            {
                Directory.Delete(_testDir, recursive: true);
            }
        }
        catch
        {
            // Best effort cleanup
        }
    }

    [Fact]
    public void SaveAtomic_CreatesValidOlbFile_CanBeReloadedIdentically()
    {
        var targetFile = Path.Combine(_testDir, "ShippingLabel.olb");
        var doc = LabelDocument.CreateDefault("Atomic Save Verification");
        doc.Layers[0].Objects.Add(new TextObject { Text = "Test Atomic Content" });

        _fileOps.SaveAtomic(doc, targetFile);

        File.Exists(targetFile).Should().BeTrue();

        var reloaded = _fileOps.Load(targetFile);
        reloaded.Id.Should().Be(doc.Id);
        reloaded.Info.Title.Should().Be("Atomic Save Verification");
        reloaded.Layers[0].Objects.Should().HaveCount(1);
        reloaded.Layers[0].Objects[0].Should().BeOfType<TextObject>().Which.Text.Should().Be("Test Atomic Content");
    }

    [Fact]
    public void SaveAtomic_WhenDocumentInvalid_AbortsWithoutCorruptingExistingFile()
    {
        var targetFile = Path.Combine(_testDir, "ExistingLabel.olb");
        var originalDoc = LabelDocument.CreateDefault("Original Valid");
        _fileOps.SaveAtomic(originalDoc, targetFile);

        var originalContent = File.ReadAllText(targetFile);

        // Create invalid document
        var invalidDoc = LabelDocument.CreateDefault("Corrupted Attempt");
        invalidDoc.PageSetup.Width = Length.FromMillimeters(-50); // Invalid!

        var act = () => _fileOps.SaveAtomic(invalidDoc, targetFile, validateBeforeSave: true);
        act.Should().Throw<DocumentValidationException>();

        // Verify original file is untouched
        var remainingContent = File.ReadAllText(targetFile);
        remainingContent.Should().Be(originalContent);
    }
}
