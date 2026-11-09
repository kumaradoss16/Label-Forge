try {
    $btApp = New-Object -ComObject "BarTender.Application"
    Write-Output "BarTender.Application COM Object created successfully!"
    Write-Output "Version: $($btApp.Version)"
    Write-Output "Build: $($btApp.BuildNumber)"
    Write-Output "IsLicensed: $($btApp.IsLicensed)"
    Write-Output "Edition: $($btApp.Edition)"
    $btApp.Quit(0)
} catch {
    Write-Output "COM Error: $($_.Exception.ToString())"
}
