# PWRS: grids, filtering and compatibility

This packaged compatibility snapshot supports users with an executable and
their actual input/UPF/log files. It is not a release guarantee. Confirm unknown
features with the documentation shipped with the executable or a matching
successful example. Source access is not needed.

## Representation and grids

`DFT.RS T` selects PWRS; `DFT.Bfield T` also selects it. The snapshot permits
`DFT.ALGO 4` and `DFT.nb_pool 1`. Choose k pools using actual generated/reduced
points; see [parallel pools](../topics/kpoint-band-parallelism.md). One band pool does not
imply a one-rank job or promise speedup from extra ranks.

Do not migrate a legacy PWL input wholesale or remove every PWL-prefixed key.
`DFT.PWL.n0` is the magnetic flux control in the orbital-field branch;
`DFT.LPRECOND` is not the real-space preconditioner option selector. See [legacy controls](../topics/legacy-parameters.md)
and [magnetic preconditioning](../topics/magnetic-preconditioning.md).

PWRS orbitals live on a real-space grid. A physical normalization is

$$
\Delta V=\Omega/(n_xn_yn_z),\qquad
\sum_g\Delta V\,|\psi(r_g)|^2=1.
$$

Do not apply a PW coefficient normalization to a real-space wavefunction file
without its format convention. Scalar `ISPIN 1` and collinear/spinor
`ISPIN 2/4` must not be mistaken for four independent output-band channels.
Native bands are one eigenvalue list; band order cannot identify up/down spin.

Snapshot defaults are `DFT.ENCUT 10 Hartree` and `DFT.ENCUT_RHO` four times
ENCUT. In PWRS the orbital grid is not a PW sphere cut off by ENCUT. Density
cutoff and FFT-grid selection can change orbital discretization too. Record
the printed grid and converge the requested observables; do not treat these
cutoffs as fully independent accuracy controls. A discarded-density norm is
a representation diagnostic, not an SCF/eigenstate residual or continuum bound.

## Compatibility restrictions

| Area | Snapshot boundary |
| --- | --- |
| Pseudopotentials | NC only; do not infer USPP/PAW support |
| Solver/pools | ALGO 4; one band pool |
| Field off | Scalar finite-difference route; field-off ISPIN 2/4 restricted |
| Field on, zero flux | Magnetic initialization at zero flux; a distinct numerical control from field off |
| Field geometry | Quantized orbital field along direct lattice vector a3 |
| XC | Gradient XC with ISPIN 4 restricted |
| SOC/filtering | Filters 1-3 do not support the SOC combination in this snapshot |
| +U | PWRS +U restricted |
| Stress | A normal exit does not establish a usable PWRS total stress |

Finite-field SOC, force and variable-cell claims require evidence for the
specific executable and combination. Retain rejections; do not alter the
physical task or remove a check just to make a run complete.

## Projector filtering versus residual preconditioning

`DFT.RS.FILTER` can change the discretized Hamiltonian, energies and forces.
`DFT.RS.PRECONDITIONER` is intended to change convergence of the same
eigenproblem. They are different controls.

| FILTER | Snapshot interpretation |
| --- | --- |
| 0 | Unfiltered radial baseline |
| 1 | Compact Gaussian-mask radial filtering; NC, non-SOC, l=0-3 |
| 2 | Experimental Fourier-leakage filtering; NC, non-SOC, l=0-3 |
| 3 | Double-grid filtering; actual zero magnetic flux, NC, non-SOC |

Mode spelling can stay unchanged across releases with different behavior.
Do not use an older calculation to validate another executable. Start with a
supported baseline and vary one setting at a time. Do not invent FDF keys from
conceptual filter parameters.

For forces, converge grid, filtering and atomic displacement response together.
Compact support, interpolation and grid placement can affect energy smoothness.
Compare representative forces to reconverged displaced energies; agreement at
one geometry or a smooth SCF history does not validate derivatives.

## Experimental full density FFT box

`DFT.RS.DENSITY_FFT_BOX` defaults false. `DFT.RS.GRID_NX/NY/NZ` default zero and
are not ordinary grid overrides outside that mode. The snapshot experimental
workflow has narrow requirements: scalar local NC, LDA, SCF_ONLY, orthogonal
axis-aligned cell, direct density mixing and identity residual preconditioning,
plus release-specific checks. Explicit sizes require all three values at least 2.

Keep it off in ordinary new inputs. It is not a general PWRS recipe, dual-grid
method or proof of no aliasing. If explicitly requested, obtain the complete
matching release example/manual rather than copying one switch.

## Convergence and cost

See [output analysis](../topics/output-analysis.md) for stage-specific status. Inner
solver progress does not prove outer self-consistency; finite energy and normal
termination cannot turn MAXITER into success. Distinguish eigenstate residual,
orthogonality and density feedback when diagnostics are available.

`Shared-core solver detail` may report H calls/columns, preconditioner
calls/columns, orthogonalization, Rayleigh-Ritz and rotation times. Preserve
labels and scope. Components can overlap or be nested and can be rank-local;
do not sum them into wall time or call them MPI-global maxima.

Compare the same executable, Hamiltonian, initial state, targets, bands,
k sampling and resources. Include setup, complete solve, iteration counts and
peak memory when available. Fewer FFTs or faster operator calls alone do not
establish faster same-accuracy SCF; see [validation](../topics/validation.md).
