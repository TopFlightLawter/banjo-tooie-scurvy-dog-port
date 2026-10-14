"""Talon Trot toggle: Z can be released and the trot keeps going; pressing Z again exits.
Idempotent. Run against src/generated before building. Usage: python apply_trot_toggle.py <generated_dir>
Findings: N64 Z = PS5 L2. Enter = Z + C-left (bainput_should_trot, button 0xA). The trot state's exit check is
func_80800710_bsbtrot, which returns bakey_released(player, Z). B (Square) attack is handled by the trot state itself.
"""
import re, sys
from pathlib import Path

gen = Path(sys.argv[1])
MARK = 'TOOIE_TROT_TOGGLE'
NL = chr(10)

# 1) exit check
p = gen / 'funcs_201.c'
t = p.read_text()
if MARK not in t:
    m = re.search(r'RECOMP_FUNC void func_80800710_bsbtrot\(uint8_t\* rdram, recomp_context\* ctx\) \{.*?^\;\}', t, re.M | re.S)
    assert m, 'func_80800710_bsbtrot not found'
    body = m.group(0)
    assert body.count('bakey_released(rdram, ctx);') == 1
    new = body.replace('bakey_released(rdram, ctx);',
                       'bakey_released(rdram, ctx);' + NL + '    ctx->r2 = tooie_trot_toggle(ctx->r2); /* ' + MARK + ' */')
    helper = NL.join([
        '/* ' + MARK + ': phase 0 = Z held since entry, 1 = Z released (latched, trot continues), 2 = Z pressed again (exit) */',
        'int tooie_trot_phase = 0;',
        'static uint64_t tooie_trot_toggle(uint64_t released) {',
        '    if (released) { if (tooie_trot_phase == 0) tooie_trot_phase = 1; return 0; }',
        '    if (tooie_trot_phase == 1) tooie_trot_phase = 2;',
        '    return tooie_trot_phase == 2 ? 1 : 0;',
        '}', '', ''])
    t = t.replace(body, helper + new)
    p.write_text(t)
    print('patched funcs_201.c')
else:
    print('funcs_201.c already patched')

# 2) entry: reset the latch whenever the crouch dispatcher starts a trot
p = gen / 'funcs_205.c'
t = p.read_text()
if MARK not in t:
    lines = t.split(NL)
    idx = [i for i, l in enumerate(lines) if l.strip() == 'bainput_should_trot(rdram, ctx);']
    assert len(idx) == 1, idx
    j = next(k for k in range(idx[0], idx[0] + 30) if lines[k].strip() == 'MEM_W(0X2C, ctx->r29) = ctx->r13;')
    lines.insert(j, '    tooie_trot_phase = 0; /* ' + MARK + ' */')
    t = 'extern int tooie_trot_phase; /* ' + MARK + ' */' + NL + NL.join(lines)
    p.write_text(t)
    print('patched funcs_205.c')
else:
    print('funcs_205.c already patched')
