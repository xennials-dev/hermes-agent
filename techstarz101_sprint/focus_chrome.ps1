Add-Type @"
  using System;
  using System.Runtime.InteropServices;
  public class WinApi {
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool IsIconic(IntPtr hWnd);
  }
"@

$proc = Get-Process -Id 22964 -ErrorAction SilentlyContinue
if ($proc) {
    Write-Output "PID 22964 Handle: $($proc.MainWindowHandle)"
    Write-Output "PID 22964 Title: $($proc.MainWindowTitle)"
    if ($proc.MainWindowHandle -ne 0) {
        $isMin = [WinApi]::IsIconic($proc.MainWindowHandle)
        Write-Output "IsIconic (Minimized): $isMin"
        # Restore (9) and Bring to front
        [WinApi]::ShowWindow($proc.MainWindowHandle, 9)
        [WinApi]::SetForegroundWindow($proc.MainWindowHandle)
        Write-Output "Restored and brought to foreground!"
    } else {
        Write-Output "MainWindowHandle is 0. Searching thread windows..."
    }
} else {
    Write-Output "Process 22964 not found."
}

