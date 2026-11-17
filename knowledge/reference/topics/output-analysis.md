# Analyze existing PW/PWRS output

Use the user's existing logs, inputs/includes, launch scripts and artifacts.
This guide and its helper work without PASP.x or any source repository. They do
not launch a calculation, MPI job or build, or modify native results. Parameter
syntax is covered by [input generation](input-generation.md); launch diagnosis
by [submission troubleshooting](workshop.md); accuracy by [validation](validation.md).
The recognized output conventions are a compatibility snapshot, not a guarantee
that every release emits the same markers.

## Identify files by content and establish provenance

PASP logs have no required extension. Analyze the user's named file even when
it has a custom suffix or no suffix. Identify the corresponding input/includes,
executable/version if known, launcher and stdout/stderr destinations. A filename,
modification time or same directory alone does not prove that files belong to
the same run. Preserve ambiguous candidates rather than automatically selecting
the newest. Combine scheduler stderr, SCF and path logs when their relationship
is established; do not hide a later failure behind an earlier successful stage.

The packaged [analyze_outputs.py](../../scripts/analyze_outputs.py) requires
Python 3.10+ and only its standard library. In the examples, `SKILL_ROOT` means
the actual installed skill path, and `CASE` means the user's work directory;
replace the placeholders. Neither is a required environment variable.

```text
python -B SKILL_ROOT/knowledge/scripts/analyze_outputs.py CASE/custom.answer
python -B SKILL_ROOT/knowledge/scripts/analyze_outputs.py CASE/stdout CASE/stderr
python -B SKILL_ROOT/knowledge/scripts/analyze_outputs.py CASE --lang zh-Hans
python -B SKILL_ROOT/knowledge/scripts/analyze_outputs.py CASE --lang zh-Hant
python -B SKILL_ROOT/knowledge/scripts/analyze_outputs.py CASE --format json
python -B SKILL_ROOT/knowledge/scripts/analyze_outputs.py CASE --recursive --format json
python -B SKILL_ROOT/knowledge/scripts/analyze_outputs.py CASE/stdout --output NEW_REPORT.md
```

Default output is English Markdown on stdout. `--lang en` (default), `zh-Hans`
and `zh-Hant` select English, Simplified Chinese and Traditional Chinese human
explanations. Raw evidence, filenames, numerical values, units, JSON keys and
status codes remain unchanged. JSON also records language and a localized
summary. `--output` exclusively creates a new user-chosen file; it does not
overwrite existing files, create missing parent directories or permit native
result names as reports. Use `--help` for the installed helper's exact interface;
these are Python helper options, not PASP executable flags.

## Discovery, resource use and failures

Directory scanning is nonrecursive unless `--recursive` is explicit. The helper
samples up to 64 KiB per file to identify recognizable text and skips obvious
binary/UPF content and symbolic links. A sampled but unrecognized text file is
an unresolved candidate, not proof that it is unrelated to PASP; a known explicit
text path can be read in full. Empty stdout/stderr likewise remains uncertain.
Native result artifacts are inventoried by path/size, not decoded by this helper.

Text logs are streamed, retaining stage summaries rather than full eigenvalue
or trajectory tables. Per-category retained evidence is bounded (up to 200
records for errors/warnings/completion and same-stage results), with total counts
reported; stage count still grows with the number of detected stages. Fortran
D/d exponents are accepted. Invalid UTF-8 is replaced and flagged. Overflow
asterisks, incomplete tables and missing blocks are not repaired or invented.

Exit 0 means analysis completed, not calculation success: a MAXITER or failed
run can yield a valid report and exit 0. Unreadable/missing paths, explicit binary
NUL content or read failures yield exit 2 with issues recorded. Keep the helper's
parsing limitations separate from the state of the original calculation.

## Interpret each stage

| Observed evidence | Supported interpretation | Not established |
| --- | --- | --- |
| `PASP_SCF_RESULT status=LEGACY_CONVERGED` | Recognized legacy SCF stopping rule met | Extra outer H/Gram certification, ground state or numerical-parameter convergence |
| `certified=F` | Additional outer certification absent | Failure solely because this field is false |
| `status=MAXITER` | Iteration budget exhausted without accepted convergence | Success from finite energy, force or a normal exit |
| `status=NUMERICAL_FAILURE`, `Error in routine`, `ERROR STOP` | Failure requiring context and stderr inspection | Recovery because an earlier stage succeeded |
| `PASP_BAND_RESULT status=EIGENVALUES_CONVERGED` | Fixed-density path eigenvalue-change criterion met | New SCF convergence or certified physical gap |
| `PASP_BAND_RESULT status=MAXITER` | Last finite bands can remain unconverged | Convergence merely because a spectrum exists |
| `PASP is finished gracefully.` | Observed normal program ending | Every SCF/MD stage or material accuracy accepted |
| Old iteration tables without recognized result markers | Last visible values and explicit evidence can be reported | A guessed modern status |

A stage may have a short status record and a fuller record with iterations,
energy and diagnostics. Treat them as complementary, not automatically two SCFs.
Recognized electronic/NSCF banners, band-reference markers and completion help
separate stages. Without banners, changes in full iteration-result records may
suggest a new stage, but identical repeated records cannot establish whether
there was another calculation. Check the original context.

The helper's file-level outcomes are conservative evidence summaries:
`failure_observed`, `unconverged_observed`, `convergence_unconfirmed`,
`completion_unconfirmed`, or `criteria_met_and_graceful_observed`. Explicit
errors, numerical failures and recognizable nonfinite/overflow numerical fields
remain failure evidence; MAXITER remains unconverged evidence. Missing result
or completion evidence remains unknown. These labels are not process exit codes
or physical-accuracy certificates. MPI-interleaved, clipped, concatenated and
unrecognized-route logs need manual review. A new truncated final stage must
remain visible even after an accepted earlier stage.

## Energy accounting

For the recognized energy labels, the snapshot convention is

$$
E_{\mathrm{tot}}=E_{\mathrm{band}}-\mathrm{deband}+E_H+E_{\mathrm{xc}}+E_{\mathrm{II}}+E_{\mathrm{dip}}+E_U.
$$

In `eband,-deband,EH,Exc,EII,Edip`, the second printed value is already signed.
Sum those values directly, then add separately printed EHub if present. Do not
omit enabled dipole/+U terms or subtract Hubbard double counting twice. If a
helper assumes an absent EHub is zero, state that assumption and check the
actual input and complete output block. Rounded components cannot certify a
more precise total-energy difference.

`eband-deband` versus `Ts+Epslocal+Enl` (with a corresponding Zeeman term when
applicable) is an accounting diagnostic. A small difference alone does not
validate UPFs, magnetic order, forces or convergence. Do not silently replace
printed potential-expectation terms with a presumed density-functional identity
in a non-self-consistent last iteration. Independent +U reconstruction requires
matched occupations, U/J and projector definitions, beyond this log helper.

## Magnetization, forces and stress

For ISPIN 2, `total magnetism` is a signed integral; `absolute magnetism` is an
absolute-density integral. Antiferromagnetic cancellation can make the first
near zero while the second stays finite. Neither is an individual atom's moment.
For ISPIN 4, component-wise absolute integrals are not the integral of vector
magnitude. Preserve the actual printed values and lines; initial MAGMOM is not
a final-state measurement, and intermediate/final quantities can refer to
different electronic stages.

`POSITION and FORCE` carries positions and forces; recognized forces use
Ha/Bohr. The helper counts atom rows and the maximum vector norm within the
recognized block, warning when incomplete. Constraints or force projections
may matter. Finite forces from unconverged SCF do not prove variational accuracy
or completed geometry optimization.

For recognized ordinary PW total stress, units are Ha/Bohr^3 and kbar, with
positive compression; 1 kbar = 0.1 GPa. The helper reads explicitly labeled
total tensors, not kinetic/Hubbard components as totals. Confirm the convention
for the actual release. Fixed-lattice SCF can retain residual stress. Do not
infer PWRS total-stress support from a normal exit or alter cell/U/radii from
one residual stress value.

## Timing and native artifacts

`Time using in DFT_SCF`, solver-detail blocks and older profile markers report
what their labels and scope say. They may be local to a reporting rank and may
exclude startup/setup/postprocessing. H, kinetic/local/nonlocal, FFT and reshape
components can overlap. Preserve numbers without summing overlapping times or
manufacturing a speedup; see [validation](validation.md).

| Artifact/convention | Interpretation boundary |
| --- | --- |
| `CHGCAR` plus paired restart metadata | Native density handoff; keep original bytes and verify compatible SCF provenance/settings |
| `WAVECAR` and auxiliary snapshots | Native PASP states, not a promise of VASP reader compatibility |
| `PLUS_U_NS` | Auxiliary correlated occupations; existence does not certify compatible subspaces or convergence |
| Native band content | Absolute Hartree eigenvalues with a stored reference; use [band plotting](band-plotting.md) |
| `plot.dat` | Shifted by the stored reference already; never subtract it twice |
| `DOSCAR` | Inspect actual units/bin/channel definitions; see [DOS](dos.md) |
| `EIGENVAL` text table | Native stdout table where recognized; see [eigenvalue analysis](eigenvalue-analysis.md) |
| `VLOC`, `CRTCAR`, force/MD/structure files | Inventory first; require their actual format and producer before interpretation |

Names are examples of recognized conventions, not a required suffix or a
cross-software format guarantee. Report source paths and line numbers from the
user's own supplied files, stage states, key observables and missing evidence.

### Native MD output checks

For MD output, report the actual schema and units from headings. Check frame count against requested updates (including step 0), sequential steps/times, finite scalar and per-atom blocks, and lattice/stress blocks for variable-cell cases. Scan the whole legacy log for unique `PW_MD: self-consistent iteration failed` steps; repeated MPI lines are not additional MD steps. Keep `LOBPCG error! Renormal` events separate. A graceful MD end establishes completion evidence only; it does not certify every electronic step or physical accuracy. Absence of newer structured markers is not itself a failure.

Do not merge a log and trajectory merely because they share a directory. Compare initial coordinates, velocities, energy, temperature and hashes. Preserve requested/read-back/effective controls as separate evidence classes. For NVE, assess drift only when the reported energy is the relevant conserved quantity. NPH/NPT variable-cell `Ep` may include pressure-volume terms, and NPH extended enthalpy requires a complete definition. Thermostat/barostat runs should be summarized with observed windows, duration and units; a latter-half statistic is not an equilibrium certificate.
