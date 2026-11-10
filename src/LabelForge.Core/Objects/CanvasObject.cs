using System.Text.Json.Serialization;
using LabelForge.Core.Geometry;

namespace LabelForge.Core.Objects;

/// <summary>
/// Abstract base class for all visual objects placeable on a label layer.
/// Employs polymorphic JSON serialization with type discriminators.
/// </summary>
[JsonPolymorphic(TypeDiscriminatorPropertyName = "$type")]
[JsonDerivedType(typeof(TextObject), typeDiscriminator: "text")]
[JsonDerivedType(typeof(BarcodeObject), typeDiscriminator: "barcode")]
[JsonDerivedType(typeof(ShapeObject), typeDiscriminator: "shape")]
[JsonDerivedType(typeof(PictureObject), typeDiscriminator: "picture")]
public abstract class CanvasObject : IEquatable<CanvasObject>
{
    /// <summary>
    /// Gets or sets the immutable, globally unique identifier of this object.
    /// </summary>
    public Guid Id { get; set; } = Guid.NewGuid();

    /// <summary>
    /// Gets or sets the human-readable unique name of this object within the label (e.g. "Barcode_1").
    /// </summary>
    public string Name { get; set; } = "Object";

    /// <summary>
    /// Gets or sets the physical horizontal offset from the label origin.
    /// </summary>
    public Length X { get; set; } = Length.Zero;

    /// <summary>
    /// Gets or sets the physical vertical offset from the label origin.
    /// </summary>
    public Length Y { get; set; } = Length.Zero;

    /// <summary>
    /// Gets or sets the physical width of the object.
    /// </summary>
    public Length Width { get; set; } = Length.FromMillimeters(25.4);

    /// <summary>
    /// Gets or sets the physical height of the object.
    /// </summary>
    public Length Height { get; set; } = Length.FromMillimeters(12.7);

    /// <summary>
    /// Gets or sets the rotation angle in degrees clockwise (0.0 to 360.0).
    /// </summary>
    public double RotationAngle { get; set; } = 0.0;

    /// <summary>
    /// Gets or sets whether this object is visible on the canvas and in print.
    /// </summary>
    public bool IsVisible { get; set; } = true;

    /// <summary>
    /// Gets or sets whether this object is locked against interactive canvas editing.
    /// </summary>
    public bool IsLocked { get; set; } = false;

    /// <summary>
    /// Gets or sets the reference anchor point for positional placement and rotation.
    /// </summary>
    public AnchorPoint AnchorPoint { get; set; } = AnchorPoint.TopLeft;

    /// <summary>
    /// Optional conditional print expression (e.g. boolean rule or variable check).
    /// </summary>
    public string? PrintWhenCondition { get; set; }

    /// <summary>
    /// Gets the bounding rectangle of this object in unrotated local coordinates.
    /// </summary>
    [JsonIgnore]
    public Rect2D Bounds => new(X, Y, Width, Height);

    public virtual bool Equals(CanvasObject? other)
    {
        if (other is null) return false;
        if (ReferenceEquals(this, other)) return true;
        return Id == other.Id &&
               Name == other.Name &&
               X == other.X &&
               Y == other.Y &&
               Width == other.Width &&
               Height == other.Height &&
               Math.Abs(RotationAngle - other.RotationAngle) < 1e-4 &&
               IsVisible == other.IsVisible &&
               IsLocked == other.IsLocked &&
               AnchorPoint == other.AnchorPoint &&
               PrintWhenCondition == other.PrintWhenCondition;
    }

    public override bool Equals(object? obj) => Equals(obj as CanvasObject);

    public override int GetHashCode() => HashCode.Combine(Id, Name, X, Y, Width, Height);
}
