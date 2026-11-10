namespace LabelForge.Core.Tests;

using FluentAssertions;
using LabelForge.Core.Geometry;
using LabelForge.Core.Models;
using LabelForge.Core.Objects;
using LabelForge.Core.Serialization;
using Xunit;

public class SerializationTests
{
    private readonly DocumentSerializer _serializer = new();

    [Fact]
    public void RoundTrip_EmptyDocument_PreservesAllProperties()
    {
        var doc = LabelDocument.CreateDefault("Shipping Master");
        doc.Info.Author = "Engineering Lead";

        var json = _serializer.Serialize(doc);
        json.Should().Contain("\"formatVersion\": \"1.0\"");
        json.Should().Contain("\"title\": \"Shipping Master\"");

        var roundTripped = _serializer.Deserialize(json);
        roundTripped.Id.Should().Be(doc.Id);
        roundTripped.FormatVersion.Should().Be("1.0");
        roundTripped.Info.Title.Should().Be("Shipping Master");
        roundTripped.Info.Author.Should().Be("Engineering Lead");
        roundTripped.PageSetup.Width.Millimeters.Should().BeApproximately(doc.PageSetup.Width.Millimeters, 0.0001);
    }

    [Fact]
    public void RoundTrip_AllObjectTypes_PolymorphicSerialization_PreservesDerivedTypes()
    {
        var doc = LabelDocument.CreateDefault("Comprehensive Sample");
        var layer = doc.Layers[0];

        // 1. TextObject
        var text = new TextObject
        {
            Name = "TitleText",
            Text = "PALLET ID: 9812",
            FontFamily = "Segoe UI",
            FontSizePoints = 16.0,
            Bold = true,
            X = Length.FromMillimeters(10),
            Y = Length.FromMillimeters(15),
            Width = Length.FromMillimeters(60),
            Height = Length.FromMillimeters(10)
        };
        layer.Objects.Add(text);

        // 2. BarcodeObject
        var barcode = new BarcodeObject
        {
            Name = "ShipmentBarcode",
            Symbology = BarcodeSymbology.Code128,
            Data = "PKG-88291039",
            XDimensionMils = 12.0,
            BarHeight = Length.FromMillimeters(18.0),
            X = Length.FromMillimeters(10),
            Y = Length.FromMillimeters(30),
            Width = Length.FromMillimeters(70),
            Height = Length.FromMillimeters(22)
        };
        layer.Objects.Add(barcode);

        // 3. ShapeObject
        var shape = new ShapeObject
        {
            Name = "BoundingBox",
            ShapeType = ShapeType.RoundedRectangle,
            CornerRadius = Length.FromMillimeters(3.0),
            StrokeThickness = Length.FromMillimeters(0.8),
            StrokeColorHex = "#1E293B",
            X = Length.FromMillimeters(5),
            Y = Length.FromMillimeters(5),
            Width = Length.FromMillimeters(90),
            Height = Length.FromMillimeters(140)
        };
        layer.Objects.Add(shape);

        // 4. PictureObject
        var pic = new PictureObject
        {
            Name = "CompanyLogo",
            SourceType = PictureSourceType.EmbeddedBase64,
            SourceData = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            SizingMode = PictureSizingMode.PreserveAspectFit,
            X = Length.FromMillimeters(70),
            Y = Length.FromMillimeters(10),
            Width = Length.FromMillimeters(20),
            Height = Length.FromMillimeters(15)
        };
        layer.Objects.Add(pic);

        var json = _serializer.Serialize(doc);

        // Verify polymorphic discriminator presence
        json.Should().Contain("\"$type\": \"text\"");
        json.Should().Contain("\"$type\": \"barcode\"");
        json.Should().Contain("\"$type\": \"shape\"");
        json.Should().Contain("\"$type\": \"picture\"");

        // Roundtrip
        var restored = _serializer.Deserialize(json);
        restored.Layers.Should().HaveCount(1);
        restored.Layers[0].Objects.Should().HaveCount(4);

        var restoredText = restored.Layers[0].Objects[0].Should().BeOfType<TextObject>().Subject;
        restoredText.Name.Should().Be("TitleText");
        restoredText.Text.Should().Be("PALLET ID: 9812");
        restoredText.Bold.Should().BeTrue();
        restoredText.FontSizePoints.Should().Be(16.0);

        var restoredBarcode = restored.Layers[0].Objects[1].Should().BeOfType<BarcodeObject>().Subject;
        restoredBarcode.Name.Should().Be("ShipmentBarcode");
        restoredBarcode.Symbology.Should().Be(BarcodeSymbology.Code128);
        restoredBarcode.Data.Should().Be("PKG-88291039");
        restoredBarcode.XDimensionMils.Should().Be(12.0);

        var restoredShape = restored.Layers[0].Objects[2].Should().BeOfType<ShapeObject>().Subject;
        restoredShape.ShapeType.Should().Be(ShapeType.RoundedRectangle);
        restoredShape.CornerRadius.Millimeters.Should().BeApproximately(3.0, 0.0001);

        var restoredPic = restored.Layers[0].Objects[3].Should().BeOfType<PictureObject>().Subject;
        restoredPic.SourceType.Should().Be(PictureSourceType.EmbeddedBase64);
        restoredPic.SourceData.Should().StartWith("iVBORw0");
    }
}
