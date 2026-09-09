# Delete a directory git could not remove because of Windows MAX_PATH.
# robocopy /MIR against an empty dir handles long paths natively; Remove-Item alone does not.
# Usage: powershell -File purge-longpath-dir.ps1 -Target <path> [-Execute]
param(
    [Parameter(Mandatory = $true)][string]$Target,
    [switch]$Execute
)

if (-not (Test-Path -LiteralPath $Target)) {
    Write-Host "not present, nothing to do: $Target"; exit 0
}

$size = (Get-ChildItem -LiteralPath $Target -Recurse -Force -ErrorAction SilentlyContinue |
         Measure-Object -Property Length -Sum).Sum
Write-Host ("target: {0} ({1:N1} MB)" -f $Target, ($size / 1MB))

if (-not $Execute) {
    Write-Host "DRY RUN -- re-run with -Execute to delete."
    exit 0
}

$empty = Join-Path $env:TEMP ("gcu-empty-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $empty -Force | Out-Null
try {
    robocopy $empty $Target /MIR /NFL /NDL /NJH /NJS /NC /NS /NP | Out-Null
    # robocopy exit codes are a bitmask: < 8 is success. 1-7 means "copied/changed", not failure.
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed with exit code $LASTEXITCODE" }
    Remove-Item -LiteralPath $Target -Recurse -Force -ErrorAction Stop
} finally {
    Remove-Item -LiteralPath $empty -Recurse -Force -ErrorAction SilentlyContinue
}

if (Test-Path -LiteralPath $Target) {
    Write-Host "FAILED -- still present: $Target"; exit 1
}
Write-Host ("removed: {0} ({1:N1} MB reclaimed)" -f $Target, ($size / 1MB))
