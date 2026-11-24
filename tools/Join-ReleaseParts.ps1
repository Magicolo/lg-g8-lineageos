[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$File,
    [string]$Directory = '.'
)

$ErrorActionPreference = 'Stop'
$folder = (Resolve-Path -LiteralPath $Directory).Path
$manifest = Get-Content -LiteralPath (Join-Path $folder 'split-files.json') -Raw | ConvertFrom-Json
$entry = @($manifest.files | Where-Object { $_.name -ceq $File })
if ($entry.Count -ne 1 -or $File -notmatch '^[A-Za-z0-9_.-]+\z') {
    throw 'Choose one whole filename listed in split-files.json.'
}
$entry = $entry[0]
$destination = Join-Path $folder $File
if (Test-Path -LiteralPath $destination) {
    if ((Get-FileHash -LiteralPath $destination).Hash -ne $entry.sha256) {
        throw 'A conflicting output file already exists.'
    }
    Write-Output "The existing $File already has the correct digest."
    return
}

$parts = foreach ($part in $entry.parts) {
    if ($part.name -notmatch '^[A-Za-z0-9_.-]+\z' -or $part.sha256 -notmatch '^[0-9a-f]{64}\z') {
        throw 'Invalid part name or digest in manifest.'
    }
    $path = Join-Path $folder $part.name
    $current = Get-Item -LiteralPath $path
    if ($current.Length -ne $part.size -or (Get-FileHash -LiteralPath $path).Hash -ne $part.sha256) {
        throw "Part failed its integrity check - $($part.name)"
    }
    $current.FullName
}

$temporary = Join-Path $folder ($File + '.' + [guid]::NewGuid().ToString('N') + '.partial')
$target = [IO.File]::Open($temporary, 'CreateNew', 'Write')
try {
    foreach ($part in $parts) {
        $source = [IO.File]::OpenRead($part)
        try { $source.CopyTo($target) } finally { $source.Dispose() }
    }
} finally {
    $target.Dispose()
}
if ((Get-Item -LiteralPath $temporary).Length -ne $entry.size -or
    (Get-FileHash -LiteralPath $temporary).Hash -ne $entry.sha256) {
    throw "Joined file failed its integrity check - $temporary"
}
[IO.File]::Move($temporary, $destination)
Write-Output "Verified and assembled $File."
