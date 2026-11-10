namespace LabelForge.Core.Tests;

using FluentAssertions;
using LabelForge.Core.Geometry;
using LabelForge.Core.Models;
using Xunit;

public class DocumentCreationTests
{
    [Fact]
    public void CreateDefault_ProducesStandardShipping4x6Label()
    {
        var doc = LabelDocument.CreateDefault("Test Shipping Label");

        doc.Id.Should().NotBeEmpty();
        doc.FormatVersion.Should().Be("1.0");
        doc.Info.Title.Should().Be("Test Shipping Label");
        doc.Info.ApplicationName.Should().Be("LabelForge");

        doc.PageSetup.Width.Millimeters.Should().BeApproximately(101.6, 0.01);
        doc.PageSetup.Height.Millimeters.Should().BeApproximately(152.4, 0.01);
        doc.PageSetup.Orientation.Should().Be(LabelOrientation.Portrait);

        doc.Layers.Should().HaveCount(1);
        doc.Layers[0].Name.Should().Be("Background");
        doc.Layers[0].IsVisible.Should().BeTrue();
        doc.Layers[0].IsLocked.Should().BeFalse();
        doc.Layers[0].Objects.Should().BeEmpty();
    }

    [Fact]
    public void EmptyDocument_HasValidStructure()
    {
        var doc = new LabelDocument();
        doc.Id.Should().NotBeEmpty();
        doc.Layers.Should().BeEmpty();
        doc.AllObjects.Should().BeEmpty();
    }
}
