
## Native PW-MD analysis and provenance

### Standalone offline analyzer

Use the installed `knowledge/scripts/analyze_md.py` for actual native trajectory
validation and statistics. Python 3.10+ and the standard library suffice; optional
`--plot-dir` additionally requires Matplotlib. It needs no PASP executable, source
code, private utility or UPF. The input may have any filename. Resolve
`SKILL_ROOT` to the installed package's absolute root, and keep reports in the
user workspace. Read `--help` before choosing options.

```bash
python "$SKILL_ROOT/knowledge/scripts/analyze_md.py" "$RUN_DIR/output_MD.dat" --input "$RUN_DIR/lattice_model.fdf" --log "$RUN_DIR/log.out" --window-start-fs 2000 --window-end-fs 4000 --format json --output "$REPORT_DIR/md.json"
```

The example's 2000–4000 fs inclusive window is appropriate only when those times
actually exist. Omitting both window options uses the entire observed interval.
The report records requested bounds and the first/last selected samples. Empty,
reversed or out-of-range windows are errors. Statistics use the arithmetic mean,
population standard deviation, minimum and maximum, with units in field names.
This window does not certify equilibration.

The streaming reader validates finite time/energy and optional temperature,
all positions/velocities/forces, atom counts/IDs/species across sections and
frames, printed units, duplicate/incomplete records, consecutive steps and
uniform time spacing. It accepts the observed split-line NVE `Step`/`Time`,
`Etot` layout and the newer combined-header `E_tot` layout. Variable-cell frames
must contain complete three-row lattice and stress blocks; volume is the
absolute lattice determinant in cubic Angstroms. Mean diagonal stress is the
tensor trace divided by three; its pressure sign convention is not inferred.
When the native layout prints no temperature, the result is null, not a
fabricated temperature. Nonzero initial restart steps are preserved.

`--expected-steps N` means N updates from the observed initial step, usually
N+1 frames. Without that option, a supplied FDF's `PW_MD.nstep` provides the
requested comparison; without either, only the observed interval can be called
valid. `--dt-fs` provides an explicit spacing check; otherwise spacing is inferred
from observed frames and compared with a supplied FDF's requested dt. A missing
update cannot be inferred from two time samples without an independent expected
dt. Recursive input includes and their SHA-256 identities are recorded, but
settings remain **requested**, not runtime-effective. A requested ENCUT value
does not authenticate the actual run cutoff; do not pair a current 20 Ha input
with historical 2 Ha output as if it were one calculation.

An optional `--log` is matched against **all** trajectory step/time/printed
total-energy rows, including extra, missing or duplicate log rows. SCF failure
messages and renormalization diagnostics are counted separately. Repeated
legacy SCF failure messages are associated with the next printed MD row, with
that association stated explicitly. Graceful completion markers do not prove
electronic or physical convergence. Legacy logs with no explicit SCF result
protocol remain `no_explicit_protocol`; matching frames and a finish marker
establish a completed trajectory, not cutoff convergence or global SCF validity.

JSON status fields separate `trajectory`, `process_completion`,
`electronic_evidence`, and `physical_convergence`. A completed requested interval
is `complete_requested_updates`; an interval with no supplied requested length
is `valid_observed_interval`. Definite requested-control or log pairing errors
are reported separately. Ordinary Ep+Ek accounting is checked at printed
precision. A least-squares ordinary-energy slope is reported in Ha/ps only for
an explicitly requested NVE ensemble; conservation is never certified by that
slope. No NVT/NPT ordinary-energy conservation or NPH extended-enthalpy formula
is invented.

Default report language is English. Use `--lang zh-Hans` or `--lang zh-Hant` for
Simplified/Traditional Chinese explanatory text; JSON keys and stable status
codes remain machine-readable English. `--format markdown` is the default.
`--output` exclusively creates a new report and refuses overwrite. Optional
`--plot-dir` writes clean temperature (when printed), ordinary energy and cell
volume (when available) PNGs, also refusing existing names. Analysis has no
NumPy requirement. Exit 0 means no definite issue was found, **not** certified
physical accuracy; exit 1 covers invalid/truncated records, requested/log
mismatches, SCF failure evidence and I/O/plot errors; argparse uses exit 2 for
invalid CLI arguments. Invalid data produce a structured error report rather
than a successful-looking summary.

For native `DFT.LMD T` workflows, identify the actual main input and every `%include` before selecting a structure. A same-directory file such as `cell.str` is not evidence of the run structure unless referenced. Pair input, read-back (`PASP.used_info`), legacy log, trajectory and initial-state hashes; compare atom count, lattice, coordinates, velocities, energy, temperature and time range. Keep requested controls, read-back/default echoes and runtime-effective controls in separate fields. A read-back echo may precede later ensemble overrides; absence of a modern marker is not a failure.

Use the observed native trajectory schema rather than presumed columns: `Step`, `Time`, `Ep`, `Ek`, `Etot`, `Temp`, `H`, `fs`, positions/velocities, and for variable-cell runs lattice/stress with their printed units. A request for `N` updates commonly yields step 0 through `N` (`N+1` frames). Scan the whole legacy log for `PW_MD: self-consistent iteration failed`, report unique MD steps and repeated MPI messages separately, and preserve `LOBPCG error! Renormal` as a separate diagnostic. Completion markers and trajectory counts are independent evidence layers.

`PW_MD.init_velocity_tmp` and `PW_MD.velocity_temp` are observed historical spellings; do not claim they are aliases without matching release evidence. Initial velocity controls and observed step-0 temperature are distinct. If a log and trajectory disagree at step 0, keep them as separate artifacts until provenance is confirmed; do not join their SCF labels by directory name.

Interpret ensemble observables conservatively. NVE energy drift is meaningful only when the complete NVE control and energy definition are established. NPH can conserve a fully defined extended enthalpy; ordinary `Ep+Ek` is not automatically that quantity. NVT/NPT thermostat or barostat exchange means NVE drift tests do not apply. Variable-cell `Ep` may include pressure/volume bookkeeping; do not call it a standalone electronic ground-state energy. Temperature degree-of-freedom formulas are diagnostics, not universal assumptions. Report the actual statistics window and duration; a latter-half window is not certified equilibrium, and a near-zero-temperature NPT run is not a finite-temperature benchmark.
