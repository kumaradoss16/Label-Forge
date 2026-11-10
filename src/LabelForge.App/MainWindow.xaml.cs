namespace LabelForge.App;

using System.Windows;
using Microsoft.Win32;
using LabelForge.Core.Models;
using LabelForge.Core.Serialization;
using LabelForge.Core.Validation;

public partial class MainWindow : Window
{
    private readonly DocumentSerializer _serializer;
    private readonly DocumentValidator _validator;
    private readonly AtomicFileOperations _fileOps;

    private LabelDocument _currentDocument;
    private string? _currentFilePath;

    public MainWindow(
        DocumentSerializer serializer,
        DocumentValidator validator,
        AtomicFileOperations fileOps)
    {
        InitializeComponent();
        _serializer = serializer;
        _validator = validator;
        _fileOps = fileOps;

        _currentDocument = LabelDocument.CreateDefault();
        UpdateTitle();
    }

    private void UpdateTitle()
    {
        var docName = string.IsNullOrEmpty(_currentFilePath) ? "Untitled" : System.IO.Path.GetFileName(_currentFilePath);
        Title = $"LabelForge — {docName} ({_currentDocument.PageSetup.Width.Millimeters:F1}mm x {_currentDocument.PageSetup.Height.Millimeters:F1}mm)";
    }

    private void OnNewDocumentClicked(object sender, RoutedEventArgs e)
    {
        _currentDocument = LabelDocument.CreateDefault();
        _currentFilePath = null;
        UpdateTitle();
        StatusText.Text = "New document created.";
    }

    private void OnOpenDocumentClicked(object sender, RoutedEventArgs e)
    {
        var dlg = new OpenFileDialog
        {
            Filter = "LabelForge Documents (*.olb)|*.olb|All Files (*.*)|*.*",
            DefaultExt = ".olb"
        };

        if (dlg.ShowDialog(this) == true)
        {
            try
            {
                _currentDocument = _fileOps.Load(dlg.FileName);
                _currentFilePath = dlg.FileName;
                UpdateTitle();
                StatusText.Text = $"Opened: {System.IO.Path.GetFileName(dlg.FileName)}";
            }
            catch (Exception ex)
            {
                MessageBox.Show(this, $"Failed to open document: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }

    private void OnSaveDocumentClicked(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrEmpty(_currentFilePath))
        {
            OnSaveAsDocumentClicked(sender, e);
        }
        else
        {
            SaveCurrentDocument(_currentFilePath);
        }
    }

    private void OnSaveAsDocumentClicked(object sender, RoutedEventArgs e)
    {
        var dlg = new SaveFileDialog
        {
            Filter = "LabelForge Documents (*.olb)|*.olb|All Files (*.*)|*.*",
            DefaultExt = ".olb",
            FileName = "Label1.olb"
        };

        if (dlg.ShowDialog(this) == true)
        {
            _currentFilePath = dlg.FileName;
            SaveCurrentDocument(_currentFilePath);
        }
    }

    private void SaveCurrentDocument(string path)
    {
        try
        {
            _fileOps.SaveAtomic(_currentDocument, path, validateBeforeSave: true, createBackup: false);
            UpdateTitle();
            StatusText.Text = $"Saved: {System.IO.Path.GetFileName(path)}";
        }
        catch (Exception ex)
        {
            MessageBox.Show(this, $"Failed to save document: {ex.Message}", "Save Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private void OnExitClicked(object sender, RoutedEventArgs e)
    {
        Close();
    }

    private void OnAboutClicked(object sender, RoutedEventArgs e)
    {
        MessageBox.Show(this,
            "LabelForge Desktop Application\nVersion 1.0.0 (M0/M1 Engine)\n\nIndependent clean-room label design system.",
            "About LabelForge",
            MessageBoxButton.OK,
            MessageBoxImage.Information);
    }
}
