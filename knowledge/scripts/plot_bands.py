#!/usr/bin/env python3
"""Read native PASP PW/PWRS TB.bands content and export a band figure.

Python 3.10+, NumPy and Matplotlib. Inputs are read-only; outputs never replace
existing files. The supported file format contains one eigenvalue list;
neither the header nor band index identifies up/down spin, even with user-supplied
ISPIN2/4 provenance. Check compatibility against an actual file from your version.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from contextlib import ExitStack
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

import numpy as np

HARTREE_EV = 27.211386245988  # CODATA 2018; conversion, not a fitted shift.
MAX_BYTES = 64 * 1024 * 1024
MAX_VALUES = 2_000_000
MAX_LINE = 16384
PATH_ATOL = 1.1e-6  # Native coordinates and label ticks use six decimals.
NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?\Z")
TICK = re.compile(r"\s*(\S+)\s+(['\"])(.*?)\2\s*\Z")


class BandFormatError(ValueError):
    """Malformed, unsupported or over-budget native band content."""


@dataclass(frozen=True)
class BandData:
    source: Path
    sha256: str
    size_bytes: int
    reference_ha: float
    path: np.ndarray  # (nk,), native cumulative reciprocal distance
    energies_ha: np.ndarray  # (nk, nb), unchanged file ordering
    ticks: tuple[tuple[float, str], ...]
    header_path_range: tuple[float, float]
    header_energy_range: tuple[float, float]


def number(token: str) -> float:
    if not NUMBER.fullmatch(token):
        raise BandFormatError(f"invalid finite Fortran number: {token[:60]!r}")
    value = float(token.replace("D", "E").replace("d", "e"))
    if not math.isfinite(value):
        raise BandFormatError("nonfinite numeric value")
    return value


class _Reader:
    def __init__(self, stream):
        self.stream = stream
        self.line = 0
        self.size = 0
        self.digest = hashlib.sha256()

    def next(self, required=True):
        while raw := self.stream.readline(MAX_LINE + 1):
            self.line += 1
            self.size += len(raw)
            if len(raw) > MAX_LINE or self.size > MAX_BYTES:
                raise BandFormatError("input exceeds line/file budget")
            self.digest.update(raw)
            if any(c < 32 and c not in (9, 10, 13) for c in raw):
                raise BandFormatError(f"line {self.line}: binary/control data")
            try:
                text = raw.decode("utf-8").rstrip("\r\n")
            except UnicodeDecodeError as exc:
                raise BandFormatError(f"line {self.line}: not UTF-8 text") from exc
            if text.strip():
                return text
        if required:
            raise BandFormatError(f"line {self.line}: truncated band file")
        return None

    def values(self, count, *, continuation=False, fixed=False):
        text = self.next()
        if continuation and not text[:10].isspace():
            raise BandFormatError(f"line {self.line}: missing wrapped-energy indentation")
        fields = text.split()
        if len(fields) != count and fixed:
            # Native F10.6/F12.4 may touch at a full field width.
            widths = ([10] if not continuation else []) + [12] * (count - (not continuation))
            body = text[10:] if continuation else text
            fields = []
            offset = 0
            for width in widths:
                fields.append(body[offset:offset + width].strip())
                offset += width
            if body[offset:].strip():
                raise BandFormatError(f"line {self.line}: extra numeric data")
        if len(fields) != count:
            raise BandFormatError(f"line {self.line}: expected {count} fields, got {len(fields)}")
        try:
            return [number(field) for field in fields]
        except BandFormatError as exc:
            raise BandFormatError(f"line {self.line}: {exc}") from exc


def read_bands(path: str | Path) -> BandData:
    """Parse the supported native band format, independently of the filename.

    O(nk*nb) retained storage, capped before array allocation. Continuations
    use ten-energy records; blank physical records are allowed.
    plot.dat alone is deliberately rejected: its reference/path/spin metadata
    cannot be reconstructed from the two-column content.
    """
    source = Path(path).resolve()
    if source.stat().st_size > MAX_BYTES:
        raise BandFormatError(f"input exceeds {MAX_BYTES} byte budget")
    with source.open("rb") as stream:
        reader = _Reader(stream)
        reference = reader.values(1)[0]
        path_range = tuple(reader.values(2))
        energy_range = tuple(reader.values(2))
        dimensions = reader.next().split()
        if len(dimensions) != 3 or not all(re.fullmatch(r"\+?\d+", x) for x in dimensions):
            raise BandFormatError("expected integer header: nband 1 nk")
        nb, channels, nk = map(int, dimensions)
        if channels != 1:
            raise BandFormatError("unsupported channel header: this parser requires 1")
        if nb < 1 or nk < 2 or nb * nk > MAX_VALUES:
            raise BandFormatError(f"invalid/over-budget dimensions ({nb}, {nk})")
        if path_range[0] > path_range[1] or energy_range[0] > energy_range[1]:
            raise BandFormatError("reversed header range")
        x = np.empty(nk)
        energies = np.empty((nk, nb))
        for ik in range(nk):
            first = min(nb, 10)
            row = reader.values(first + 1, fixed=True)
            x[ik], energies[ik, :first] = row[0], row[1:]
            for start in range(first, nb, 10):
                count = min(10, nb - start)
                energies[ik, start:start + count] = reader.values(
                    count, continuation=True, fixed=True
                )
        if np.any(np.diff(x) < 0) or x[-1] <= x[0]:
            raise BandFormatError("path must be nondecreasing with positive extent")
        if not np.allclose([x[0], x[-1]], path_range, atol=PATH_ATOL, rtol=0):
            raise BandFormatError("path endpoints disagree with header")
        label_count = reader.next().strip()
        if not re.fullmatch(r"\+?\d+", label_count) or not 0 <= int(label_count) <= nk:
            raise BandFormatError("invalid label count")
        ticks = []
        for _ in range(int(label_count)):
            match = TICK.fullmatch(reader.next())
            if not match:
                raise BandFormatError(f"line {reader.line}: expected distance 'label'")
            position = number(match[1])
            if ticks and position < ticks[-1][0]:
                raise BandFormatError("label distances are out of order")
            if not np.any(np.abs(x - position) <= PATH_ATOL):
                raise BandFormatError("label distance has no matching path sample")
            ticks.append((position, match[3].strip()))
        if reader.next(required=False) is not None:
            raise BandFormatError(f"line {reader.line}: trailing content after labels")
    x.flags.writeable = energies.flags.writeable = False
    return BandData(source, reader.digest.hexdigest(), reader.size, reference, x,
                    energies, tuple(ticks), path_range, energy_range)


def display_ticks(ticks):
    """Merge coincident labels, retaining repeated symmetry points elsewhere."""
    positions, labels = [], []
    for position, label in ticks:
        if label in ("Gamma", r"\Gamma", "Γ"):
            label = "Γ"
        if positions and position == positions[-1]:
            labels[-1] = "|".join(filter(None, [labels[-1], label]))
        else:
            positions.append(position)
            labels.append(label)
    return positions, labels


def unit_scale(unit, units_per_hartree=None):
    """Return a positive conversion factor; a named custom unit is explicit."""
    builtins = {"ev": HARTREE_EV, "mev": 1000 * HARTREE_EV,
                "ha": 1.0, "hartree": 1.0, "ry": 2.0, "rydberg": 2.0}
    if not unit or len(unit) > 40 or not unit.isprintable():
        raise ValueError("unit name must contain 1–40 printable characters")
    if units_per_hartree is not None:
        if not math.isfinite(units_per_hartree) or units_per_hartree <= 0:
            raise ValueError("units-per-hartree must be positive and finite")
        if unit.lower() in builtins:
            raise ValueError("built-in energy units have fixed scales; omit units-per-hartree")
        return units_per_hartree
    if unit.lower() not in builtins:
        raise ValueError("custom unit requires --units-per-hartree SCALE")
    return builtins[unit.lower()]


def make_figure(data, *, reference_ha=None, absolute=False, unit="eV", ylim=None,
                units_per_hartree=None, title="Electronic band structure", ispin=None,
                break_before=()):
    """Build a figure; explicit 1-based breaks cut edges without rescaling x."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import AutoMinorLocator

    nk = len(data.path)
    breaks = sorted(set(break_before))
    if any(index < 2 or index > nk for index in breaks):
        raise ValueError(f"break-before indices must be within 2..{nk}")
    if ispin not in (None, 1, 2, 4):
        raise ValueError("ISPIN must be 1, 2 or 4; it does not resolve eigenstate spin")
    if absolute and reference_ha is not None:
        raise ValueError("absolute and explicit reference are mutually exclusive")
    scale = unit_scale(unit, units_per_hartree)
    reference = 0.0 if absolute else data.reference_ha if reference_ha is None else reference_ha
    if not math.isfinite(reference):
        raise ValueError("reference must be finite")
    if ylim and (not all(math.isfinite(v) for v in ylim) or ylim[0] >= ylim[1]):
        raise ValueError("energy limits must be finite and increasing")
    with np.errstate(over="ignore", invalid="ignore"):
        energy = (data.energies_ha - reference) * scale
    if not np.all(np.isfinite(energy)):
        raise ValueError("energy transformation overflowed; check units/reference")
    style = {"font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
             "font.size": 13, "axes.linewidth": 1.3, "axes.spines.top": False,
             "axes.spines.right": False, "svg.fonttype": "none", "pdf.fonttype": 42,
             "text.usetex": False, "axes.unicode_minus": True}
    with plt.rc_context(style):
        fig, ax = plt.subplots(figsize=(7.2, 5.2), layout="constrained")
        # Okabe-Ito blue; preserve the spectrum without inventing spin labels.
        edges = [0, *(index - 1 for index in breaks), nk]
        for start, stop in pairwise(edges):
            ax.plot(data.path[start:stop], energy[start:stop], color="#0072B2", lw=1.35,
                    marker="." if stop - start == 1 else None, markersize=3)
        positions, labels = display_ticks(data.ticks)
        if positions:
            ax.set_xticks(positions, labels)
            for tick in ax.get_xticklabels():
                tick.set_parse_math(False)
            for position in positions[1:-1]:
                ax.axvline(position, color="#c9cdd1", lw=0.65, zorder=0)
        if not absolute:
            ax.axhline(0, color="#626970", ls=(0, (4, 3)), lw=0.9, zorder=0)
        ax.set(xlim=(data.path[0], data.path[-1]), xlabel="Wave-vector path",
               ylabel=f"{'Energy' if absolute else 'E − E_ref'} ({unit})")
        ax.yaxis.label.set_parse_math(False)
        if ylim:
            ax.set_ylim(*ylim)
        ax.set_title(title, loc="left", fontsize=16, pad=12, parse_math=False)
        ax.yaxis.set_minor_locator(AutoMinorLocator(2))
        ax.tick_params(which="major", direction="out", length=5, width=1)
        ax.tick_params(which="minor", length=2.5)
    return fig


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="explicit native band-content path; any filename")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--name", default="bands", help="new output basename")
    parser.add_argument("--formats", nargs="+", choices=("png", "pdf", "svg"), default=["png", "pdf", "svg"])
    parser.add_argument("--unit", default="eV", help="eV (default), meV, Ha/Hartree, Ry, or custom unit name")
    parser.add_argument("--units-per-hartree", type=float,
                        help="positive finite conversion factor, required for a custom unit")
    parser.add_argument("--ylim", type=float, nargs=2, metavar=("MIN", "MAX"))
    parser.add_argument("--title", default="Electronic band structure")
    reference = parser.add_mutually_exclusive_group()
    reference.add_argument("--reference-ha", type=float, help="explicit subtraction reference in Hartree")
    reference.add_argument("--absolute", action="store_true", help="plot raw eigenvalues")
    parser.add_argument("--ispin", type=int, choices=(1, 2, 4), help="user-supplied provenance, never spin assignment")
    parser.add_argument("--break-before", nargs="+", type=int, default=[], metavar="INDEX",
                        help="explicit 1-based sample indices; disconnect preceding edge, retain native x")
    args = parser.parse_args(argv)
    try:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", args.name):
            raise ValueError("name must be a simple 1–80 character output basename")
        data = read_bands(args.input)
        fig = make_figure(data, reference_ha=args.reference_ha, absolute=args.absolute,
                          unit=args.unit, units_per_hartree=args.units_per_hartree,
                          ylim=args.ylim, title=args.title,
                          ispin=args.ispin, break_before=args.break_before)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        formats = list(dict.fromkeys(args.formats))
        targets = [args.output_dir / f"{args.name}.{fmt}" for fmt in [*formats, "json"]]
        existing = [str(path) for path in targets if path.exists() or path.is_symlink()]
        if existing:
            raise FileExistsError("refusing to replace: " + ", ".join(existing))
        ref = 0.0 if args.absolute else data.reference_ha if args.reference_ha is None else args.reference_ha
        metadata = {"schema": "pasp-native-band-plot-v1", "input": str(data.source),
                    "sha256": data.sha256, "size_bytes": data.size_bytes,
                    "shape_nk_nband": list(data.energies_ha.shape), "writer_channel_field": 1,
                    "ispin_user_supplied": args.ispin, "spin_resolved": False,
                    "energy_input_unit": "Hartree", "energy_output_unit": args.unit,
                    "units_per_hartree": unit_scale(args.unit, args.units_per_hartree),
                    "unit_scale_source": "user" if args.units_per_hartree is not None else "builtin",
                    "hartree_eV": HARTREE_EV, "header_reference_ha": data.reference_ha,
                    "subtracted_reference_ha": ref,
                    "reference_source": "absolute" if args.absolute else "user" if args.reference_ha is not None else "file_header",
                    "reference_origin_verified": False, "convergence": "unknown; inspect associated run log",
                    "energy_rounding_step_ha": 1e-4, "path_rounding_step": 1e-6,
                    "path_unit": "native PW/PWRS cumulative Bohr^-1 (2*pi included)",
                    "path_breaks_inferred": False, "break_before_1based": sorted(set(args.break_before)),
                    "ticks": data.ticks, "header_energy_range_ha": data.header_energy_range,
                    "ylim": args.ylim, "title": args.title,
                    "outputs": [str(path.resolve()) for path in targets],
                    "python": sys.version.split()[0], "numpy": np.__version__}
        import matplotlib
        metadata["matplotlib"] = matplotlib.__version__
        # Reserve every destination with exclusive creation before any save.
        # On failure partial new files remain visible; rerun with a fresh name.
        with ExitStack() as stack:
            handles = [stack.enter_context(path.open("xb")) for path in targets]
            with matplotlib.rc_context({"svg.fonttype": "none", "pdf.fonttype": 42}):
                for handle, fmt in zip(handles, formats):
                    fig.savefig(handle, format=fmt, dpi=300, facecolor="white", bbox_inches="tight")
            handles[-1].write((json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        import matplotlib.pyplot as plt
        plt.close(fig)
        print(json.dumps({"outputs": metadata["outputs"], "shape": metadata["shape_nk_nband"]}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, MemoryError) as exc:
        parser.exit(2, f"plot_bands: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
