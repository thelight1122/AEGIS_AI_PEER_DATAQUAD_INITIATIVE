<#
Durable SSH tunnel: Windows 127.0.0.1:8790 -> vm-cyberpeer-core 127.0.0.1:8790

Carries the Lumin GPT Action Orb origin to the cloudflared connector on this machine.
The origin binds loopback on the Pod host, so this tunnel is the only path in, and the
Cloudflare ingress points at the local end of it.

Reconnects on drop. ExitOnForwardFailure means a half-open tunnel that cannot bind the
local port fails immediately rather than sitting there looking healthy while forwarding
nothing.
#>

$ErrorActionPreference = 'Continue'

$RemoteHost = 'AEGISIPFSNode'
$LocalPort  = 8790
$RemotePort = 8790
$LogFile    = Join-Path $env:LOCALAPPDATA 'aegis-lumin-tunnel.log'

function Write-Log([string]$Message) {
    $line = "{0}  {1}" -f (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'), $Message
    Add-Content -Path $LogFile -Value $line
}

Write-Log "tunnel supervisor starting: 127.0.0.1:$LocalPort -> ${RemoteHost}:$RemotePort"

while ($true) {
    # If something already holds the port, do not fight it.
    $held = Get-NetTCPConnection -State Listen -LocalPort $LocalPort -ErrorAction SilentlyContinue
    if ($held) {
        Write-Log "port $LocalPort already listening; waiting"
        Start-Sleep -Seconds 30
        continue
    }

    Write-Log "connecting"
    & ssh -N `
        -o BatchMode=yes `
        -o ExitOnForwardFailure=yes `
        -o ServerAliveInterval=30 `
        -o ServerAliveCountMax=3 `
        -o StrictHostKeyChecking=accept-new `
        -L "${LocalPort}:127.0.0.1:${RemotePort}" `
        $RemoteHost 2>&1 | ForEach-Object { Write-Log "ssh: $_" }

    Write-Log "tunnel exited (code $LASTEXITCODE); retrying in 15s"
    Start-Sleep -Seconds 15
}
