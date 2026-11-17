# Sampled eigenvalues and conditional band edges

Use [analyze_eigenvalues.py](../../scripts/analyze_eigenvalues.py) with existing
native band content or a native stdout `EIGENVAL` table. It works offline, does
not run PASP and accepts arbitrary filenames or extensionless paths. It is not
a universal reader for other software's same-named files. The recognized
conventions are a compatibility snapshot; unknown formats need the actual
release documentation or matching example.

Python 3.10+ and NumPy are required. The helper shares the packaged band reader;
its analysis does not require importing Matplotlib. Resolve `SKILL_ROOT` from
the installed skill location and `CASE` from the user's chosen work directory.

```text
python -B SKILL_ROOT/knowledge/scripts/analyze_eigenvalues.py CASE/spectrum --occupied-bands 12
python -B SKILL_ROOT/knowledge/scripts/analyze_eigenvalues.py CASE/custom_stdout --input-kind scf --occupied-bands 12 --unit eV --lang zh-Hans
python -B SKILL_ROOT/knowledge/scripts/analyze_eigenvalues.py CASE/stdout --input-kind scf --table 2 --ef-hartree 0.2 --format json
python -B SKILL_ROOT/knowledge/scripts/analyze_eigenvalues.py CASE/data --occupied-bands 12 --unit custom --units-per-hartree 10 --lang zh-Hant --output NEW_REPORT.md
```

These are helper flags, not PASP flags. Use `--help` for the installed interface.
The `12`, `0.2` and custom factor above only illustrate syntax.

## Filling is an explicit assumption

`--occupied-bands N` assumes the lowest N states at each sampled k are occupied.
Both occupied and empty states must be present. N counts states in the native
single eigenvalue list, not automatically states per spin. The helper sorts
energies to choose edges while retaining original band indices, with no inferred
up/down assignment.

It reports sampled VBM/CBM, all band-edge samples with equal printed energies,
the indirect difference and the smallest same-k direct difference. The indirect
difference may be negative to show overlap; it is not clamped to zero. A gap
conditional on fixed N does not prove that the actual finite-temperature or
fractionally occupied state is insulating.

Without N, a header reference or explicit `--ef-hartree` supplies only a
reference-split HOMO/LUMO diagnostic: energies at or below the reference form
the lower set and energies above it the upper set. This is not a demonstrated
occupation-based band gap. A state exactly on the reference follows that
convention, not a claim of definite zero-temperature occupation. For an SCF
table without an explicit usable reference/filling, the result remains
`filling_required`; do not invent an EF.

The printed `weight` in an SCF table can combine k integration, occupation and
spin counting. Rounded small values can become zero. It is not a pure occupation
probability, so the helper does not infer integer filling from WKE, electron
count or ISPIN. Preserve the filling assumption, finite smearing and any actual
fractional occupations when interpreting the result.

## Validate tables and provenance

The stdout reader expects paired EIGENVAL boundaries, recognized headers,
continuous k/band indices, Cartesian and reciprocal coordinates, and equal
band counts at each point. Empty, nonfinite, interrupted or truncated tables
are rejected. If several complete tables are present, choose `--table INDEX`
explicitly; the helper does not automatically use the final table.

Reports retain table/edge line numbers and printed edge weights. A nearby
preceding SCF status is context only; check the complete run with
[output analysis](output-analysis.md). A closed equal-length table cannot reveal
whole points or columns consistently omitted from the supplied text: compare
counts against the actual input and run metadata. Limits are 64 MiB input and
2,000,000 states; invalid text is not silently repaired.

Native path data has cumulative distance, not recoverable three-dimensional k
vectors. The recognized legacy raw band precision is 0.0001 Hartree, about
2.72 meV; converting units or printing more decimals adds no information. The
SCF table's Hartree column is the analysis data; a neighboring eV column is not
used to reconstruct extra precision. See [band plotting](band-plotting.md).

## Units, languages and output

Default unit is eV, using 27.211386245988 eV/Ha. Ha/Hartree, Ry/Rydberg and meV
are also built in. A custom unit needs its name and a positive finite
`--units-per-hartree` factor. `--ef-hartree` always uses Hartree; output unit
selection does not change that input convention.

`--lang en` is default; `zh-Hans` and `zh-Hant` select Simplified and Traditional
Chinese human explanations. JSON keys, status codes, raw evidence and values
stay stable. Default output is Markdown on stdout; `--format json` selects JSON.
`--output` exclusively creates a new file and refuses existing paths. The
analysis leaves native inputs unchanged.

## Scientific limits

Path gaps cover only the supplied path; SCF sampled gaps cover only retained
mesh/irreducible points. Neither guarantees continuous full-Brillouin-zone
extrema. Positive sampled differences do not prove an insulator. Retain missing
occupations, MAXITER, unknown executable/file provenance, missing completion,
finite smearing and unconverged cutoff/k/empty-band settings as limitations.

The helper does not certify a ground state, magnetic order, gap accuracy,
effective mass or Fermi surface. For analysis scope see
[native spectra](native-band-analysis.md); for physical validation see
[validation](validation.md). Do not activate an unrelated native physical task
to obtain an ordinary offline band-edge query.
