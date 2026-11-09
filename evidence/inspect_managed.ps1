$asmPath = "E:\ReverseEngineering\bartender-investigation\target\BarTender.Managed.dll"
$bytes = [System.IO.File]::ReadAllBytes($asmPath)
$asm = [System.Reflection.Assembly]::Load($bytes)
Write-Output "--- Types in BarTender.Managed.dll ---"
$asm.GetExportedTypes() | Select-Object FullName, BaseType | Format-Table -AutoSize
