---
name: pasp-dft
description: "准备与检查 PASP PW/PWRS 输入，指导 SCF、能带、磁性、SOC、DFT+U、固定晶胞离子弛豫和原生 MD，离线分析已有日志、弛豫、能级与 DOS，并绘制能带及电荷/电流场。"
---

# pasp_DFT

You are the entry skill for native PASP PW/PWRS DFT. The canonical invocation
is `$pasp-dft`; the display name is `pasp_DFT`.

Your responsibilities are only:

1. Classify the request as workflow, reference or mixed.
2. Read the smallest relevant local instruction file below.
3. For a skill-version query, read [VERSION](VERSION) in this package. Keep it
   separate from the user's PASP executable version.

Keep parameter dictionaries and stage-specific details downstream.

## Resource paths

The skill root is the directory of this loaded top-level `SKILL.md`, resolving
its symlink to the actual resource package when applicable. Discover it from
the loaded entry; never assume the user's current directory is the package.
The usual project installation is `<project>/.agents/skills/pasp-dft/`.

Bare `knowledge/...` and `subskills/...` paths are relative to that root.
Markdown links and explicit `./` or `../` paths are relative to their document.
User inputs, run directories and generated reports belong to the user's
workspace. Invoke scripts using a quoted absolute skill-root path; pass that
same resolved root to downstream readers. Do not change into the package or
create a `skills/` alias to make examples work. See [README](README.md) for
portable shell examples and installation.

## Routing

- Task, preparation, input changes, current stage or next step: read the
  [workflow controller](subskills/pasp-dft-orchestrator/skill.md).
- Exact field meaning, syntax, units, defaults, conditional rules or file
  format: read [reference lookup](subskills/pasp-dft-reference/skill.md).
- Mixed task and parameter questions: identify the stage through workflow
  first, then load only its needed reference details.
- Bounded read-only fact collection requested downstream: follow the
  [verifier contract](subskills/pasp-dft-verifier/skill.md). It does not choose
  scientific settings, edit inputs, submit jobs or replace the final answer.

Files under `subskills/` are local instruction files. Read them normally;
do not invoke colon-qualified nested skill names or assume separate registration.

## Supported workflows

- Deterministic offline input auditing with `knowledge/scripts/audit_inputs.py`: recursive includes, dependencies, documented defaults and pool consistency. Read the [input audit contract](knowledge/reference/topics/input-audit.md); physical choices and release compatibility still require interpretation.
- PW SCF, fixed-density path bands and SCF-reference handoff.
- Collinear magnetism, AFM and DFT+U.
- Noncollinear and SOC comparisons.
- Fixed-cell ionic relaxation and offline analysis of native relaxation logs
  with `knowledge/scripts/analyze_relax.py`. See the
  [relaxation analysis contract](knowledge/reference/topics/relaxation-analysis.md).
- PWRS orbital magnetic fields, zero/finite flux and boundary settings.
- Native ionic MD with its supported ensemble branches.
- Native MD frame, time, energy, temperature and log consistency analysis with `knowledge/scripts/analyze_md.py`; read the [MD analysis contract](knowledge/reference/topics/md-analysis.md). File completeness does not certify physical convergence.
- Existing-output analysis: logs, eigenvalues, sampled band edges, DOS and MD
  interpretation, band figures, and native charge/current field slices or
  whole-cell integrals. For fields, load the
  [field reference](knowledge/reference/topics/field-plotting.md) and the
  installed `knowledge/scripts/plot_fields.py --help` through the output route.

## Operational notes

Runtime guidance uses this package plus the user's authorized `PASP.x`, release
documentation, inputs, UPFs and results. Existing-output analysis does not
require PASP execution. Do not require source code, private paths or build tools,
or invent executable version/dry-run flags. LCAO and other models belong to
their own skills. Unsupported or undocumented behavior remains an evidence gap.

Use actual file content and provenance, including arbitrary log filenames.
Workflow state, input dependencies, scientific choices, report language/units
and slice-versus-integral semantics remain in downstream resources. Keep
limitations and convergence evidence in accompanying reports/JSON, outside
scientific plots. Preserve existing authorization; do not add repeated approvals.
