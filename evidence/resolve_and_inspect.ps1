[System.AppDomain]::CurrentDomain.add_ReflectionOnlyAssemblyResolve({
    param($sender, $args)
    $assemblyName = [System.Reflection.AssemblyName]($args.Name)
    $candidate = "E:\ReverseEngineering\bartender-investigation\target\$($assemblyName.Name).dll"
    if (Test-Path $candidate) {
        return [System.Reflection.Assembly]::ReflectionOnlyLoadFrom($candidate)
    }
    return [System.Reflection.Assembly]::ReflectionOnlyLoad($args.Name)
})

$asm = [System.Reflection.Assembly]::ReflectionOnlyLoadFrom("E:\ReverseEngineering\bartender-investigation\target\BarTend.exe")
$refAssemblies = $asm.GetReferencedAssemblies()
Write-Output "--- Referenced Assemblies in BarTend.exe ---"
$refAssemblies | Select-Object Name, Version, CultureName, @{Name="PublicKeyToken"; Expression={[System.BitConverter]::ToString($_.GetPublicKeyToken())}} | Format-Table -AutoSize

try {
    $types = $asm.GetTypes()
    Write-Output "Successfully resolved all types! Total: $($types.Count)"
    $meaningfulTypes = $types | Where-Object { $_.FullName -notmatch "CppImplementationDetails|ArrayType|\$StaticArray" }
    Write-Output "Meaningful managed types: $($meaningfulTypes.Count)"
    $meaningfulTypes | Select-Object FullName, BaseType, IsPublic, IsClass | Select-Object -First 50 | Format-Table -AutoSize
} catch [System.Reflection.ReflectionTypeLoadException] {
    Write-Output "Exceptions count: $($_.Exception.LoaderExceptions.Count)"
    $_.Exception.LoaderExceptions | ForEach-Object { $_.Message } | Select-Object -Unique | Format-List
}
