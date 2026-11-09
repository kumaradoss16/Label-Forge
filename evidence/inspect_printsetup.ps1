$asmPath = "E:\ReverseEngineering\bartender-investigation\target\Seagull.BarTender.Print.dll"
$bytes = [System.IO.File]::ReadAllBytes($asmPath)
$asm = [System.Reflection.Assembly]::Load($bytes)

$t = $asm.GetType("Seagull.BarTender.Print.PrintSetup")
Write-Output "--- PrintSetup Properties ---"
$t.GetProperties() | Select-Object Name, PropertyType | Format-Table -AutoSize
