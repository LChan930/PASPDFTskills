# Native PW/PWRS density of states

This compatibility snapshot concerns native PW/PWRS files. First establish run
provenance and convergence with [output analysis](output-analysis.md). A native
`DOSCAR` is not automatically a VASP-format file. Its name alone does not
identify units, channel definitions or the generating workflow.

## Workflow and controls

In the packaged snapshot, Gaussian occupations (`DFT.ISMEAR 0`) are associated
with native DOS generation in the ordinary SCF workflow. SCF_ONLY can omit the
ordinary output stage, and MAXITER can leave a DOS file. A fixed-density NSCF
input does not by itself guarantee that this executable writes a DOS file.
Confirm the actual log and output rather than promising a complete dense-mesh
NSCF-to-DOS workflow.

Path bands (`DFT.lbandstructure T`) are plot-only with a preserved SCF reference;
a high-symmetry path is not a bulk k integration mesh. Do not redefine its
Fermi energy or treat path weights as DOS integration weights. The separate
`DensityOfStates` block is not interchangeable with the native DFT DOS controls.

| Parameter | Snapshot convention |
| --- | --- |
| `DFT.ISMEAR` | Default -1; Gaussian 0; do not infer MP order from a positive integer |
| `DFT.SIGMA` | Default 0.007 Hartree as a bare number |
| `DFT.NEDOS` | Default 301; use at least 2 and check resolution |
| `OccupationFunction` | Default `FD`; explicit `MP` selects that occupation family where supported |
| `OccupationMPOrder` | Default 1 for the MP choice; no DFT prefix |
| `SingleExcitation` | Not a DOS output switch; changes filling behavior |

Use a positive finite width. Do not rely on invalid-input rejection or an
absolute-value treatment of a negative width being identical across versions.
Changing occupation scheme changes the calculation: do not replace FD/MP with
Gaussian merely to obtain a missing file without the user's physical intent.
Converge width and bulk k mesh separately.

## Count states and identify the width convention

For normalized k weights, scalar spin-degenerate states carry a factor 2;
`ISPIN 2/4` native states do not acquire an extra factor 2. The Gaussian
cumulative-state convention in the snapshot is

$$
I(E)=r_s\sum_{nk}w_k\frac{1+\operatorname{erf}[(E-\epsilon_{nk})/\sigma]}{2},
\qquad r_s=2\ (\mathrm{ISPIN}=1),\quad r_s=1\ (\mathrm{ISPIN}=2/4).
$$

Here SIGMA corresponds to standard deviation $\sigma/\sqrt{2}$, so widths from
other tools may require conversion. The native DOS may be represented as
finite-bin differences of the cumulative distribution, labeled at bin right
edges, rather than point samples of a Gaussian. Confirm file/version semantics
before calling a half-bin visual displacement an error.

Printed SCF `weight` values can combine occupation, k weight and spin counting.
Do not apply them as pure occupation probabilities or multiply by k/spin
weights a second time. Native total DOS does not provide spin-up/down, atomic
or orbital projections merely because the calculation is magnetic. Never infer
such channels from band-number halves.

## Recognized file and energy units

The recognized header has Emax/Emin/nEdos/EF labels followed by
`# E(Ha) dos(E) Int dos(E)`. Its three columns are absolute energy in Hartree,
DOS in states/Hartree per simulation cell, and cumulative states per cell.
They are not automatically normalized by volume or atom count. The cumulative
value at the upper edge counts represented states, not necessarily the number
of electrons; compare electron filling at the actual reference as appropriate.

For $E'=C(E-E_F)$, transform the density consistently:

$$
D'(E')=D(E)/C.
$$

The cumulative count is unchanged. With the default plotting unit eV,
$C=27.211386245988$ eV/Ha. Record reference subtraction and unit conversion
separately. A plot of DOS in states/eV with unscaled states/Ha values is wrong.

## Audit before interpreting fine structure

Check that energies are ordered and distinct at the available print precision,
all values are finite, bins resolve the chosen width, and the energy window
covers the tails of the represented states. Compare a discrete DOS integral
using the file's bin convention against the cumulative-count change. A coarse
window/grid can lose apparent spectral weight; refining NEDOS in one example
does not prove every window is adequate.

Legacy text output may round energies to 0.0001 Ha (about 2.72 meV), yielding
repeated printed energies on fine grids. Do not infer physical degeneracy or
sub-meV structure from those repetitions, or silently perturb the energy axis
to force an integral. Request higher-precision data or a documented output
format when needed.

Keep a mismatch as a diagnostic: distinguish bin-versus-point semantics,
truncated tails, insufficient empty states, duplicate rounded energies,
unconverged occupations and unknown output provenance. A valid integral does
not establish SCF or k-mesh convergence. A file at EF near zero is not, by
itself, proof of a band gap; smearing, sampling and resolution can all matter.

## Tool boundary

The packaged log helper inventories DOS artifacts; it does not promise a
universal DOS reader or PDOS reconstruction. Inspect the actual text and units
before any user-requested custom analysis. Native band plotting and sampled
band-edge analysis are separate helpers described in [band plotting](band-plotting.md)
and [eigenvalue analysis](eigenvalue-analysis.md). None of these launches PASP
or establishes unsupported DOS features in the installed executable.
