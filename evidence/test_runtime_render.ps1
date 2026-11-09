try {
    $dllPath = "E:\ReverseEngineering\bartender-investigation\target\SDK\Assemblies\Seagull.BarTender.Print.dll"
    Add-Type -Path $dllPath
    Write-Output "Loaded Seagull.BarTender.Print.dll successfully"

    $engine = New-Object Seagull.BarTender.Print.Engine($true)
    Write-Output "Engine created. IsAlive: $($engine.IsAlive), Version: $($engine.Version), Edition: $($engine.Edition)"

    $sampleBtw = "E:\ReverseEngineering\bartender-investigation\target\SDK\Print Engine API Samples\TaskMaster\C#\Address.btw"
    Write-Output "Opening $sampleBtw ..."
    $doc = $engine.Documents.Open($sampleBtw)
    Write-Output "Doc opened: $($doc.Title), PageSetup Paper: $($doc.PageSetup.PaperName), Width: $($doc.PageSetup.LabelWidth), Height: $($doc.PageSetup.LabelHeight)"

    $outDir = "E:\ReverseEngineering\bartender-investigation\screenshots\runtime"
    if (!(Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    
    $messages = $null
    $doc.ExportPrintPreviewToFile($outDir, "Address_Preview_%PageNumber%.png", [Seagull.BarTender.Print.ImageType]::PNG, [Seagull.BarTender.Print.ColorDepth]::ColorDepth24bit, (New-Object Seagull.BarTender.Print.Resolution(800, 600)), [System.Drawing.Color]::White, [Seagull.BarTender.Print.OverwriteOptions]::Overwrite, $true, $true, [ref]$messages)
    
    Write-Output "Export completed! Checking files..."
    Get-ChildItem $outDir | Select-Object Name, Length | Format-Table -AutoSize

    $doc.Close([Seagull.BarTender.Print.SaveOptions]::DoNotSaveChanges)
    $engine.Stop([Seagull.BarTender.Print.SaveOptions]::DoNotSaveChanges)
    Write-Output "Engine stopped cleanly."
} catch {
    Write-Output "Runtime test failed: $($_.Exception.ToString())"
}
