# Orbital-field setup and real-space preconditioner options

This operational reference is a packaged compatibility snapshot, not an official
release manual or a guarantee for every PASP executable. It records actual input
spellings and recognized log evidence without describing unpublished methods.
Names appearing inside existing input keys or log tags are compatibility strings,
not an official method name. Use the manual supplied with the executable or a
matching successful input/log when compatibility is uncertain.

For representation, spin and filter restrictions read [PWRS](../modules/pwrs.md). For
ordinary input construction use [input generation](input-generation.md).

## Establish the requested field

`DFT.Bfield T` selects the snapshot orbital-field PWRS workflow. Its field is
quantized through the a1/a2 lattice face and directed along direct lattice
vector a3. In a skew cell a3 need not be the face normal. This is not a general
Cartesian B-vector interface: do not invent component or gauge input keys.

`DFT.PWL.n0` is the integer flux control for this branch, with snapshot default
1; positive, negative and zero integers are valid. Confirm the actual lattice,
orientation, field request and printed setup. Changing the cell at fixed integer
flux also changes the physical field. Enabling Bfield selects the snapshot
all-k magnetic workflow; use the actual generated point count for pool selection.

A field-off run and a field-on/n0=0 run are different numerical controls. Keep
the distinction visible in an audit or comparison. An absent field switch must
not be interpreted as an implicitly enabled finite field.

## Select a real-space preconditioner option

`DFT.RS.PRECONDITIONER` is the integer option selector and defaults to 0.
Enabling the field does not automatically choose option 4. `DFT.LPRECOND` is
not its enabling switch; do not add that legacy key for this purpose.

| Option | Operational compatibility in this snapshot |
| --- | --- |
| 0 | Default baseline option |
| 1 | Available selector value; confirm suitability with the executable's supplied documentation/example |
| 2 | Experimental option requiring magnetic initialization in this snapshot; do not recommend it without matching evidence |
| 3 | Actual zero flux required; nonzero flux restricted |
| 4 | Requires Bfield initialization and the supported a3/gauge convention; positive, negative or zero integer flux |

All PWRS limitations remain in force: ALGO 4, one band pool and compatible
NC/spin/XC/filter settings. The separate experimental full density FFT-box
workflow instead requires option 0 and its own narrow compatibility conditions.
A selectable option is not a claim of universal support or acceleration.

The fragments below only show confirmed selection syntax. They are not complete
material inputs. Retain the user's structure, UPFs, XC, bands, sampling and
required numerical controls.

```text
# Actual zero-flux PWRS task; check all other compatibility conditions
DFT.RS T
DFT.RS.PRECONDITIONER 3
```

```text
# Orbital-field task; field set by the actual cell and integer flux
DFT.Bfield T
DFT.PWL.n0 1
DFT.RS.PRECONDITIONER 4
```

Do not add option-specific tuning keys when their packaged defaults suffice.
Do not change option, physical field or coefficients solely to suppress a
failure without understanding the user's requested calculation.

## Existing coefficient keys

The following are existing compatibility spellings, not method names. Their
numbers are snapshot defaults, not universally optimized material parameters.
They are bare atomic-unit controls; do not append generic FDF unit suffixes
without matching release documentation. Preserve intentional user values and
record any actual change.

| Existing input key | Snapshot default | Accepted value requirement |
| --- | --- | --- |
| `DFT.RS.GAPP.TAU` | 1.63 | Finite positive |
| `DFT.RS.GAPP.WEIGHT` | 2.73 | Finite nonnegative |
| `DFT.RS.GAPP.DELTA` | 7.89 | Finite positive |
| `DFT.RS.MAGNETIC_GAUSSIAN.TIME` | 0.18818924310286425 | Finite positive |
| `DFT.RS.MAGNETIC_GAUSSIAN.AMPLITUDE` | 7.02028330509751 | Finite nonnegative |
| `DFT.RS.MAGNETIC_GAUSSIAN.LOCAL` | 0.10093129881850713 | Finite positive |

The first three belong to option 3; the final three belong to option 4 in this
snapshot. Do not assume invalid values will be ignored in an inactive option.
Use a release-specific supplied example if units or tuning behavior matter to
the task; this operational page makes no method or derivation claim.

## Read status and retain evidence

Recognized logs can include `PASP_RS_GAUSSIAN_SETUP`. Preserve that exact tag and
its printed fields when reporting the run; it is a compatibility identifier,
not an official name. Setup fields such as seconds, retained bytes/MiB, k,
reason or counts describe the reported scope only. They do not establish global
memory, total wall time, numerical convergence or a speedup. Missing diagnostic
text is not proof of inactivity in an older/different executable.

Use [output analysis](output-analysis.md) for the separate SCF/path status.
Retain explicit rejection, MAXITER, nonfinite values and missing evidence.
Do not reinterpret a completed setup or a zero exit code as physical success.
If a comparison is requested, follow the ordinary matched-input and declared
accuracy reporting rules in [validation](validation.md); no performance promise
or explanation of the unpublished option is supplied here.
