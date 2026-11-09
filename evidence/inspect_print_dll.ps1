$asmPath = "E:\ReverseEngineering\bartender-investigation\target\Seagull.BarTender.Print.dll"
$bytes = [System.IO.File]::ReadAllBytes($asmPath)
$asm = [System.Reflection.Assembly]::Load($bytes)
Write-Output "--- Types in Seagull.BarTender.Print.dll ---"
$asm.GetExportedTypes() | Select-Object FullName, BaseType | Format-Table -AutoSize
