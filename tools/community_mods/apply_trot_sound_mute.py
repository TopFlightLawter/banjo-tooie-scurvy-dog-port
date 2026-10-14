"""Mute the Talon Trot footstep (sound id 0x0433) at the engine's 'start slot' function func_800C3BDC.
Sound slots live at 0x80128C10 (+0x80 each, 1-based index in a0); +0x58 halfword = sound id,
+0x5A halfword = volume, +0x5C = volume handed to the voice (computed from +0x5A).
v2 (2026-10-12): the footstep is STARTED at volume 0 (+0x5A=+0x5C=0). v1 freed the slot early, which broke other
sounds (silo open sound cut off while Trotting) because the game still held the footstep's slot number.
Idempotent. Usage: python apply_trot_sound_mute.py <generated_dir>"""
import re, sys
from pathlib import Path
gen = Path(sys.argv[1]); MARK = 'TOOIE_TROT_SOUND_MUTE'; NL = chr(10)
p = gen / 'funcs_136.c'; t = p.read_text()
if MARK in t:
    print('already applied'); raise SystemExit(0)
m = re.search(r'RECOMP_FUNC void func_800C3BDC\(uint8_t\* rdram, recomp_context\* ctx\) \{' + NL + r'(.*?)' + NL + r'    int c1cs = 0;' + NL, t, re.S)
assert m, 'func_800C3BDC header not found'
patch = NL.join([
    '    { /* ' + MARK + ' */',
    '        uint32_t tm_idx = (uint32_t)ctx->r4 & 0xFFu;',
    '        if (tm_idx != 0u && (uint16_t)MEM_H(0X58, (gpr)(int32_t)(0x80128B90u + tm_idx * 0x80u)) == 0x0433u) {',
    '            MEM_H(0X5A, (gpr)(int32_t)(0x80128B90u + tm_idx * 0x80u)) = 0;',
    '            MEM_H(0X5C, (gpr)(int32_t)(0x80128B90u + tm_idx * 0x80u)) = 0;',
    '        }',
    '    }', ''])
t = t[:m.end()] + patch + t[m.end():]
p.write_text(t); print('patched funcs_136.c')
