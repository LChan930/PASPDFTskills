"""Black-box regression tests for the native fixed-cell relaxation CLI."""
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / "knowledge/scripts/analyze_relax.py"
ACCURACY = "reached required accuracy - stopping structural energy minimisation."
CAPPED = "Warning: NSTEP Reached. Maybe larger NSTEP is needed."
DONE = "PASP is finished gracefully."


def scf(energy, status="LEGACY_CONVERGED"):
    return (
        "==== Entering electronic step of PW-DFT ====\n"
        "==== End of electronic step of PW-DFT ====\n"
        f"PASP_SCF_RESULT status={status} certified=F\n"
        f"Total energy (in Hartree) is: {energy}\n"
    )


def forces(first="0.000100", second_z="0.000400", closed=True):
    table = (
        "======= POSITION and FORCE =======\n"
        "atom     POSITION                 FORCE\n"
        f"1  0.000000 0.000000 0.000000 {first} 0.000000 0.000000\n"
        f"2  1.000000 0.000000 0.000000 0.000000 0.000300 {second_z}\n"
    )
    return table + ("======= POSITION and FORCE END =======\n" if closed else "")


def log_text(exit_line=CAPPED, final_table=None):
    return (
        "PASP start\n"
        + scf("-5.00D+00")
        + "PASP_RELAX_FIXED_CELL enabled=T cell_dof=disabled optimizer=IONCGR\n"
        + forces(second_z="0.000800")
        + scf("-5.02D+00")
        + "------ iteration for ionic relaxation: 1\n"
        + (forces() if final_table is None else final_table)
        + (f"{exit_line}\n{DONE}\n" if exit_line else "")
    )


class AnalyzeRelaxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root / "run.sample"
        self.fdf = self.root / "lattice_model.fdf"
        self.fdf.write_text("Model DFT\nDFT.LRELAX T\nDFT.nstep 1\nDFT.EDIFFG -0.01\n")

    def run_cli(self, data, *args, input_file=True):
        self.log.write_text(data, encoding="utf-8")
        flags = ["--input", str(self.fdf)] if input_file else []
        return subprocess.run(
            [sys.executable, "-X", "utf8", "-B", str(CLI), str(self.log),
             "--format", "json", *flags, *map(str, args)],
            text=True, encoding="utf-8", capture_output=True, check=False,
        )

    def parse(self, process, code):
        self.assertEqual(process.returncode, code, (process.stdout, process.stderr))
        return json.loads(process.stdout)

    def test_native_scf_precedes_ionic_step_header(self):
        data = self.parse(self.run_cli(log_text()), 0)
        initial, last = data["frames"]
        self.assertEqual([initial["step"], last["step"]], [0, 1])
        self.assertAlmostEqual(initial["energy_ha"], -5.0)
        self.assertAlmostEqual(last["energy_ha"], -5.02)
        self.assertAlmostEqual(last["delta_energy_ha"], -0.02)
        self.assertEqual(last["max_force_atom_id"], 2)
        self.assertAlmostEqual(last["max_force_ha_per_bohr"], math.hypot(0.0003, 0.0004))
        self.assertAlmostEqual(last["max_force_ev_per_angstrom"], 0.0005 * 51.42208, places=6)

    def test_runtime_stop_is_distinct_from_step_limit(self):
        capped = self.parse(self.run_cli(log_text()), 0)
        converged = self.parse(self.run_cli(log_text(ACCURACY), input_file=False), 0)
        self.assertEqual(capped["ionic_exit"]["status"], "nstep_limit")
        self.assertEqual(converged["ionic_exit"]["status"], "converged")
        self.assertEqual(capped["run_completion"]["status"], "graceful")
        self.assertEqual(converged["run_completion"]["status"], "graceful")

    def test_truncated_table_keeps_only_last_complete_frame(self):
        result = self.parse(self.run_cli(log_text("", forces(closed=False))), 1)
        self.assertEqual([f["step"] for f in result["frames"]], [0])

    def test_duplicate_atom_row_does_not_become_valid_geometry(self):
        bad_table = forces().replace("\n2  ", "\n1  ")
        result = self.parse(self.run_cli(log_text("", bad_table)), 1)
        self.assertEqual([f["step"] for f in result["frames"]], [0])

    def test_initial_structure_already_accurate(self):
        log = log_text().split("==== Entering electronic step of PW-DFT ====")[1]
        log = "==== Entering electronic step of PW-DFT ====" + log + ACCURACY + "\n" + DONE + "\n"
        result = self.parse(self.run_cli(log, input_file=False), 0)
        self.assertEqual([f["step"] for f in result["frames"]], [0])

    def test_concatenated_runs_are_ambiguous(self):
        result = self.parse(self.run_cli(log_text() + log_text()), 1)
        self.assertEqual(result["ionic_exit"]["status"], "ambiguous")

    def test_positive_ediffg_remains_optimizer_specific(self):
        self.fdf.write_text("Model DFT\nDFT.LRELAX T\nDFT.nstep 1\nDFT.EDIFFG 0.1\n")
        result = self.parse(self.run_cli(log_text()), 0)
        self.assertEqual(result["threshold"]["status"], "optimizer_specific")
        self.assertEqual(result["ionic_exit"]["status"], "nstep_limit")

    def test_electronic_failure_remains_visible_at_ionic_exit(self):
        log = log_text().replace(
            scf("-5.02D+00"), scf("-5.02D+00", "MAXITER"),
        )
        result = self.parse(self.run_cli(log), 1)
        self.assertEqual(result["electronic_status"]["status"], "failure_evidence_present")
        self.assertEqual(result["ionic_exit"]["status"], "nstep_limit")

    def test_xyz_export_and_overwrite_protection(self):
        xyz = self.root / "final.xyz"
        self.parse(self.run_cli(log_text(), "--xyz", xyz, "--symbols", "Ba", "O"), 0)
        lines = xyz.read_text(encoding="utf-8").splitlines()
        self.assertEqual(int(lines[0]), 2)
        self.assertEqual(lines[2].split()[0], "Ba")
        self.assertEqual(lines[3].split()[0], "O")
        self.assertAlmostEqual(float(lines[3].split()[1]), 0.52917721, places=6)
        original = xyz.read_bytes()
        failure = self.run_cli(log_text(), "--xyz", xyz, "--symbols", "Ba", "O")
        self.assertEqual(failure.returncode, 2, failure.stderr)
        self.assertEqual(xyz.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
