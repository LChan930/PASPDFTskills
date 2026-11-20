# Native fixed-cell ionic relaxation analysis

Use [analyze_relax.py](../../scripts/analyze_relax.py) on the native PASP log
from a single fixed-cell ionic relaxation. The log may have any filename.
Python 3.10+ and the standard library suffice for analysis and XYZ export.
PNG plotting requires Matplotlib. PASP.x, its source code, MPI, UPFs and
private launch scripts are unnecessary for this offline analysis.

Resolve `SKILL_ROOT` to the actual installed skill root. Run from the user's
working directory and choose new paths for any files you create.

```bash
python -B "$SKILL_ROOT/knowledge/scripts/analyze_relax.py" --help
python -B "$SKILL_ROOT/knowledge/scripts/analyze_relax.py" relax.answer
python -B "$SKILL_ROOT/knowledge/scripts/analyze_relax.py" relax.answer --input lattice_model.fdf --lang zh-Hant --format json --output relax-report.json
python -B "$SKILL_ROOT/knowledge/scripts/analyze_relax.py" relax.answer --plot relax-curves.png --xyz relax-last.xyz --symbols Ba Ti O O O
```

The optional FDF should belong to the same calculation. A supplied FDF records
requested settings and provides diagnostic thresholds. Check provenance with
the actual run records before attributing those settings to the executable.
English Markdown goes to stdout by default. Select Simplified Chinese with
`--lang zh-Hans` or Traditional Chinese with `--lang zh-Hant`. JSON keys and
status codes are stable across languages. Reports, plots and XYZ files use
exclusive creation.

## Read the run evidence

The analyzer reads step 0, subsequent ionic step headers printed after SCF,
and their complete position and force tables. It checks finite values and
consistent contiguous atom IDs. Each complete step reports energy and
adjacent-step energy differences in Ha, maximum per-atom Cartesian force
norm in Ha/Bohr and eV/Å, its atom ID, and log line evidence. A truncated table
can leave an earlier complete step available for inspection.

The JSON fields `ionic_exit`, `run_completion`, `electronic_status` and
`threshold` retain independent evidence. Use the explicit logger exit to
distinguish convergence from reaching the ionic step cap. A graceful process
ending and a finite force are insufficient to establish SCF convergence.
Check explicit SCF stop or failure evidence. For logs without this evidence,
report the electronic status as unconfirmed.

- A negative `DFT.EDIFFG` gives a force tolerance in eV/Å by its absolute
  value. Compare it with the maximum norm derived from the printed force
  components. If the rounding interval straddles the tolerance, the diagnostic
  is `within_rounding_uncertainty`.
- A positive `DFT.EDIFFG` specifies an energy tolerance in Ha. Differences
  between adjacent printed steps provide a diagnostic. Optimizer-specific
  stopping logic and printed rounding can affect the comparison.

| Exit code | Meaning |
| --- | --- |
| `0` | The log shows a recognized ionic outcome, convergence or the step cap, and a graceful ending without detected failure or ambiguity. |
| `1` | The log shows incomplete, failed or ambiguous evidence. Inspect the findings and any retained complete steps. |
| `2` | The command, input file or output path could not be used. |

Repeated or concatenated runs, unrelated logs and incomplete final records can
prevent a complete outcome. Use the evidence and step/line anchors in the report.
An ionic stopping decision remains specific to that run and its settings.

## Geometry and convergence artifacts

The report's `last_complete_geometry` is an indexed table of rounded Cartesian
coordinates in Bohr. Its step may precede the latest header in a failed or
truncated log. To create a chemical XYZ file, supply one actual element per atom
in the log's order using `--symbols`. The BaTiO3 command shows an example of
that order. XYZ converts the logged positions to Å for inspection and viewing.
Use a matching native full-precision structure with verified cell and species
when preparing a new calculation or restart.

`--plot` plots the retained per-step energy and maximum force in a PNG.
Both derived artifacts use complete retained steps and are available when
such data survive a failed or truncated run. Keep the accompanying report with
the plot or XYZ so that its run evidence and source precision remain visible.
