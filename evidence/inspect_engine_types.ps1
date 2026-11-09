$asmPath = "E:\ReverseEngineering\bartender-investigation\target\Seagull.BarTender.Print.dll"
$bytes = [System.IO.File]::ReadAllBytes($asmPath)
$asm = [System.Reflection.Assembly]::Load($bytes)

$typesToInspect = @("Seagull.BarTender.Print.Engine", "Seagull.BarTender.Print.LabelFormatDocument", "Seagull.BarTender.Print.PrintSetup", "Seagull.BarTender.Print.PageSetup")
foreach ($typeName in $typesToInspect) {
    $t = $asm.GetType($typeName)
    if ($t) {
        Write-Output "================ $typeName ================"
        Write-Output "--- Properties ---"
        $t.GetProperties() | Select-Object Name, PropertyType | Format-Table -AutoSize
        Write-Output "--- Methods ---"
        $t.GetMethods([System.Reflection.BindingFlags]'Public,Instance,DeclaredOnly') | Select-Object Name, ReturnType | Format-Table -AutoSize
    } else {
        Write-Output "Type not found: $typeName"
    }
}
