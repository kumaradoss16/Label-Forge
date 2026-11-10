namespace LabelForge.Core.Tests;

using FluentAssertions;
using LabelForge.Core.Geometry;
using LabelForge.Core.Models;
using LabelForge.Core.Objects;
using LabelForge.Core.Validation;
using Xunit;

public class ObjectValidationTests
{
    private readonly DocumentValidator _validator = new();

    [Fact]
    public void ValidDocument_PassesValidation()
    {
        var doc = LabelDocument.CreateDefault();
        var result = _validator.Validate(doc);

        result.IsValid.Should().BeTrue();
        result.Errors.Should().BeEmpty();
    }

    [Fact]
    public void NegativePageDimensions_FailValidation()
    {
        var doc = LabelDocument.CreateDefault();
        doc.PageSetup.Width = Length.FromMillimeters(-10);

        var result = _validator.Validate(doc);

        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e => e.PropertyPath == "PageSetup.Width");
    }

    [Fact]
    public void MarginsExceedingPage_FailValidation()
    {
        var doc = LabelDocument.CreateDefault();
        doc.PageSetup.Width = Length.FromMillimeters(50);
        doc.PageSetup.Margins = new Thickness2D(Length.FromMillimeters(30), Length.Zero, Length.FromMillimeters(30), Length.Zero);

        var result = _validator.Validate(doc);

        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e => e.PropertyPath == "PageSetup.PrintableWidth");
    }

    [Fact]
    public void BarcodeObject_WithEmptyData_FailsValidation()
    {
        var doc = LabelDocument.CreateDefault();
        var barcode = new BarcodeObject
        {
            Data = ""
        };
        doc.Layers[0].Objects.Add(barcode);

        var result = _validator.Validate(doc);

        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e => e.PropertyPath.EndsWith(".Data"));
    }

    [Fact]
    public void DuplicateLayerIds_FailValidation()
    {
        var doc = LabelDocument.CreateDefault();
        var duplicateId = Guid.NewGuid();
        doc.Layers[0].Id = duplicateId;
        doc.Layers.Add(new Layer("Second Layer") { Id = duplicateId });

        var result = _validator.Validate(doc);

        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e => e.Message.Contains("Duplicate layer ID"));
    }

    [Fact]
    public void DuplicateObjectNames_GenerateWarningNotError()
    {
        var doc = LabelDocument.CreateDefault();
        doc.Layers[0].Objects.Add(new TextObject { Name = "SharedName", Text = "Hello" });
        doc.Layers[0].Objects.Add(new TextObject { Name = "SharedName", Text = "World" });

        var result = _validator.Validate(doc);

        result.IsValid.Should().BeTrue(); // Warnings do not make IsValid false
        result.Errors.Should().Contain(e => e.Severity == ValidationSeverity.Warning && e.Message.Contains("Duplicate object name"));
    }
}
