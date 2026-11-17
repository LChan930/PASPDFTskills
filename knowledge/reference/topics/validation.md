# Validation and reporting with an executable

Use the user's available inputs, UPFs, launch scripts, logs and result files.
This guide is self-contained: it requires no private repository, source tests
or build tools. Loading the skill does not authorize starting a new PASP run,
MPI job, long material calculation or download. Analyze existing evidence first;
run a calculation only within the user's requested scope.

## Distinguish evidence levels

| Evidence | What it supports | What it does not establish |
| --- | --- | --- |
| Input/UPF inspection | Intended model, units, species and requested features | Actual acceptance or successful execution |
| Recognized log/protocol | Observed stages, status and printed quantities for that run | Unprinted checks or support in every release |
| Offline helper success | The supplied file matches that helper's accepted format | Convergence, physical validity or a PASP run |
| Completed SCF with accepted status | That executable's stopping rule was met | Ground state or cutoff/k/grid convergence |
| Converged parameter/displacement study | Requested observables within declared tolerances over tested cases | All materials, fields or spin states |
| Actual multi-rank run | Observed behavior for its ranks/pools/input | General parallel correctness or speedup |
| Repeated matched-accuracy timing | Performance for that problem and resource setup | A universal speedup |

Record executable identity/version if known, input/includes, UPF identities and
metadata, restart files, lattice, k sampling, band count, occupations, spin,
field and numerical controls. Checksums help distinguish artifacts but are not
proof of physical compatibility. Do not invent a version flag or dry-run mode;
use the site's documented invocation and already printed metadata.

## SCF and band status

Interpret each stage independently; see [output analysis](output-analysis.md).
`PASP_SCF_RESULT status=LEGACY_CONVERGED` means the recognized legacy stopping
rule was met. `certified=F` says an additional outer certification is absent;
it alone is not a failure flag. Inner eigenstate convergence and outer density
self-consistency are separate questions.

`MAXITER` means the budget was exhausted without accepted convergence. A finite
last energy, density, force, stress, written spectrum or zero process exit does
not make it converged. `NUMERICAL_FAILURE`, nonfinite numerical fields and
explicit runtime errors must remain visible even if an earlier stage succeeded.
A huge residual-like number can be a placeholder for an unmeasured diagnostic;
check labels and context before calling it a measured error.

`PASP_BAND_RESULT status=EIGENVALUES_CONVERGED` concerns the fixed-density path
eigenvalue criterion. Check the matching SCF reference and status; path success
is not a second SCF or a certified band gap. Graceful termination, scheduler
COMPLETED and shell exit zero describe completion at their respective levels,
not physical accuracy. Unknown/old log protocols remain unknown.

## Converge the requested observable

Declare tolerances before comparing results. Vary relevant controls separately:
cutoffs/grids, bulk k mesh, empty bands, occupation width, SCF/eigensolver targets
and requested force/stress tolerances. Preserve the same lattice, UPFs, XC,
magnetic order and physical field unless that physical change is intentional.
A path gap is only a sampled path quantity; a positive difference does not
prove an insulating full Brillouin zone.

For magnetic systems, inspect the final state rather than initial MAGMOM.
Total magnetization near zero can be antiferromagnetic or nonmagnetic; local
moments and state comparisons are needed. +U values/projectors and SOC choices
must be held fixed in a numerical convergence study. Do not choose U or a
radius merely to erase a residual stress or obtain an expected gap.

## Energy, force and stress checks

For the recognized energy labels, the accounting convention is

$$
E_{\mathrm{tot}}=E_{\mathrm{band}}-\mathrm{deband}+E_H+E_{\mathrm{xc}}+E_{\mathrm{II}}+E_{\mathrm{dip}}+E_U.
$$

The printed list `eband,-deband,EH,Exc,EII,Edip` already contains a signed second
term. Add those values directly and include separately printed EHub when +U
is enabled. Do not subtract a double-counting contribution again. An omitted
line is missing evidence, not automatically zero. Respect printed precision;
rounded components cannot certify smaller differences than their rounding.
An energy-contraction consistency check is not proof of a ground state.

A total-force finite-difference check compares reconverged, otherwise matching
calculations at displaced geometries:

$$
F_a\approx-\frac{E(R+h e_a)-E(R-h e_a)}{2h}.
$$

Use several physically appropriate step sizes and retain original energies and
failures. Too-small steps amplify rounding and SCF noise; too-large steps probe
nonlinear response. Check whether a free energy rather than internal energy is
required for the occupation scheme. Do not claim a derivative validation from
one displacement or from unconverged electronic states.

For stress, verify units, sign, volume normalization and strain convention.
Recognized ordinary PW output uses Ha/Bohr^3 and kbar, with positive compression;
1 kbar = 0.1 GPa. Confirm this convention for the actual log. Electronic SCF at
fixed lattice can retain nonzero stress. A normal PWRS exit does not establish
that a total-stress feature is supported; consult actual release evidence.

## MD checks

Check every electronic stage, actual trajectory length, time-step convergence,
geometry/velocity units, intended ensemble and energy drift. A trajectory file
or a graceful ending does not prove stable dynamics. Native DFT `PW_MD.*` and
effective-H `MD.*` describe different models; see [scope](upstream.md).
Magnetic/geometric forces and variable-cell dynamics need specific compatibility
evidence. Do not launch long trajectories solely to validate an offline report.

## Performance with comparable accuracy

Keep executable, input, initial state, H, stopping targets, bands, k points,
restart policy and resources fixed. Record ranks, pools, threads, affinity,
node type, elapsed wall time, repetitions and fluctuation. Include startup,
setup, full SCF and postprocessing in the declared timing scope. Separate cold
and warm starts and identify memory measurements as local or global.

Field-off PWRS and field-on/zero-flux PWRS are different numerical controls.
Compare each explicitly. For a preconditioner comparison, use identity mode 0
at the same actual H as the baseline; do not change a filter or physical field
at the same time. First establish comparable physical accuracy across PW/PWRS
before interpreting their time ratio.

Component times can overlap or be nested. Rank-local timing is not MPI sum or
maximum. Fewer H calls, faster kernels or cache reuse do not prove faster full
SCF. Keep timeout, MAXITER, incompatible provenance and failed accuracy cases
in the report; do not compute a valid speedup from them.

## Deliver a reviewable result

Give the files examined, stage-specific conclusions and their exact line
anchors, assumptions, units/reference choices, actual helper commands and any
new output paths. State what was not available or run. Preserve raw errors and
uncertainties. Do not report private test counts, historical PASS labels or
unperformed physical/MPI checks as evidence for the user's executable.
