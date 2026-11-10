namespace LabelForge.Core.Tests;

using FluentAssertions;
using LabelForge.Core.Geometry;
using Xunit;

public class GeometryTests
{
    [Fact]
    public void FromMillimeters_StoresCanonicalValueCorrectly()
    {
        var len = Length.FromMillimeters(25.4);
        len.Millimeters.Should().BeApproximately(25.4, 0.0001);
        len.Inches.Should().BeApproximately(1.0, 0.0001);
        len.Points.Should().BeApproximately(72.0, 0.001);
    }

    [Fact]
    public void FromInches_ConvertsToCanonicalMillimeters()
    {
        var len = Length.FromInches(4.0);
        len.Millimeters.Should().BeApproximately(101.6, 0.0001);
        len.Inches.Should().Be(4.0);
    }

    [Fact]
    public void DpiConversions_ProduceExactPixelValues()
    {
        var oneInch = Length.FromInches(1.0);

        // Screen 96 DPI
        oneInch.ToScreenPixels().Should().BeApproximately(96.0, 0.0001);

        // Standard thermal 203 DPI (8 dots/mm)
        oneInch.ToDevicePixels(203.2).Should().BeApproximately(203.2, 0.0001);

        // High res thermal 300 DPI
        oneInch.ToDevicePixels(300.0).Should().BeApproximately(300.0, 0.0001);

        // 600 DPI
        oneInch.ToDevicePixels(600.0).Should().BeApproximately(600.0, 0.0001);
    }

    [Fact]
    public void LengthArithmetic_WorksConsistently()
    {
        var a = Length.FromMillimeters(10.0);
        var b = Length.FromMillimeters(5.0);

        (a + b).Millimeters.Should().BeApproximately(15.0, 0.0001);
        (a - b).Millimeters.Should().BeApproximately(5.0, 0.0001);
        (a * 2.0).Millimeters.Should().BeApproximately(20.0, 0.0001);
        (a / 2.0).Millimeters.Should().BeApproximately(5.0, 0.0001);
        (-a).Millimeters.Should().BeApproximately(-10.0, 0.0001);
    }

    [Fact]
    public void Rect2D_ContainsAndIntersects_CalculatesAccurately()
    {
        var rect = new Rect2D(Length.FromMillimeters(10), Length.FromMillimeters(10), Length.FromMillimeters(50), Length.FromMillimeters(50));
        
        var inside = new Point2D(Length.FromMillimeters(25), Length.FromMillimeters(25));
        var outside = new Point2D(Length.FromMillimeters(5), Length.FromMillimeters(5));

        rect.Contains(inside).Should().BeTrue();
        rect.Contains(outside).Should().BeFalse();

        var overlapping = new Rect2D(Length.FromMillimeters(40), Length.FromMillimeters(40), Length.FromMillimeters(30), Length.FromMillimeters(30));
        rect.IntersectsWith(overlapping).Should().BeTrue();
    }
}
