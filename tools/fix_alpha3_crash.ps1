<#
.SYNOPSIS
  Fixes the random startup crash (access violation 0xc0000005, fault offset
  0x10e9b15) in a Banjo-Tooie: Recompiled Alpha 3 TooieRecompiled.exe.

.DESCRIPTION
  The guest-update pacing observer reads game address 0x80127634 through an
  unsigned literal, so the generated code addresses RDRAM + 0x100127636, which
  is past the end of the 4 GB RDRAM reservation. Whether that faults depends on
  what the OS mapped there on that launch.

  This script changes the one 8-byte immediate in the executable from
  0x100127636 to 0x127636. It finds the instruction by pattern, refuses to run
  unless exactly one match exists, and writes a backup first.

.EXAMPLE
  .\fix_alpha3_crash.ps1 -Path "C:\Games\BanjoTooieRecomp\TooieRecompiled.exe"
#>
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "File not found: $Path" }
$Path = (Resolve-Path -LiteralPath $Path).Path

# mov rax, 0x100127636   (REX.W B8 imm64)
$bad  = [byte[]](0x48,0xB8,0x36,0x76,0x12,0x00,0x01,0x00,0x00,0x00)
$good = [byte[]](0x48,0xB8,0x36,0x76,0x12,0x00,0x00,0x00,0x00,0x00)

$bytes = [System.IO.File]::ReadAllBytes($Path)

Add-Type -TypeDefinition @"
using System.Collections.Generic;
public static class PatternScan {
    public static List<int> FindAll(byte[] hay, byte[] needle) {
        var hits = new List<int>();
        int limit = hay.Length - needle.Length;
        for (int i = 0; i <= limit; i++) {
            if (hay[i] != needle[0]) continue;
            int k = 1;
            while (k < needle.Length && hay[i + k] == needle[k]) k++;
            if (k == needle.Length) hits.Add(i);
        }
        return hits;
    }
}
"@
function Find-All([byte[]]$hay, [byte[]]$needle) { return ,[PatternScan]::FindAll($hay, $needle) }

$bad_hits  = Find-All $bytes $bad
$good_hits = Find-All $bytes $good

if ($bad_hits.Count -eq 0 -and $good_hits.Count -eq 1) {
    Write-Host "Already fixed: $Path"
    exit 0
}
if ($bad_hits.Count -ne 1) {
    throw "Expected exactly one affected instruction, found $($bad_hits.Count). This is not an unmodified Alpha 3 build; nothing was changed."
}

$at = $bad_hits[0]
Write-Host ("Found affected instruction at file offset 0x{0:X}" -f $at)
if ($WhatIf) { Write-Host "WhatIf: no changes made."; exit 0 }

$backup = "$Path.before_rdram_fix"
if (-not (Test-Path -LiteralPath $backup)) {
    Copy-Item -LiteralPath $Path -Destination $backup
    Write-Host "Backup: $backup"
}

$bytes[$at + 6] = 0x00   # 0x...01_00127636 -> 0x...00_00127636
[System.IO.File]::WriteAllBytes($Path, $bytes)

$check = [System.IO.File]::ReadAllBytes($Path)
$after = Find-All $check $good
$still = Find-All $check $bad
if ($still.Count -ne 0 -or $after.Count -ne 1) { throw "Verification failed; restore from $backup" }
Write-Host "Fixed. Launch the game as usual."
