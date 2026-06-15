<# :
@echo off
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting admin privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
powershell -ExecutionPolicy Bypass -File "%~f0"
exit /b
#>

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  GitHub Network Optimization" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] Admin required!" -ForegroundColor Red
    Write-Host "Right-click -> Run as Administrator" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

$hostsPath = "C:\Windows\System32\drivers\etc\hosts"
$domains = @(
    "github.com",
    "api.github.com",
    "codeload.github.com",
    "uploads.github.com",
    "objects.githubusercontent.com",
    "github.global.ssl.fastly.net"
)

Write-Host "===== Step 1: Resolve GitHub IPs =====" -ForegroundColor Green
Write-Host ""

$ipMap = @{}
foreach ($d in $domains) {
    try {
        $ips = [System.Net.Dns]::GetHostAddresses($d)
        $ipv4 = ($ips | Where-Object { $_.AddressFamily -eq "InterNetwork" } | Select-Object -First 1).IPAddressToString
        if ($ipv4) {
            $ipMap[$d] = $ipv4
            Write-Host "  $d -> $ipv4" -ForegroundColor White
        } else {
            Write-Host "  $d -> No IPv4" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  $d -> Failed" -ForegroundColor Red
    }
}

if ($ipMap.Count -eq 0) {
    Write-Host ""
    Write-Host "[ERROR] Cannot resolve any GitHub domain" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "===== Step 2: Update hosts file =====" -ForegroundColor Green
Write-Host ""

$hostsContent = Get-Content $hostsPath -Raw -ErrorAction SilentlyContinue

$markerStart = "# === GitHub Access Optimization Start ==="
$markerEnd = "# === GitHub Access Optimization End ==="

$escapedStart = [regex]::Escape($markerStart)
$escapedEnd = [regex]::Escape($markerEnd)
$pattern = "(?s)" + $escapedStart + ".*?" + $escapedEnd
$hostsContent = $hostsContent -replace $pattern, ""

$githubBlock = "`n$markerStart"
foreach ($d in $domains) {
    if ($ipMap.ContainsKey($d)) {
        $githubBlock += "`n$($ipMap[$d]) $d"
    }
}
$githubBlock += "`n$markerEnd`n"

$hostsContent = $hostsContent.TrimEnd() + "`n" + $githubBlock

attrib -R $hostsPath
Set-Content -Path $hostsPath -Value $hostsContent -NoNewline -Encoding ASCII
attrib +R $hostsPath

Write-Host "  hosts updated" -ForegroundColor White

Write-Host ""
Write-Host "===== Step 3: Flush DNS =====" -ForegroundColor Green
Write-Host ""

ipconfig /flushdns | Out-Null
Write-Host "  DNS flushed" -ForegroundColor White

Write-Host ""
Write-Host "===== Step 4: Optimize Git network =====" -ForegroundColor Green
Write-Host ""

git config --global http.postBuffer 524288000
Write-Host "  http.postBuffer = 524288000 (500MB)" -ForegroundColor White

git config --global http.lowSpeedLimit 1000
git config --global http.lowSpeedTime 60
Write-Host "  http.lowSpeedLimit = 1000, lowSpeedTime = 60" -ForegroundColor White

git config --global http.version HTTP/1.1
Write-Host "  http.version = HTTP/1.1" -ForegroundColor White

git config --global core.compression 0
Write-Host "  core.compression = 0" -ForegroundColor White

git config --global http.sslBackend schannel
Write-Host "  http.sslBackend = schannel" -ForegroundColor White

Write-Host ""
Write-Host "===== Step 5: Verify connection =====" -ForegroundColor Green
Write-Host ""

$successCount = 0
$failCount = 0
foreach ($d in @("github.com", "api.github.com")) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $result = $tcp.BeginConnect($d, 443, $null, $null)
        $ok = $result.AsyncWaitHandle.WaitOne(8000, $false)
        if ($ok -and $tcp.Connected) {
            Write-Host "  ${d}:443 -> OK" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  ${d}:443 -> TIMEOUT" -ForegroundColor Red
            $failCount++
        }
        $tcp.Close()
    } catch {
        Write-Host "  ${d}:443 -> ERROR" -ForegroundColor Red
        $failCount++
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
if ($failCount -eq 0) {
    Write-Host "  Done! GitHub connection OK" -ForegroundColor Green
} elseif ($successCount -gt 0) {
    Write-Host "  Done! Partial connection, try again later" -ForegroundColor Yellow
} else {
    Write-Host "  Done, but connection still failed" -ForegroundColor Red
    Write-Host "  Try: 1.Check proxy 2.Retry later 3.Use GitHub API" -ForegroundColor Yellow
}
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"