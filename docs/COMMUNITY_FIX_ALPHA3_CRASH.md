# Alpha 3 startup crash: cause and fix

This is a community fix by CubicCanvas (TopFlightLawter). It is not from the
original maintainer.

## Symptom

`TooieRecompiled.exe` closes to the desktop with no error, usually a few
seconds after **Start Game**, and sometimes before it. Windows logs an access
violation (`0xc0000005`) at fault offset `0x10e9b15` in the Alpha 3 release.
It is intermittent: the same settings launch fine on some attempts.

## Cause

The pacing observer hook that the build tooling inserts at the start of guest
function `func_800A73F4` reads game address `0x80127634`:

```c
tooie_guest_update_observed(MEM_H(0X80127634, 0) != 0);
```

`0X80127634` is an unsigned 32-bit literal, so the `MEM_H` address arithmetic
is not sign-extended the way the rest of the generated code is. The access
lands at `RDRAM + 0x100127636`, past the end of the 4 GB RDRAM reservation.
The correct offset is `0x127636`.

Whether that read faults depends on what Windows happened to map at that
address on that launch, which is why the crash is intermittent. When it does
not fault, the hook reads an unrelated value.

The compiled instruction is:

```
movabs rax, 0x100127636
cmp    word ptr [rdi + rax], 0
```

## Fix

Source: emit a sign-extended literal in `tools/instrument_continuous.py`:

```c
tooie_guest_update_observed(MEM_H(-0X7FED89CC, 0) != 0);
```

Existing Alpha 3 executables: `tools/fix_alpha3_crash.ps1` changes the one
immediate from `0x100127636` to `0x127636` (a single byte, `01` to `00`).

```powershell
.\tools\fix_alpha3_crash.ps1 -Path "C:\path\to\TooieRecompiled.exe"
```

The script locates the instruction by byte pattern, stops unless exactly one
match exists, writes `TooieRecompiled.exe.before_rdram_fix` first, and
verifies the result.

## What was and was not verified

- Verified: the fault offset in 182 Windows crash records maps to this
  instruction (Alpha 3 release exe and local builds).
- Verified: after patching, Alpha 3 launched successfully on every attempt on
  the reporter's machine (Windows 11, Intel i7-10850H, NVIDIA MX250, Vulkan).
  Before patching it crashed in a large share of launches.
- Verified: the patch script on an unmodified copy produced a byte-identical
  result to the executable that was tested in game.
- Verified: `apply_guest_update_observer` emits the new literal and the
  address arithmetic evaluates to `0x127636`.
- Verified: the executable was rebuilt from the changed source and the hook disassembles to `cmp word ptr [rdi + 0x127636], 0`, the correct address. That rebuilt executable (with the Talon Trot patches in tools/community_mods applied) was then launched repeatedly, including at other display settings, and every launch started without a crash; the Windows Application log recorded no faults for it. The reporter counted "well over 10" launches; the game log recorded 9 of them.
- The cause of the intermittence (what is mapped at the bad address) is
  inferred, not observed.

## Disclosure

Diagnosis and the patch were produced with Claude Code (an AI assistant) and
checked against the reporter's own crash logs and launches.
