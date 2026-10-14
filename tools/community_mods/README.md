# Community Talon Trot mods

Two optional patches for Banjo-Tooie: Recompiled, by CubicCanvas. Both are
scripts that edit the locally generated game code before a build. They contain
patch logic only: no ROM data and no generated game code.

| Script | Effect |
|---|---|
| `apply_trot_toggle.py` | Talon Trot toggle. Release Z (L2 on PS5) and the Trot keeps going; press Z again to exit. B (Square) still attacks. Requested in issue #17. |
| `apply_trot_sound_mute.py` | Silences the Trot's extra footstep sound (id `0x0433`). The normal footstep (`0x0401`) and all other sounds are unchanged. Requested in issue #10. |

## Use

1. Generate the game code as described in `docs/CODEGEN.md`.
2. Run each script against the generated directory (idempotent):

   ```
   py -3 tools/community_mods/apply_trot_toggle.py generated
   py -3 tools/community_mods/apply_trot_sound_mute.py generated
   ```

3. Build as usual. Regenerating the code removes the patches, so re-run the
   scripts after any regeneration.

If the repository's codegen provenance check rejects the edited output, the
patched output must be re-attested locally; these scripts do not do that for
you.

## Status

Both were confirmed by the author in game on Alpha 3 (Windows 11, Vulkan).
They are not part of the upstream project and have had no wider testing.
Prepared with Claude Code (AI assistance).
