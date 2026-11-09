$asmPath = "E:\ReverseEngineering\bartender-investigation\target\Seagull.BarTender.Print.dll"
$bytes = [System.IO.File]::ReadAllBytes($asmPath)
$asm = [System.Reflection.Assembly]::Load($bytes)

$t = $asm.GetType("Seagull.BarTender.Print.LabelFormatDocument")
Write-Output "--- LabelFormatDocument Properties ---"
$t.GetProperties() | Select-Object Name, PropertyType | Format-Table -AutoSize
Write-Output "--- LabelFormatDocument Methods ---"
$t.GetMethods([System.Reflection.BindingFlags]'Public,Instance,DeclaredOnly') | Select-Object Name, ReturnType | Format-Table -AutoSize
