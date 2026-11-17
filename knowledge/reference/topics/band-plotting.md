# Read and plot existing native band spectra

Use the user's explicit native PW/PWRS spectrum and corresponding log. Files
can have any name or no extension. The packaged helper validates content; it
does not launch PASP, SCF or MPI. The format below is a packaged compatibility
snapshot, not a promise about all PASP releases or other software's `.bands`.

## Decide what the figure can show

Confirm system, path, desired energy window and energy zero. By default preserve
stored sample order, use the header reference as zero and plot all stored bands.
Check `PASP_BAND_REFERENCE` and `PASP_BAND_RESULT` in a matching run log via
[output analysis](output-analysis.md). A header number alone does not establish
an accepted SCF Fermi energy or convergence. Record MAXITER or other incomplete
convergence in the accompanying report and metadata even when plotted numbers
are finite.

The default restrained figure uses blue spectra, light path guides and a dashed
zero. Native data lacks state-resolved spin labels, so the helper does not create
up/down colors. `--ispin` only records user-supplied provenance. Never label
band-number halves as spin channels.

Keep the figure canvas focused on the spectrum: a concise material/method title,
axes, path labels and a necessary data legend. Do not add status or provenance
sentences such as "legacy converged", "path converged", "spin labels
unavailable", automatic ISPIN subtitles or cautionary footnotes to the figure.
Place convergence, missing metadata and interpretation limits in the external
report and JSON. `--ispin` records provenance in JSON without annotating the
figure. This presentation rule does not change data interpretation or permit
invented spin labels.

## Recognized native content

| Content | Snapshot convention |
| --- | --- |
| Line 1 | One reference energy in Hartree; zero and negative values are valid |
| Line 2 | Cumulative path start/end distances; native PW/PWRS distances use Bohr inverse including 2 pi |
| Line 3 | Stored energy-range metadata; recompute the actual range from samples |
| Line 4 | `nband 1 nk`; constant middle field is not ISPIN |
| Each k sample | Distance and raw energies, up to 10 energies per line, continued as needed; native blank lines allowed |
| Energy precision | Legacy text step 0.0001 Hartree, about 2.72 meV |
| Tail | Symmetry-point count followed by distance/quoted-label pairs |
| `plot.dat` | Two-column per-band blocks, already shifted by reference in Hartree |

Raw native band energies are absolute. Default plotting uses

$$
E_{\mathrm{plot}}=(E-E_{\mathrm{ref}})\times27.211386245988\ \mathrm{eV/Ha}.
$$

Subtract once. `plot.dat` alone lacks the raw reference, path-label and spin
metadata needed for this reader; the helper rejects that two-column format.
Even if shifted text has more digits, pairing it with metadata requires proof
that both files came from the same run. Never subtract its reference again.

The single native eigenvalue list does not provide per-state spin projections
for ISPIN 2/4. A spinor spectrum is not two independent up/down lists.

## Path segments and labels

Preserve stored cumulative distances. Do not reconstruct three-dimensional k
coordinates, assign a high-symmetry path or reorder bands without supporting
input. With `BandLines`, the point counts describe samples, not automatic path
breaks; a count of 1 does not mean disconnect.

This native format has no explicit discontinuity marker. A large step or
repeated Gamma label does not establish a break. If the user knows a break,
provide `--break-before` with 1-based sample indices. It disconnects the
preceding edge while retaining stored x distance; it does not compress the
interval or reconstruct geometry. Different labels at the same distance may
be combined; repeated labels at different distances remain distinct.

The helper does not interpolate, unfold, infer filling or certify a gap.
Missing labels remain numeric coordinates. For sampled edges use
[eigenvalue analysis](eigenvalue-analysis.md).

## Helper invocation

[plot_bands.py](../../scripts/plot_bands.py) requires Python 3.10+, NumPy and
Matplotlib. Use an available environment; do not silently install dependencies.
Replace `SKILL_ROOT` and `CASE` with actual paths. Write to the user's chosen
workspace. Options shown here belong to the helper, not the PASP executable.

```text
python -B SKILL_ROOT/knowledge/scripts/plot_bands.py CASE/spectrum --output-dir FIGURES --title "Band spectrum" --ispin 1 --ylim -6 8
python -B SKILL_ROOT/knowledge/scripts/plot_bands.py CASE/spectrum --output-dir FIGURES --name spectrum-ha --unit Ha --ylim -0.25 0.30 --formats png svg
python -B SKILL_ROOT/knowledge/scripts/plot_bands.py CASE/spectrum --output-dir FIGURES --name spectrum-ry --unit Ry --ylim -0.5 0.6
python -B SKILL_ROOT/knowledge/scripts/plot_bands.py CASE/spectrum --output-dir FIGURES --name custom --unit "kJ/mol" --units-per-hartree 2625.4996394799
python -B SKILL_ROOT/knowledge/scripts/plot_bands.py CASE/spectrum --output-dir FIGURES --name raw --absolute
python -B SKILL_ROOT/knowledge/scripts/plot_bands.py CASE/spectrum --output-dir FIGURES --name breaks --reference-ha -0.25 --break-before 81 122
```

The default unit is eV. Built-in factors per Hartree are eV 27.211386245988,
meV 27211.386245988, Ha/Hartree 1, and Ry/Rydberg 2. A custom unit name requires
`--units-per-hartree` with a positive finite factor. Built-in factors cannot
be overridden. `--ylim` and axis labels always use the selected final unit.
`--reference-ha` always takes Hartree, irrespective of plot unit; it is mutually
exclusive with `--absolute`. The default reference is the input header.

Default output basename is `bands`, with PNG/PDF/SVG and a JSON sidecar; select
formats with `--formats`. PNG uses 300 dpi, PDF embeds TrueType and SVG retains
text. If any target exists, the helper refuses the batch rather than overwriting.
The input stays read-only. Keep an error and any partial new files if export
fails, then choose a fresh basename for an authorized retry.

The JSON records input path/hash/size, spectrum shape, stored reference,
selected shift/unit/conversion, original labels, explicit breaks, window,
software versions and generated paths. Convergence/provenance remains unknown
until matched to log evidence. The reader limits input to 64 MiB, each line to
16 KiB and 2,000,000 eigenvalues. It accepts Fortran D/d exponents and rejects
nonfinite, truncated, out-of-order or extra inconsistent content rather than
silently truncating it. Use `--help` for the installed version's exact interface.

## Review and deliver

Inspect the PNG for readable labels, limits, ticks, crossings and missing glyphs.
Provide requested vector outputs plus JSON when available, explaining original
energy precision and matched-log status. English/Simplified/Traditional Chinese
analysis reports are available through the separate log/eigenvalue helpers;
the plot helper has no `--lang` option. Set an appropriate user-provided title
and confirm font coverage rather than assuming multilingual glyphs are installed.
