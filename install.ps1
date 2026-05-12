<#
.SYNOPSIS
Installs the probe-feature skill library into ~/.claude/skills/.

.DESCRIPTION
Walks skills/ for any folder containing a SKILL.md and copies each leaf folder to
~/.claude/skills/<leaf-name>/. On collision, prompts overwrite / skip / archive.
Offers to archive prototype skills (probe, scope, grill-me) on first run.

.PARAMETER DryRun
If set, prints what would happen without copying anything.

.PARAMETER Force
If set, overwrites collisions without prompting.

.EXAMPLE
.\install.ps1
.\install.ps1 -DryRun
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$repoRoot   = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillsRoot = Join-Path $repoRoot 'skills'
$destRoot   = Join-Path $HOME '.claude\skills'
$archiveRoot = Join-Path $destRoot '.archive'

if (-not (Test-Path $skillsRoot)) {
    throw "skills/ folder not found at $skillsRoot"
}

if (-not (Test-Path $destRoot)) {
    if ($DryRun) {
        Write-Host "[dry-run] would create $destRoot"
    } else {
        New-Item -ItemType Directory -Path $destRoot -Force | Out-Null
    }
}

# Find leaf skill folders (any folder containing SKILL.md, excluding shared/templates).
$leafSkills = Get-ChildItem -Path $skillsRoot -Recurse -Filter 'SKILL.md' -File |
    Where-Object { $_.Directory.FullName -notlike '*shared\templates*' } |
    ForEach-Object { $_.Directory }

Write-Host "Found $($leafSkills.Count) skill folders to install."

# Offer to archive prototype skills on first encounter.
$prototypes = @('probe', 'scope', 'grill-me')
$existingPrototypes = $prototypes | Where-Object { Test-Path (Join-Path $destRoot $_) }
if ($existingPrototypes.Count -gt 0) {
    Write-Host "Found existing prototype skills: $($existingPrototypes -join ', ')"
    if (-not $Force) {
        $answer = Read-Host "Archive these (move to .archive/) before installing the new library? (y/N)"
    } else {
        $answer = 'y'
    }
    if ($answer -eq 'y') {
        if (-not (Test-Path $archiveRoot)) {
            if (-not $DryRun) { New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null }
        }
        foreach ($p in $existingPrototypes) {
            $src = Join-Path $destRoot $p
            $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
            $dst = Join-Path $archiveRoot "$p-$stamp"
            if ($DryRun) {
                Write-Host "[dry-run] would archive $src -> $dst"
            } else {
                Move-Item -Path $src -Destination $dst
                Write-Host "Archived $p -> .archive/$p-$stamp"
            }
        }
    }
}

# Install each leaf.
$installed = 0; $skipped = 0; $overwritten = 0
foreach ($leaf in $leafSkills) {
    $name = $leaf.Name
    $dst = Join-Path $destRoot $name

    if (Test-Path $dst) {
        if ($Force) {
            $action = 'overwrite'
        } else {
            $action = Read-Host "Skill '$name' already exists. (o)verwrite / (s)kip / (a)rchive-then-overwrite?"
        }
        switch ($action) {
            'o' {
                if ($DryRun) { Write-Host "[dry-run] would overwrite $dst" }
                else { Remove-Item -Recurse -Force $dst; Copy-Item -Recurse $leaf.FullName $dst }
                $overwritten++
            }
            'overwrite' {
                if ($DryRun) { Write-Host "[dry-run] would overwrite $dst" }
                else { Remove-Item -Recurse -Force $dst; Copy-Item -Recurse $leaf.FullName $dst }
                $overwritten++
            }
            'a' {
                $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
                $archDst = Join-Path $archiveRoot "$name-$stamp"
                if (-not (Test-Path $archiveRoot)) {
                    if (-not $DryRun) { New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null }
                }
                if ($DryRun) {
                    Write-Host "[dry-run] would archive existing $dst -> $archDst, then install"
                } else {
                    Move-Item -Path $dst -Destination $archDst
                    Copy-Item -Recurse $leaf.FullName $dst
                }
                $overwritten++
            }
            default {
                Write-Host "Skipped $name"; $skipped++
            }
        }
    } else {
        if ($DryRun) { Write-Host "[dry-run] would install $name -> $dst" }
        else { Copy-Item -Recurse $leaf.FullName $dst }
        $installed++
    }
}

Write-Host ""
Write-Host "Summary: $installed installed, $overwritten overwritten/archived, $skipped skipped."
