Get-CimInstance Win32_Process -Filter "Name = 'chrome.exe'" | Where-Object { $_.CommandLine -like "*remote-debugging-port*" } | ForEach-Object {
    Write-Output "PID: $($_.ProcessId)"
    Write-Output "CMD: $($_.CommandLine)"
}

