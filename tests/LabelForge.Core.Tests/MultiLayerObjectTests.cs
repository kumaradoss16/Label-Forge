namespace LabelForge.Core.Tests;

using FluentAssertions;
using LabelForge.Core.Geometry;
using LabelForge.Core.Models;
using LabelForge.Core.Objects;
using Xunit;

public class MultiLayerObjectTests
{
    [Fact]
    public void MultiLayer_SupportsOrderingAndObjectLookup()
    {
        var doc = new LabelDocument();

        var layerBg = new Layer("Background", zIndex: 0);
        var layerContent = new Layer("Content", zIndex: 10);
        var layerOverlay = new Layer("Overlay", zIndex: 20);

        var bgShape = new ShapeObject { Name = "BackgroundBorder" };
        var titleText = new TextObject { Name = "TitleLabel", Text = "Inventory Tag" };
        var barcode = new BarcodeObject { Name = "PrimaryBarcode", Data = "INV-001" };
        var confidentialWatermark = new TextObject { Name = "Watermark", Text = "CONFIDENTIAL" };

        layerBg.Objects.Add(bgShape);
        layerContent.Objects.Add(titleText);
        layerContent.Objects.Add(barcode);
        layerOverlay.Objects.Add(confidentialWatermark);

        doc.Layers.Add(layerBg);
        doc.Layers.Add(layerContent);
        doc.Layers.Add(layerOverlay);

        doc.AllObjects.Should().HaveCount(4);

        // Find by name
        var foundBarcode = doc.FindObjectByName("PrimaryBarcode");
        foundBarcode.Should().NotBeNull();
        foundBarcode.Should().BeSameAs(barcode);

        // Find by ID
        var foundTitle = doc.FindObjectById(titleText.Id);
        foundTitle.Should().NotBeNull();
        foundTitle.Should().BeSameAs(titleText);

        // Case insensitive lookup
        doc.FindObjectByName("watermark").Should().BeSameAs(confidentialWatermark);
    }
}
