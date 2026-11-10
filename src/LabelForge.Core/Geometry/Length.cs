using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace LabelForge.Core.Geometry;

/// <summary>
/// Represents an immutable physical length measurement stored canonically in millimeters.
/// Provides deterministic conversions to/from Inches, Centimeters, Points, and device pixels at specified DPI.
/// </summary>
[JsonConverter(typeof(LengthJsonConverter))]
public readonly struct Length : IEquatable<Length>, IComparable<Length>
{
    private const double MmPerInch = 25.4;
    private const double PointsPerInch = 72.0;

    /// <summary>
    /// Gets the length value in millimeters (canonical storage unit).
    /// </summary>
    public double Millimeters { get; }

    /// <summary>
    /// Gets the length value converted to inches.
    /// </summary>
    public double Inches => Millimeters / MmPerInch;

    /// <summary>
    /// Gets the length value converted to centimeters.
    /// </summary>
    public double Centimeters => Millimeters / 10.0;

    /// <summary>
    /// Gets the length value converted to typographic points (1/72 inch).
    /// </summary>
    public double Points => Inches * PointsPerInch;

    private Length(double millimeters)
    {
        Millimeters = millimeters;
    }

    public static Length Zero => new(0.0);

    public static Length FromMillimeters(double mm) => new(mm);

    public static Length FromInches(double inches) => new(inches * MmPerInch);

    public static Length FromCentimeters(double cm) => new(cm * 10.0);

    public static Length FromPoints(double points) => new((points / PointsPerInch) * MmPerInch);

    public static Length FromPixels(double pixels, double dpi = 96.0)
    {
        if (dpi <= 0) throw new ArgumentOutOfRangeException(nameof(dpi), "DPI must be positive.");
        return FromInches(pixels / dpi);
    }

    /// <summary>
    /// Converts this physical length to pixels / dots for a specified device resolution (DPI).
    /// Default is 96.0 DPI (standard Windows / WPF screen coordinate system).
    /// </summary>
    public double ToPixels(double dpi = 96.0)
    {
        if (dpi <= 0) throw new ArgumentOutOfRangeException(nameof(dpi), "DPI must be positive.");
        return Inches * dpi;
    }

    /// <summary>
    /// Converts this physical length to 96-DPI screen pixels.
    /// </summary>
    public double ToScreenPixels() => ToPixels(96.0);

    /// <summary>
    /// Converts this physical length to device dots/pixels at the specified hardware DPI.
    /// </summary>
    public double ToDevicePixels(double dpi) => ToPixels(dpi);

    public static Length operator +(Length a, Length b) => new(a.Millimeters + b.Millimeters);
    public static Length operator -(Length a, Length b) => new(a.Millimeters - b.Millimeters);
    public static Length operator -(Length a) => new(-a.Millimeters);
    public static Length operator *(Length a, double factor) => new(a.Millimeters * factor);
    public static Length operator *(double factor, Length a) => new(a.Millimeters * factor);
    public static Length operator /(Length a, double divisor)
    {
        if (Math.Abs(divisor) < double.Epsilon) throw excitingDivideByZero();
        return new(a.Millimeters / divisor);
    }
    public static double operator /(Length a, Length b)
    {
        if (Math.Abs(b.Millimeters) < double.Epsilon) throw excitingDivideByZero();
        return a.Millimeters / b.Millimeters;
    }

    private static DivideByZeroException excitingDivideByZero() => new("Cannot divide Length by zero.");

    public static bool operator ==(Length a, Length b) => Math.Abs(a.Millimeters - b.Millimeters) < 1e-6;
    public static bool operator !=(Length a, Length b) => !(a == b);
    public static bool operator <(Length a, Length b) => a.Millimeters < b.Millimeters;
    public static bool operator <=(Length a, Length b) => a.Millimeters <= b.Millimeters || a == b;
    public static bool operator >(Length a, Length b) => a.Millimeters > b.Millimeters;
    public static bool operator >=(Length a, Length b) => a.Millimeters >= b.Millimeters || a == b;

    public bool Equals(Length other) => this == other;

    public override bool Equals(object? obj) => obj is Length other && Equals(other);

    public override int GetHashCode() => Math.Round(Millimeters, 4).GetHashCode();

    public int CompareTo(Length other) => Millimeters.CompareTo(other.Millimeters);

    public override string ToString() => $"{Millimeters:F2} mm";

    public string ToString(string format, IFormatProvider? formatProvider = null)
        => $"{Millimeters.ToString(format, formatProvider)} mm";

    public static Length Parse(string value)
    {
        if (string.IsNullOrWhiteSpace(value))
            throw new ArgumentException("Length string cannot be empty.", nameof(value));

        value = value.Trim().ToLowerInvariant();

        if (value.EndsWith("mm"))
            return FromMillimeters(double.Parse(value[..^2].Trim(), CultureInfo.InvariantCulture));
        if (value.EndsWith("in"))
            return FromInches(double.Parse(value[..^2].Trim(), CultureInfo.InvariantCulture));
        if (value.EndsWith("cm"))
            return FromCentimeters(double.Parse(value[..^2].Trim(), CultureInfo.InvariantCulture));
        if (value.EndsWith("pt"))
            return FromPoints(double.Parse(value[..^2].Trim(), CultureInfo.InvariantCulture));
        if (value.EndsWith("px"))
            return FromPixels(double.Parse(value[..^2].Trim(), CultureInfo.InvariantCulture));

        // Default unit is millimeters if numeric only
        return FromMillimeters(double.Parse(value, CultureInfo.InvariantCulture));
    }
}

public sealed class LengthJsonConverter : JsonConverter<Length>
{
    public override Length Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        return reader.TokenType switch
        {
            JsonTokenType.Number => Length.FromMillimeters(reader.GetDouble()),
            JsonTokenType.String => Length.Parse(reader.GetString()!),
            _ => throw new JsonException($"Unexpected token type {reader.TokenType} for Length.")
        };
    }

    public override void Write(Utf8JsonWriter writer, Length value, JsonSerializerOptions options)
    {
        // Serialized canonically as a floating-point number in millimeters
        writer.WriteNumberValue(Math.Round(value.Millimeters, 4));
    }
}
