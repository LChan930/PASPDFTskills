# Native spectra: what can be analyzed offline

This guide describes the packaged compatibility snapshot and its offline
helpers. It does not guarantee additional analysis features in an unidentified
PASP executable. Use the user's actual input/log and the manual supplied with
that executable when a native feature is uncertain.

Ordinary native PW/PWRS path output supplies an eigenvalue spectrum and energy
reference. Do not assume that writing a band file also produces a complete
band-gap, effective-mass, Fermi-surface or orbital-projection report. A file
called `Eg.dat` may belong to another model or external-data workflow; inspect
its provenance and units rather than treating its name as a native DFT contract.

## Choose the appropriate offline tool

| Question | Packaged workflow | Evidence boundary |
| --- | --- | --- |
| Did each SCF/path stage meet its reported criterion? | [Output analysis](output-analysis.md) | Recognized log evidence, not physical certification |
| Can I plot the existing native path spectrum? | [Band plotting](band-plotting.md) | Stored path order and precision only |
| Where are sampled band edges under a declared filling? | [Eigenvalue analysis](eigenvalue-analysis.md) | Conditional sampled edges and differences |
| Is a DOS integral or normalization plausible? | [DOS guide](dos.md) | Actual file's units, bins, weights and sampling |

Do not activate EPC/EPR, topology or MD just to obtain an ordinary gap query.
Those are distinct physical tasks and may alter the calculation or require
special prerequisites. A task-specific band-isolation check is not a general
postprocessing report. Missing native reporting is not a reason to require
source access: analyze the available files within their evidence limits.

## Information a spectrum cannot supply

A cumulative one-dimensional path distance does not reconstruct three-dimensional
k vectors. A constant channel-count field does not identify ISPIN. Band index
halves do not identify spin projection. Rounded energies do not gain precision
when converted to eV. Path labels do not define missing path discontinuities.

A positive path or sampled-mesh gap is not proof of full-Brillouin-zone
insulating behavior. Effective masses require adequately resolved curvature
near the actual band extremum, physical reciprocal-space coordinates and the
appropriate directional/tensor fit. Fermi surfaces need suitable bulk sampling
and filling. Atomic/orbital/spin projections require genuine state-resolved
projection data. Do not synthesize any of these from an unlabelled eigenvalue
list or claim the packaged helpers implement them.

Keep unknown provenance, missing occupations, MAXITER, finite smearing and
unconverged sampling visible. A useful report can give a plot and conditional
sampled edges while clearly stating what remains unestablished.
