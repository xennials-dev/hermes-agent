Get-CimInstance Win32_Process -Filter "Name = 'chrome.exe'" | Where-Object { $_.CommandLine -like "*AutomationData*" } | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force
    Write-Output "Killed: $($_.ProcessId)"
}

