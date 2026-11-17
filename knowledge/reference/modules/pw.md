# PW calculations and shared DFT workflows

This packaged reference is a compatibility snapshot for users with a PASP
executable, their inputs, UPFs and logs. It is not an official release manual
or a guarantee for an unidentified executable. Confirm uncertain combinations
with the documentation supplied with that executable or a matching successful
input/log. No source tree or development repository is needed.

Start with [input generation](../topics/input-generation.md) for complete input syntax
and detailed parameter tables. Related guides cover [PWRS](pwrs.md),
[orbital fields](../topics/magnetic-preconditioning.md), [parallel pools](../topics/kpoint-band-parallelism.md)
and [validation](../topics/validation.md).

## Identify the calculation and retain intent

Read the actual main input and all includes. `Model DFT` selects native DFT in
this snapshot. `DFT.RS T` selects PWRS; `DFT.Bfield T` also selects PWRS.
Local real-space replacement settings in a PW input do not imply full PWRS.
File names such as `MD.input` do not select the physical model.

Keep the user's structure, species order, pseudopotentials, XC, magnetic order
and intentional nondefault controls. Defaults are compatibility facts, not
material recommendations or convergence evidence. Do not copy the entire
parameter catalogue into a new input or silently delete uncertain settings
from an existing one.

## Common controls

The following defaults belong to this packaged snapshot. Check the detailed
parameter references and actual executable evidence before relying on them.

| Key | Snapshot default or convention |
| --- | --- |
| `DFT.home_made` | true; ordinarily omit the redundant default |
| `DFT.RS`, `DFT.Bfield`, `DFT.SCF_ONLY` | false |
| `DFT.nk_pool`, `DFT.nb_pool` | 1, 1 |
| `DFT.ENCUT` | 10 Hartree |
| `DFT.ENCUT_RHO` | Four times the selected ENCUT |
| `DFT.ALGO`, `DFT.ISPIN` | 4, 1 |
| `DFT.NELM`, `DFT.EDIFF` | 500, `1.0d-4` Hartree |
| `DFT.mixing`, `DFT.mixing_mag` | 0.1, 0.1; dimensionless |
| `DFT.mixing.method`, `DFT.mixing.Pulay_m` | 2, 6; methods 1/2/3 are linear/Pulay/Broyden |
| `DFT.ISMEAR`, `DFT.SIGMA` | -1, 0.007 Hartree |
| `DFT.lusesym`, `DFT.luse_all_kpoints` | true, false; all-k selection overrides symmetry reduction |
| `DFT.lbandstructure`, `DFT.NBAND` | false, 0; zero requests automatic band count |
| `DFT.LCHARG`, `DFT.RCHARG`, `DFT.LWAVE`, `DFT.RWAVE` | Integer 0; enable with integer 1, not T/F |
| `DFT.VLOC_RCUT` | 10 Bohr; explicit values require a length unit |

Turning off spatial symmetry alone need not remove time-reversal reduction.
Choose pools from actual generated/reduced points, not the raw mesh product.
Do not change sampling or symmetry just to fit a resource request. Nonzero
initial MAGMOM does not establish a magnetic ground state or an insulating gap.

## SCF to path bands

For a fresh SCF intended to supply bands, retain `DFT.LCHARG 1` and the intended
SCF mesh. In this snapshot `DFT.SCF_ONLY T` returns before ordinary density
handoff, so it is not a shortcut for producing that handoff. The path input
needs `DFT.lbandstructure T`, sufficient `DFT.NBAND`, `BandLinesScale` and complete
`BandLines`. Its path replaces the SCF mesh. Adding `DFT.RCHARG 1` does not
replace the required valid SCF restart pair.

The typical pair is `CHGCAR` plus `CHGCAR.restart`; keep renamed density files
paired with the corresponding metadata according to the applicable release.
Copy original bytes and line endings. This is not VASP's CHGCAR format. Do not
edit a stored status or reconstruct a reference energy from a rounded log.

Recognized metadata begins `PASP_DFT_RESTART 1`. `DENSITY_BYTES` and
`DENSITY_ADLER32` bind metadata to density bytes; `EF_HARTREE` stores the reference
in Hartree. Geometry, spin, electron count and producer status must also match.
The checksum is not a full pseudopotential or Hamiltonian fingerprint: retain
compatible UPFs and physical settings. A legacy density without metadata may
be usable for an ordinary restart, but cannot establish the path-band reference.
Corrupt, unknown-version or mismatched metadata should not be bypassed.

The recognized path workflow requires an accepted SCF producer
(`SCF/LEGACY_CONVERGED`) and prints markers such as:

```text
PASP_BAND_REFERENCE source=SCF_RESTART ... occupations=PLOT_ONLY
PASP_BAND_RESULT status=EIGENVALUES_CONVERGED iterations=...
```

It uses fixed SCF density and the SCF energy reference, rather than fitting
bulk occupations or a new Fermi energy to a high-symmetry path. `MAXITER` can
leave finite last-iteration bands and must be reported as unconverged. The
recognized success criterion concerns eigenvalue changes; it is not a proof
of eigenvector residual, cutoff convergence or gap accuracy. A single iteration
cannot demonstrate an inter-iteration change criterion.

See [band plotting](../topics/band-plotting.md) for raw versus shifted energies and
[eigenvalue analysis](../topics/eigenvalue-analysis.md) for conditional sampled edges.

## Mixing and site moments

Charge and magnetic damping can affect different quantities across mixing
schemes and +U. Changing `mixing_mag` alone is not guaranteed to change every
magnetic update. Use supported methods and inspect convergence histories rather
than assuming a parsed parameter has the intended effect in every workflow.

`DFT.RWIGS` defines species-ordered spherical site-moment integration radii, not
a mixing parameter, initial MAGMOM radius or Hubbard projector radius. The
snapshot syntax is a block of bare Angstrom radii, one per species:

```text
%block DFT.RWIGS
2.0
%endblock DFT.RWIGS
```

This is one-species syntax, not a recommended radius. Use positive finite
radii and test radius sensitivity. An absent block does not imply an automatic
element radius. A single-line form may report `FDF_BLOCK: Not a block`.
Spheres can overlap and do not form a unique partition of magnetization.
Check site-moment printing in the actual spin mode/log; total magnetization is
not an individual atom's moment.

## Local potential cutoff

`DFT.VLOC_RCUT 14 Bohr` illustrates explicit units, not a recommendation.
`DFT.VLOC_RCUT 0 Bohr` denotes the snapshot legacy full radial-grid choice.
Negative/nonfinite radii are invalid. A positive cutoff selects a radial-grid
prefix whose endpoint need not exactly equal the requested radius. Do not
truncate the UPF itself: this control does not globally shorten nonlocal
projectors, correlated orbitals or core charge. Converge requested energies,
forces and stress rather than assuming the default is optimal for every UPF.

## SOC and DFT+U

Check actual UPF relativistic metadata and pseudopotential type. A successful
scalar run does not establish SOC support. The snapshot restricts gradient XC
with `DFT.ISPIN 4`; do not claim general noncollinear GGA. PWRS filters and
finite orbital fields add compatibility restrictions; see [PWRS](pwrs.md).

Native +U uses `DFT.n_manifolds_plus_U`, `DFT.plusU_type` and a `DFT_plus_U`
block. Type 1 uses Hartree Ueff; type 2 uses U/J. Obtain full block syntax from
[auxiliary parameters](../params/input-parameters-auxiliary.md) or a matching release
example; do not guess shell/site columns. U/J, correlated shells, atom/species
mapping, projectors and magnetic order are physical inputs, not universal defaults.

Keep matching `PLUS_U_NS` auxiliary occupations when a restart/handoff needs
them. File existence or equal dimensions does not establish compatibility of
species, sites, U/J or correlated subspaces, and does not restore mixing history.
Charge density alone cannot reconstruct these occupations.

Snapshot restrictions include PWRS +U, SCF_ONLY +U, RRAM +U and type-2 g shells.
Do not bypass a rejection. Type-2 f-shell anisotropy conventions require the
intended physical model to be confirmed. Availability of a +U switch does not
validate arbitrary materials, SOC/MPI combinations or forces/stress.

## Berry, Chern and molecular dynamics

Electronic Berry phase, k-space Chern number and nuclear-coordinate molecular
Berry curvature are different observables. Use task-specific controls and
interpret their results separately. A topology-related gap check is not a
general material gap report.

The snapshot Chern workflow is restricted to NC, `ISPIN 1/2`, a single k pool
and single band pool, and sufficient occupied/empty states. It requires the
complete requested integration plane rather than an arbitrary SCF irreducible
mesh or path. Band-selection spellings include `DFT.LBERRY.NINT` and
`DFT.LBERRY.NEND`. Verify eigenstate convergence, constant occupied dimension,
band-group isolation, link validity, mesh convergence and orientation/sign
conventions. Preserve noninteger results; never replace a failed calculation
with zero or round away poor convergence. A positive sampled gap does not
establish a continuous insulating manifold.

Native ionic MD uses `Model DFT`, `DFT.LMD T` and `PW_MD.*`, distinct from
effective-H dynamics; see [scope](../topics/upstream.md).

| Native key | Snapshot convention |
| --- | --- |
| `PW_MD.dt` | 1.0 fs default; bare values use fs here |
| `PW_MD.nstep` | 10 default |
| `PW_MD.temperature` | 0 K default |
| `PW_MD.velocity_temp` | Defaults to temperature |
| `PW_MD.lmolBC` | Defaults to orbital-field choice |
| `PW_MD.solver`, `PW_MD.thermostat` | Magnetic/geometric-force route: 3/0 |
| `PW_MD.ensemble`, `PW_MD.barostat` | Magnetic/geometric-force route: 1/0 |

These describe the restricted NVE leapfrog route, not general ensemble support.
`DFT.delta_tau` for molecular Berry displacements is positive finite Bohr.
Do not reuse a displaced-state snapshot without matching geometry and state
provenance. Disabling molecular Berry force need not disable ionic Lorentz
force in an orbital-field run. Verify every electronic step, time-step
convergence, velocity initialization and energy drift; variable-cell field
dynamics needs separate release-specific evidence.

### Native MD interpretation boundary

Native `PW_MD.*` output requires provenance-aware interpretation. `Ep`, `Ek` and `Etot` labels are reported terms; in NPH/NPT, `Ep` can include pressure/volume bookkeeping and need not equal an isolated electronic total. NVE drift is an appropriate diagnostic only for NVE with a defined conserved energy. NPH may conserve an extended enthalpy when all terms are defined, while NVT/NPT exchange heat or work with controls. State temperature degree-of-freedom assumptions explicitly and report the measured window and duration. Do not treat a near-zero-temperature NPT case as a finite-temperature benchmark.
