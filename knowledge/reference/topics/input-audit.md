# Offline native FDF input audit

`knowledge/scripts/audit_inputs.py` performs bounded static checks using only
Python 3.10+ standard library and this package's parameter tables. It requires
no PASP executable, source repository, MPI, NumPy or network. It does not edit
inputs, select scientific parameters, run calculations or emulate the executable
parser. Successful analysis does not establish a converged or physically valid
calculation.

Use the absolute installed skill path and an existing FDF file or a case directory
containing `lattice_model.fdf`:

```text
python -B SKILL_ROOT/knowledge/scripts/audit_inputs.py CASE --format json
python -B SKILL_ROOT/knowledge/scripts/audit_inputs.py CASE/lattice_model.fdf --ranks 40 --irreducible-kpoints 20
python -B SKILL_ROOT/knowledge/scripts/audit_inputs.py CASE --lang zh-Hans --output NEW_REPORT.md
python -B SKILL_ROOT/knowledge/scripts/audit_inputs.py CASE --lang zh-Hant --format json --output NEW_REPORT.json
```

Replace `SKILL_ROOT`, `CASE` and report placeholders with actual paths. Defaults
are English Markdown on stdout. `--lang en|zh-Hans|zh-Hant` changes human
explanations while raw evidence, codes, numbers, paths and JSON keys remain
stable. `--output` exclusively creates a new UTF-8 file and refuses any existing
path. Parent directories must already exist. Exit 0 means the audit completed,
including when findings contain errors; exit 2 means invalid invocation, missing
main input, registry/read failure or refused report creation. Inspect `status`,
`summary` and `findings`, not the exit code alone.

## Explicit coverage

| Area | Automated checks | Boundaries |
|---|---|---|
| Include closure | Recursive `%include`, single/double quoted paths with spaces, comments outside quotes, missing files, cycles, source hashes and include edges | Relative paths first use main-input working directory. A beside-including-file fallback is warned; two existing alternatives are warned. This lookup is an audit convention requiring release confirmation, not executable equivalence. |
| FDF syntax | Named `%block`/`%endblock` pairing, nested/unclosed blocks, quoted scalar tokens, duplicate keys/blocks with file/line anchors | Unknown directives warn. Every duplicate remains unresolved; subsequent structure/semantic checks are conservatively skipped, without choosing first/last precedence. |
| Registry | Known names/types/default descriptions loaded from the three packaged `reference/params/input-parameters-*.md` tables | Unknown keys WARN, including `DFT.nv_pool` with a safe nk/nb typo hint. No automatic spelling correction. `rmax_cut` is recognized as an ancillary name; its physical adequacy is not checked. |
| Scalar types | Finite numeric values, integer literals, logical literals, explicit energy units where documented | Recognized name does not mean all enum/conditional rules are implemented. Many workflow-specific types and blocks remain outside semantic coverage. |
| Structure | Positive atom/species count, coordinate row count, finite xyz, species index/symbol consistency, lattice-block shape/conflict, positive supported-unit lattice constant | Coordinate rows require at least native `x y z species_index symbol`; trailing user fields are preserved. No determinant, lattice-parameter geometry, supercell expansion or minimum-distance check. POSCAR is inventoried but not decoded. |
| Species and UPFs | Native coordinate symbols/indices, `pseudo_pot_files` count/order, existence/hash, bounded PP_HEADER metadata for element/valence/relativity/SOC/type/XC | Do not require another program's `ChemicalSpeciesLabel`. If supplied, it is compatibility information, not the audited mapping. Legacy unrecognized UPF headers remain UNKNOWN; filenames are not metadata. No projector/radial validity or cross-species XC compatibility proof. |
| Spin/SOC | ISPIN 1/2/4, MAGMOM three finite components per atom when present; has_so=T requires ISPIN4 in this snapshot | Missing MAGMOM uses documented-default warning; no magnetic-order selection. ISPIN4 alone does not establish SOC. Per-species SR/FR metadata is retained without inventing a global scalar/spinor channel split. |
| Hubbard | Manifold count versus rows, type1/type2 fields, finite U/J, shell syntax, actual structure symbols, species-local IDs/ranges/overlap, documented task conflicts | No projector-radius selection, U calibration, occupation-matrix validation or independent effective-Hamiltonian reconstruction. |
| Cutoffs | Selected ENCUT converted to Ha; missing ENCUT defaults to 10 Ha; missing ENCUT_RHO becomes four times selected ENCUT | Ha/Hartree, Ry/Rydberg, eV and meV are recognized. Values are documented static predictions, not runtime read-back or cutoff convergence evidence. |
| Parallel pools | Positive integer pools, nk divides actual ranks, nb divides ranks/nk, nk divides supplied actual global k count; PWRS/SCF_ONLY/Chern constraints | `--ranks` is actual MPI ranks, not nodes or threads. Supply `--irreducible-kpoints` from matched global read-back, or actual generated path count for bands. No automatic launcher/log pairing and no raw-mesh-to-IBZ substitution. No universal NBAND % nb_pool rule or performance claim. |
| Stage handoff | Band/RCHARG requests inventory CHGCAR + CHGCAR.restart, +U additionally PLUS_U_NS; RWAVE inventories WAVECAR | Missing restart or upstream compatibility is UNKNOWN evidence. Existing bytes do not prove accepted upstream SCF or matching structure/spin/U/UPFs. Binary restart content is not decoded. |

`requested` preserves all explicit definitions and source anchors.
`documented_defaults` records only defaults actually consulted by checked rules.
`effective_documented_only` records the selected cutoff expression and known RS
override rule with `runtime_verified=false`. `runtime_readback` and
`runtime_effective` stay empty: no matched log or executable is consulted.
Resources explicitly record supplied counts and `raw_mesh_used_as_ibz=false`.

ERROR means a definite violation of an implemented packaged snapshot rule,
not a universal rejection by every release. WARN means ambiguity/compatibility
requires attention. UNKNOWN means evidence is missing or a check was not
performed. Unknown additional release tags are never errors solely because
they are absent from the registry.

The FDF read budget is 16 MiB per file, 256 unique dependencies during include
expansion, 64 include levels and 500,000 expanded nonempty lines. UPF metadata
reads at most 256 KiB of each header; dependency SHA-256 streams the actual file.
No content is silently repaired. Generic parser success cannot prove full
workflow support, SCF convergence, correct ground state, reasonable k mesh,
forces, stress or physical accuracy.
