try {
    $asm = [System.Reflection.Assembly]::ReflectionOnlyLoadFrom("E:\ReverseEngineering\bartender-investigation\target\BarTend.exe")
    Write-Output "FullName: $($asm.FullName)"
    try {
        $types = $asm.GetTypes()
        Write-Output "Types count: $($types.Count)"
    } catch [System.Reflection.ReflectionTypeLoadException] {
        $loadedTypes = $_.Exception.Types | Where-Object { $_ -ne $null }
        Write-Output "Loaded types count: $($loadedTypes.Count)"
        $loadedTypes | Select-Object -First 40 FullName | Format-Table -AutoSize
        Write-Output "--- Loader Exceptions (distinct): ---"
        $_.Exception.LoaderExceptions | ForEach-Object { $_.Message } | Select-Object -Unique | Format-List
    }
} catch {
    Write-Output "Outer error: $($_.Exception.ToString())"
}
