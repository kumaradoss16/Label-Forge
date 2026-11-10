namespace LabelForge.Core.Geometry;

/// <summary>
/// Represents an immutable 2D point in physical label coordinates.
/// </summary>
public readonly record struct Point2D(Length X, Length Y)
{
    public static Point2D Zero => new(Length.Zero, Length.Zero);

    public override string ToString() => $"({X}, {Y})";
}

/// <summary>
/// Represents an immutable 2D size in physical label coordinates.
/// </summary>
public readonly record struct Size2D(Length Width, Length Height)
{
    public static Size2D Zero => new(Length.Zero, Length.Zero);

    public override string ToString() => $"{Width} x {Height}";
}

/// <summary>
/// Represents an immutable 2D bounding rectangle in physical label coordinates.
/// </summary>
public readonly record struct Rect2D(Length X, Length Y, Length Width, Length Height)
{
    public static Rect2D Empty => new(Length.Zero, Length.Zero, Length.Zero, Length.Zero);

    public Length Left => X;
    public Length Top => Y;
    public Length Right => X + Width;
    public Length Bottom => Y + Height;

    public bool Contains(Point2D point)
        => point.X >= Left && point.X <= Right && point.Y >= Top && point.Y <= Bottom;

    public bool IntersectsWith(Rect2D other)
        => other.Left <= Right && other.Right >= Left && other.Top <= Bottom && other.Bottom >= Top;

    public override string ToString() => $"X={X}, Y={Y}, W={Width}, H={Height}";
}

/// <summary>
/// Represents an immutable physical margin / padding thickness.
/// </summary>
public readonly record struct Thickness2D(Length Left, Length Top, Length Right, Length Bottom)
{
    public static Thickness2D Zero => new(Length.Zero, Length.Zero, Length.Zero, Length.Zero);

    public static Thickness2D Uniform(Length value) => new(value, value, value, value);

    public static Thickness2D Symmetric(Length horizontal, Length vertical) => new(horizontal, vertical, horizontal, vertical);

    public override string ToString() => $"Left={Left}, Top={Top}, Right={Right}, Bottom={Bottom}";
}
