Add-Type @"
  using System;
  using System.Runtime.InteropServices;
  using System.Text;

  public class WinHelper {
      public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

      [DllImport("user32.dll")]
      public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

      [DllImport("user32.dll")]
      public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

      [DllImport("user32.dll", CharSet = CharSet.Auto)]
      public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

      [DllImport("user32.dll")]
      public static extern bool IsWindowVisible(IntPtr hWnd);
  }
"@

[WinHelper]::EnumWindows({
    param($hWnd, $lParam)
    $procId = 0
    [WinHelper]::GetWindowThreadProcessId($hWnd, [ref]$procId)
    $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if ($p -and ($p.Name -like "*bartend*" -or $p.Name -like "*activat*")) {
        $sb = New-Object System.Text.StringBuilder 256
        [WinHelper]::GetWindowText($hWnd, $sb, 256) | Out-Null
        $title = $sb.ToString()
        $vis = [WinHelper]::IsWindowVisible($hWnd)
        Write-Output "PID: $procId ($($p.Name)) | HWND: $hWnd | Visible: $vis | Title: '$title'"
    }
    return $true
}, [IntPtr]::Zero)
