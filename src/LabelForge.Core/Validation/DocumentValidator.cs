namespace LabelForge.Core.Validation;

using LabelForge.Core.Geometry;
using LabelForge.Core.Models;
using LabelForge.Core.Objects;

/// <summary>
/// Domain validator enforcing geometric, structural, and business rules on LabelForge documents.
/// </summary>
public sealed class DocumentValidator
{
    public ValidationResult Validate(LabelDocument document)
    {
        var result = new ValidationResult();

        if (document.Id == Guid.Empty)
        {
            result.AddError("Document.Id", "Document ID must not be empty.");
        }

        if (string.IsNullOrWhiteSpace(document.FormatVersion))
        {
            result.AddError("Document.FormatVersion", "Document format version must be specified.");
        }

        // Page setup validation
        ValidatePageSetup(document.PageSetup, result);

        // Layers validation
        ValidateLayers(document.Layers, result);

        return result;
    }

    private static void ValidatePageSetup(PageSetup pageSetup, ValidationResult result)
    {
        if (pageSetup.Width <= Length.Zero)
        {
            result.AddError("PageSetup.Width", "Label width must be strictly greater than zero.");
        }

        if (pageSetup.Height <= Length.Zero)
        {
            result.AddError("PageSetup.Height", "Label height must be strictly greater than zero.");
        }

        if (pageSetup.Margins.Left < Length.Zero || pageSetup.Margins.Right < Length.Zero ||
            pageSetup.Margins.Top < Length.Zero || pageSetup.Margins.Bottom < Length.Zero)
        {
            result.AddError("PageSetup.Margins", "Margins cannot be negative.");
        }

        if (pageSetup.PrintableWidth <= Length.Zero)
        {
            result.AddError("PageSetup.PrintableWidth", "Combined horizontal margins exceed total label width.");
        }

        if (pageSetup.PrintableHeight <= Length.Zero)
        {
            result.AddError("PageSetup.PrintableHeight", "Combined vertical margins exceed total label height.");
        }

        if (pageSetup.LabelsAcross < 1)
        {
            result.AddError("PageSetup.LabelsAcross", "Labels across must be at least 1.");
        }

        if (pageSetup.LabelsDown < 1)
        {
            result.AddError("PageSetup.LabelsDown", "Labels down must be at least 1.");
        }
    }

    private static void ValidateLayers(List<Layer> layers, ValidationResult result)
    {
        if (layers.Count == 0)
        {
            result.AddWarning("Layers", "Document contains no layers.");
            return;
        }

        var layerIds = new HashSet<Guid>();
        var objectIds = new HashSet<Guid>();
        var objectNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        for (int i = 0; i < layers.Count; i++)
        {
            var layer = layers[i];
            var layerPath = $"Layers[{i}]";

            if (layer.Id == Guid.Empty)
            {
                result.AddError($"{layerPath}.Id", "Layer ID must not be empty.");
            }
            else if (!layerIds.Add(layer.Id))
            {
                result.AddError($"{layerPath}.Id", $"Duplicate layer ID detected: '{layer.Id}'.");
            }

            if (string.IsNullOrWhiteSpace(layer.Name))
            {
                result.AddError($"{layerPath}.Name", "Layer name must not be blank.");
            }

            // Validate objects inside layer
            for (int j = 0; j < layer.Objects.Count; j++)
            {
                var obj = layer.Objects[j];
                var objPath = $"{layerPath}.Objects[{j}]";
                ValidateObject(obj, objPath, objectIds, objectNames, result);
            }
        }
    }

    private static void ValidateObject(
        CanvasObject obj,
        string path,
        HashSet<Guid> objectIds,
        HashSet<string> objectNames,
        ValidationResult result)
    {
        if (obj.Id == Guid.Empty)
        {
            result.AddError($"{path}.Id", "Object ID must not be empty.");
        }
        else if (!objectIds.Add(obj.Id))
        {
            result.AddError($"{path}.Id", $"Duplicate object ID detected: '{obj.Id}'.");
        }

        if (string.IsNullOrWhiteSpace(obj.Name))
        {
            result.AddError($"{path}.Name", "Object name must not be blank.");
        }
        else if (!objectNames.Add(obj.Name))
        {
            result.AddWarning($"{path}.Name", $"Duplicate object name detected: '{obj.Name}'. Object names should be unique for clear reference.");
        }

        if (obj.Width < Length.Zero)
        {
            result.AddError($"{path}.Width", "Object width cannot be negative.");
        }

        if (obj.Height < Length.Zero)
        {
            result.AddError($"{path}.Height", "Object height cannot be negative.");
        }

        // Polymorphic checks
        switch (obj)
        {
            case BarcodeObject barcode:
                if (string.IsNullOrEmpty(barcode.Data))
                {
                    result.AddError($"{path}.Data", "Barcode data must not be empty.");
                }
                if (barcode.XDimensionMils <= 0.0)
                {
                    result.AddError($"{path}.XDimensionMils", "Barcode X-Dimension must be strictly greater than zero mils.");
                }
                if (barcode.BarHeight <= Length.Zero)
                {
                    result.AddError($"{path}.BarHeight", "Barcode bar height must be strictly greater than zero.");
                }
                if (barcode.WideToNarrowRatio < 1.0)
                {
                    result.AddError($"{path}.WideToNarrowRatio", "Barcode wide-to-narrow ratio must be >= 1.0.");
                }
                break;

            case TextObject text:
                if (text.FontSizePoints <= 0.0)
                {
                    result.AddError($"{path}.FontSizePoints", "Font size must be strictly greater than zero points.");
                }
                if (string.IsNullOrWhiteSpace(text.FontFamily))
                {
                    result.AddError($"{path}.FontFamily", "Font family must not be blank.");
                }
                break;

            case ShapeObject shape:
                if (shape.StrokeThickness < Length.Zero)
                {
                    result.AddError($"{path}.StrokeThickness", "Shape stroke thickness cannot be negative.");
                }
                if (shape.CornerRadius < Length.Zero)
                {
                    result.AddError($"{path}.CornerRadius", "Corner radius cannot be negative.");
                }
                break;

            case PictureObject pic:
                if (pic.SourceType != PictureSourceType.VariableExpression && string.IsNullOrWhiteSpace(pic.SourceData))
                {
                    result.AddError($"{path}.SourceData", "Picture source data cannot be empty for embedded or file-referenced pictures.");
                }
                break;
        }
    }
}
