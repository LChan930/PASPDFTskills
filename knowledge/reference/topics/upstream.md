# Attribution and scope

This skill includes organizational ideas adapted from PASPskills, an independent
reference package. The recorded attribution snapshot is PASPskills 0.1.15,
revision `e645ad2adf230b6dcbcb179f50cd7300fa0216c5`, recorded on 2026-11-12.
The public project identifier is `cy0752/PASPskills` on GitHub. This record is
provenance for the packaged material, not a claim that it is the latest version
or an official manual for the user's executable.

The MIT attribution is Copyright (c) 2026 cy0752; the original text is retained
in [LICENSE.PASPskills](../LICENSE.PASPskills). It does not grant a license to PASP
itself. PASP is closed source; users need only their authorized executable,
applicable documentation and calculation files to use this skill. No separate
copy of PASPskills or private development workspace is a runtime dependency.

## Useful organizational conventions

The skill follows a thin entrypoint, task-specific references and separate
skill/user working directories. Locate scripts from the actually loaded skill
root; resolve Markdown links relative to their containing document and user
input/output paths relative to the user's chosen work directory. Do not assume
the current directory is the installation directory.

No external package's agent instructions, workflow state machine, installer or
confirmation/delegation policy is inherited by reading reference material.
The user's task and the installed skill's instructions govern the work.
Templates illustrate syntax, not guaranteed support, recommended physics or
proven performance for an unidentified executable.

## Distinguish physical models

Native PW/PWRS uses `Model DFT`. Native ionic dynamics uses `DFT.LMD` and
`PW_MD.*` in the packaged compatibility snapshot; see [PW workflows](../modules/pw.md).
Effective-H spin/lattice dynamics uses a different model and parameter family,
including `Model atomic_effective_H`, `atom_Heff.MD`, `MD.*`, `SLD.mode` and
`LLG.*`. A file named `MD.input` does not identify which model is intended.

Similarly, effective-H `MD.B_x/y/z` or an `ExternalMagneticField` example is not
a substitute for native orbital-field `DFT.Bfield` with integer `DFT.PWL.n0`.
Do not move a setting between these domains because its name sounds similar.

General PASP references can help with Model/include/block concepts, but native
DFT defaults, accepted feature combinations, restart formats and statuses must
be checked against the packaged snapshot and actual release/manual/log
evidence. When evidence is missing, report uncertainty without making source
access a prerequisite or inventing official documentation.
