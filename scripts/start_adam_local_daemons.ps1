[CmdletBinding()]
param(
    [string]$RepoRoot
)

# Windows PowerShell 5.1 leaves $PSScriptRoot empty while param() defaults are
# evaluated, so resolve the repo root here instead.
if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) '..')).Path
}

# Adam-One local daemon starter — a faithful mirror of start_lumin_local_daemons.ps1,
# adapted for the adam-one lab. Starts the four shared custodian daemons
# (Steward, Advocate, Temporal, Processor) against adam-one-lab's own state, so
# Adam runs the same operating logic as Verus/Lumin.
#
# Differences from the Lumin script, and why:
#   - Paths/identity point at adam-one-lab; peer id = 'adam-one'.
#   - The Processor runs WITHOUT --rls-active: adam-one has no RLS orb provisioned
#     (no deploy/adam-one-lab/pod). The built-in rls_runtime still materialises
#     derived rls.jsonl at commit time; only the query-time RLS *orb* is absent.
#     Enable --rls-active + AEGIS_RLS_ACTIVE only after an RLS orb is provisioned
#     and P1-activated for adam-one.
#
# No lived state is copied; each daemon operates adam-one's own state root.

$ErrorActionPreference = 'Stop'

$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
$ReleaseRoot = Join-Path $RepoRoot 'deploy\adam-one-lab\local\foundation'
$StateRoot = Join-Path $RepoRoot 'deploy\adam-one-lab\local\state'
$DaemonDir = Join-Path $StateRoot 'daemons'
$LogDir = Join-Path $StateRoot 'logs'

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Repo virtualenv python not found at $Python"
}

New-Item -ItemType Directory -Force -Path $DaemonDir, $LogDir | Out-Null

$resolvedState = (Resolve-Path -LiteralPath $StateRoot).Path
$resolvedDaemon = (Resolve-Path -LiteralPath $DaemonDir).Path
if (-not $resolvedDaemon.StartsWith($resolvedState, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to touch daemon directory outside state root: $resolvedDaemon"
}

$env:PYTHONPATH = @(
    (Join-Path $RepoRoot 'src'),
    (Join-Path $RepoRoot 'packages\aegis-pod-sdk\src'),
    (Join-Path $RepoRoot 'packages\orb-rls-persistent-relations-core\src')
) -join ';'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:AEGIS_PEER_ID = 'adam-one'
$env:AEGIS_DATAQUAD_NAMES = 'adam-one'
$env:AEGIS_FRONTIER_TRANSPORT = 'claude_desktop_mcp_stdio_local'

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$daemonSpecs = @(
    @{ Name = 'steward'; Module = 'aegis_peer_runtime.steward_daemon'; Args = @('--socket', (Join-Path $DaemonDir 'steward.sock'), '--release-root', $ReleaseRoot, '--state-root', $StateRoot) },
    @{ Name = 'advocate'; Module = 'aegis_peer_runtime.advocate_daemon'; Args = @('--socket', (Join-Path $DaemonDir 'advocate.sock'), '--release-root', $ReleaseRoot, '--state-root', $StateRoot) },
    @{ Name = 'temporal'; Module = 'aegis_peer_runtime.temporal_daemon'; Args = @('--socket', (Join-Path $DaemonDir 'temporal.sock'), '--state-root', $StateRoot) },
    @{ Name = 'processor'; Module = 'aegis_peer_runtime.processor_daemon'; Args = @('--socket', (Join-Path $DaemonDir 'processor.sock'), '--release-root', $ReleaseRoot, '--state-root', $StateRoot, '--peer-id', 'adam-one') }
)

$results = foreach ($spec in $daemonSpecs) {
    $module = $spec.Module
    $existing = Get-CimInstance Win32_Process |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine.Contains($module) -and
            $_.CommandLine.Contains($StateRoot)
        } |
        Select-Object -First 1

    if ($existing) {
        [pscustomobject]@{
            Name = $spec.Name
            Status = 'already-running'
            ProcessId = $existing.ProcessId
            Stdout = $null
            Stderr = $null
        }
        continue
    }

    $socketPath = Join-Path $DaemonDir "$($spec.Name).sock"
    if (Test-Path -LiteralPath $socketPath) {
        Remove-Item -LiteralPath $socketPath -Force
    }

    $stdout = Join-Path $LogDir "$($spec.Name)-$timestamp.out.log"
    $stderr = Join-Path $LogDir "$($spec.Name)-$timestamp.err.log"
    $arguments = @('-m', $module) + $spec.Args
    $process = Start-Process -FilePath $Python `
        -ArgumentList $arguments `
        -WorkingDirectory $RepoRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru

    [pscustomobject]@{
        Name = $spec.Name
        Status = 'started'
        ProcessId = $process.Id
        Stdout = $stdout
        Stderr = $stderr
    }
}

Start-Sleep -Milliseconds 750
$results | ConvertTo-Json -Depth 4
