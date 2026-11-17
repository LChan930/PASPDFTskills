# Submission scripts and log troubleshooting

Use this guide for user-supplied workshop or cluster launch files. The skill
does not ship or require a particular workshop directory, submission helper,
module environment or cluster layout. Examples of names below are conventions
to recognize in the user's files, not promised PASP commands or dependencies.
Do not submit a job merely to inspect an existing failure.

## Establish the actual launch route

Read the user's submission script, any scripts it invokes, the input/includes
and the scheduler stdout/stderr paths. Record the requested calculation,
working directory, executable path and argument/stdin convention. Use only the
invocation documented for that installation: do not invent PASP CLI flags,
`--version`, dry-run or input-file switches.

Names such as `sub_pasp` and `run.sh` are local wrappers, not a universal PASP
interface. Determine whether a root wrapper expects a case argument or a local
wrapper expects none by reading that actual file. Do not replace a multistage
SCF-to-bands controller with a generic command: it may protect restart pairs,
prevent overwrite and check stage-specific statuses.

Slurm can execute a spool copy of a submission script. `$0` therefore need not
identify the original case directory. Check `SLURM_SUBMIT_DIR`, the script's
working-directory logic and any `#SBATCH --chdir` or command-line override.
A local wrapper error about its own case directory may mean the directory is
wrong, a shared helper is missing, or the wrapper was copied separately.
Symbolic links alone do not establish the cause; compare the actual target
identities and paths. Do not prescribe `cd -P` as a universal repair.

## Executable and runtime environment

A file named PASP.x in the current directory need not be the one launched.
Resolve the configured path used by the actual script, including any environment
variable precedence. Check existence, execution permission and runtime library
errors. Preserve the installation's documented modules/environment rather than
loading an arbitrary compiler or MPI stack. A script-local variable such as
`PASP_EXE`, `PASP_BIN_DIR` or `MPI_NP` has meaning only if that script uses it.

Compare scheduler allocation with launcher ranks and thread settings. In Slurm,
inspect `SLURM_NTASKS`, `SLURM_CPUS_PER_TASK` and any overrides, then compare
OMP/MKL threads and affinity against allocated CPUs. Do not infer a universal
rank count, stack size, module version or `mpirun`/`srun` preference from a
workshop example. Follow the site's documented MPI launcher.

Launch a controller once; do not wrap it in another MPI launcher if it already
launches PASP. For an error about nested or outside `mpirun/srun` execution,
inspect the complete launcher and scheduler environment. Residual MPI variables
can be ambiguous; clearing them to hide an actual nested launch is not a fix.

Choose `DFT.nk_pool` and `DFT.nb_pool` from the actual reduced points and
representation limits; see [parallel pools](kpoint-band-parallelism.md).
SCF and path stages can require different resources. A legal pool arrangement
is not proof of parallel speedup or release-wide MPI compatibility.

## Find all relevant output

Read `#SBATCH --output` and `#SBATCH --error`, sbatch overrides and shell redirection, including
redirection inside shared scripts. PASP stdout/stderr can be in the scheduler
files, a separate application log, or both. Inspect files by content: PASP logs
have no required suffix, and an extensionless file may contain complete output.
An empty scheduler file does not prove the application never ran.

Do not assume a historical job followed today's scripts or that the newest
filename is the correct run. Use job IDs, launch times, input identity and
stage markers as combined evidence. Keep ambiguous candidate files visible.

Separate scheduler success, wrapper exit status, PASP completion and electronic
convergence. A wrapper may check only process exit or additionally require
specific SCF/path markers. `PASP is finished gracefully.` does not certify every
stage. Preserve stderr and the last failed/truncated stage; use
[output analysis](output-analysis.md) and [validation](validation.md).
