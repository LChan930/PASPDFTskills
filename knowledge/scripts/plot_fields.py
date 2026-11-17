#!/usr/bin/env python3
"""Plot native PASP charge/current grids with NumPy and Matplotlib (Python 3.10+).

No PASP executable or source is needed. The native formats are not VASP formats.
Inputs are read-only; every output is exclusively created. See field-plotting.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import zlib
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path

import numpy as np

BOHR_ANGSTROM = 0.529177210903
MAX_BYTES = 256 * 1024 * 1024
MAX_VALUES = 8_000_000
NUMBER = re.compile(rb"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?\Z")
TEXT = {
    "en": (
        "PASP field analysis",
        "Volume integral (native atomic units)",
        "Projection integrates; a slice interpolates periodically and does not integrate.",
        "Native current is local kinetic electronic charge current; its sign already includes electron charge.",
    ),
    "zh-Hans": (
        "PASP 场数据分析",
        "体积分（原子单位）",
        "投影执行积分；切片采用周期线性插值，不执行积分。",
        "原生电流是局域动能电子电荷电流；电子电荷符号已包含在内。",
    ),
    "zh-Hant": (
        "PASP 場資料分析",
        "體積分（原子單位）",
        "投影執行積分；切片採用週期線性插值，不執行積分。",
        "原生電流是局域動能電子電荷電流；電子電荷符號已包含在內。",
    ),
}


@dataclass(frozen=True)
class Field:
    source: Path
    kind: str
    values: np.ndarray
    ispin: int
    sha256: str
    adler32: int
    size_bytes: int


def read_field(path, kind):
    """Read x-fastest Fortran grids; current components are contiguous blocks."""
    if kind not in {"charge", "current"}:
        raise ValueError("kind must be charge or current")
    source = Path(path).resolve()
    if source.stat().st_size > MAX_BYTES:
        raise ValueError("field exceeds byte budget")
    raw = source.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError("field exceeds byte budget")
    lines = raw.split(b"\n", 1)
    if len(lines) != 2:
        raise ValueError("missing header or payload")
    header = lines[0].split()
    count = 4 if kind == "charge" else 5
    if len(header) != count or not all(re.fullmatch(rb"[+]?\d+", s) for s in header):
        raise ValueError(f"native {kind} requires {count} positive header integers")
    integers = [int(s) for s in header]
    shape, ispin = tuple(integers[:3]), integers[-1]
    if min(shape) < 1 or ispin not in (1, 2, 4):
        raise ValueError("positive grid dimensions and ISPIN 1/2/4 required")
    if kind == "current" and (integers[3] != 3 or ispin != 1):
        raise ValueError("current requires three Cartesian components and ISPIN=1")
    components = ispin if kind == "charge" else 3
    expected = math.prod(shape) * components
    if expected > MAX_VALUES:
        raise ValueError("field exceeds value budget")
    tokens = lines[1].split()
    if len(tokens) != expected:
        raise ValueError(f"expected exactly {expected} values, got {len(tokens)}")
    if not all(NUMBER.fullmatch(t) for t in tokens):
        raise ValueError("payload must contain finite Fortran numbers only")
    data = np.fromiter(
        (float(t.replace(b"D", b"E").replace(b"d", b"e")) for t in tokens),
        dtype=float,
        count=expected,
    )
    if not np.isfinite(data).all():
        raise ValueError("nonfinite field value")
    return Field(
        source,
        kind,
        data.reshape((*shape, components), order="F"),
        ispin,
        hashlib.sha256(raw).hexdigest(),
        zlib.adler32(raw),
        len(raw),
    )


def validate_cell(cell):
    cell = np.asarray(cell, dtype=float)
    if cell.shape != (3, 3) or not np.isfinite(cell).all():
        raise ValueError("cell requires nine finite numbers, lattice vectors as rows")
    lengths = np.linalg.norm(cell, axis=1)
    volume = abs(float(np.linalg.det(cell)))
    if (
        np.any(lengths <= 0)
        or not math.isfinite(volume)
        or volume <= 1e-10 * np.prod(lengths)
    ):
        raise ValueError("cell is singular or numerically degenerate")
    return cell


def read_restart(path, field=None):
    """Read public text restart geometry; verify paired density when supplied."""
    path = Path(path).resolve()
    if path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("restart exceeds byte budget")
    raw = path.read_bytes()
    lines = raw.decode("utf-8-sig").splitlines()
    if (
        not lines
        or lines[0].strip() != "PASP_DFT_RESTART 1"
        or lines[-1].strip() != "END_PASP_DFT_RESTART"
    ):
        raise ValueError("unsupported or incomplete restart")

    def unique(key):
        matches = [
            i for i, line in enumerate(lines) if line.split() and line.split()[0] == key
        ]
        if len(matches) != 1:
            raise ValueError(f"restart requires unique {key}")
        return matches[0]

    def numbers(line):
        return [float(t.replace("D", "E").replace("d", "e")) for t in line.split()]

    ci, ai = unique("CELL_BOHR"), unique("ATOMS_BOHR")
    nat = int(lines[unique("GEOMETRY_BOHR")].split()[1])
    if not 0 <= nat <= 100000 or ai != ci + 4:
        raise ValueError("malformed restart geometry")
    cell = validate_cell([numbers(line) for line in lines[ci + 1 : ci + 4]])
    rows = [numbers(line) for line in lines[ai + 1 : ai + 1 + nat]]
    if len(rows) != nat or any(len(row) != 5 for row in rows):
        raise ValueError("truncated/malformed atom records")
    atoms = np.array([row[-3:] for row in rows], dtype=float).reshape(-1, 3)
    if not np.isfinite(atoms).all():
        raise ValueError("nonfinite atom coordinates")
    bound = False
    if field is not None and field.kind == "charge":
        size = int(lines[unique("DENSITY_BYTES")].split()[1])
        checksum = int(lines[unique("DENSITY_ADLER32")].split()[1])
        if size != field.size_bytes or checksum != field.adler32:
            raise ValueError("density does not match paired restart size/checksum")
        if int(lines[unique("ISPIN")].split()[1]) != field.ispin:
            raise ValueError("density/restart ISPIN mismatch")
        bound = True
    return (
        cell,
        atoms,
        {
            "source": str(path),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "density_binding_verified": bound,
        },
    )


def reduce_field(values, cell, *, axis=2, mode="project", fraction=0.0):
    """Integrate with normal height, or interpolate a periodic fractional slice.

    The remaining axes retain their ascending native order. A projection is a
    fractional-column integral with normal length measure, not an average.
    """
    cell = validate_cell(cell)
    if axis not in (0, 1, 2) or mode not in {"slice", "project"}:
        raise ValueError("invalid axis or mode")
    if not math.isfinite(fraction) or not 0 <= fraction < 1:
        raise ValueError("fraction must be finite in [0,1)")
    remaining = [i for i in range(3) if i != axis]
    a, b = cell[remaining]
    normal = np.cross(a, b)
    area = float(np.linalg.norm(normal))
    normal /= area
    height = abs(float(cell[axis] @ normal))
    basis = np.array([a / np.linalg.norm(a), np.cross(normal, a / np.linalg.norm(a))])
    n = values.shape[axis]
    if mode == "project":
        reduced = values.sum(axis=axis) * (height / n)
    else:
        position = fraction * n
        lo = math.floor(position)
        weight = position - lo
        reduced = (1 - weight) * np.take(values, lo, axis=axis) + weight * np.take(
            values, (lo + 1) % n, axis=axis
        )
    if not np.isfinite(reduced).all():
        raise ValueError("field reduction overflowed")
    return reduced, {
        "remaining_axes": remaining,
        "basis": basis,
        "normal": normal,
        "area_bohr2": area,
        "normal_height_bohr": height,
    }


def volume_integral(values, cell):
    return values.sum(axis=(0, 1, 2)) * (
        abs(np.linalg.det(validate_cell(cell))) / math.prod(values.shape[:3])
    )


def field_presentation(kind, mode, density_unit="angstrom", stored_channel=False):
    """Describe the displayed quantity independently of a custom figure title."""
    sheet = mode == "project"
    if kind == "charge":
        quantity = "Stored density channel" if stored_channel else "Electron density"
        power = 2 if sheet else 3
        length = r"\AA" if density_unit == "angstrom" else "a_0"
        unit = f"e/{density_unit}^{power}"
        native_unit = f"e/a0^{power}"
        label = rf"{'Sheet' if sheet else 'Plane'} {quantity.lower()} ($e/{length}^{power}$)"
        representation = (
            "full_cell_sheet_density" if sheet else "plane_slice_volume_density"
        )
    else:
        quantity = "Local charge current"
        unit = "e/(a0 t0)" if sheet else "e/(a0^2 t0)"
        native_unit = unit
        tex_unit = r"e/(a_0\,t_0)" if sheet else r"e/(a_0^2\,t_0)"
        label = rf"{'Sheet' if sheet else 'Slice'} in-plane current magnitude (${tex_unit}$)"
        representation = (
            "full_cell_sheet_current" if sheet else "plane_slice_current_density"
        )
    return {
        "default_title": quantity
        + (": full-cell sheet integral" if sheet else ": plane slice"),
        "colorbar_label": label,
        "representation": representation,
        "display_unit": unit,
        "native_reduced_unit": native_unit,
        "integration_scope": "full_periodic_cell" if sheet else "none_single_plane",
        "reduction_measure": (
            "fractional-column integral with normal length measure"
            if sheet
            else "periodic linear interpolation; no integration"
        ),
    }


def make_figure(
    reduced,
    cell,
    atoms,
    plane,
    *,
    kind,
    mode,
    axis,
    fraction,
    length_unit="angstrom",
    density_unit="angstrom",
    stride=2,
    clim=None,
    title=None,
    stored_channel=False,
):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    basis = plane["basis"]
    rem = plane["remaining_axes"]
    factor = BOHR_ANGSTROM if length_unit == "angstrom" else 1.0
    lattice2d = cell[rem] @ basis.T * factor
    n, m = reduced.shape[:2]
    u, v = np.meshgrid(np.arange(n + 1) / n, np.arange(m + 1) / m, indexing="ij")
    xy = u[..., None] * lattice2d[0] + v[..., None] * lattice2d[1]
    presentation = field_presentation(kind, mode, density_unit, stored_channel)
    power = 2 if mode == "project" else 3
    if kind == "charge":
        scalar = reduced[..., 0] / (
            BOHR_ANGSTROM**power if density_unit == "angstrom" else 1
        )
        vectors = None
    else:
        vectors = reduced @ basis.T
        scalar = np.linalg.norm(vectors, axis=-1)
    periodic = scalar[np.arange(n + 1) % n][:, np.arange(m + 1) % m]
    style = {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    }
    with plt.rc_context(style):
        fig, ax = plt.subplots(figsize=(6.2, 4.7), layout="constrained")
        image = ax.pcolormesh(
            xy[..., 0],
            xy[..., 1],
            periodic,
            shading="gouraud",
            cmap="magma" if kind == "charge" else "viridis",
            vmin=None if clim is None else clim[0],
            vmax=None if clim is None else clim[1],
            rasterized=True,
        )
        fig.colorbar(
            image, ax=ax, shrink=0.8, pad=0.04, label=presentation["colorbar_label"]
        )
        outline = np.array(
            [[0.0, 0.0], lattice2d[0], lattice2d.sum(axis=0), lattice2d[1], [0.0, 0.0]]
        )
        ax.plot(*outline.T, color="#454545", linewidth=0.85)
        if vectors is not None:
            xx, yy = xy[:-1:stride, :-1:stride, 0], xy[:-1:stride, :-1:stride, 1]
            vv = vectors[::stride, ::stride]
            maximum = float(np.max(np.linalg.norm(vv, axis=-1)))
            if maximum > 0:
                reference = float(f"{maximum:.1g}")
                scale = maximum / (0.11 * max(np.linalg.norm(lattice2d, axis=1)))
                q = ax.quiver(
                    xx,
                    yy,
                    vv[..., 0],
                    vv[..., 1],
                    angles="xy",
                    scale_units="xy",
                    scale=scale,
                    width=0.004,
                    color="white",
                    edgecolor="#26373f",
                    linewidth=0.25,
                )
                ax.quiverkey(
                    q,
                    0.68,
                    1.035,
                    reference,
                    f"{reference:g} a.u.",
                    coordinates="axes",
                    labelpos="E",
                    fontproperties={"size": 8},
                )
        if len(atoms):
            fractional = atoms @ np.linalg.inv(cell)
            # Slice markers show only atoms lying on the selected periodic plane.
            if mode == "slice":
                distance = np.abs((fractional[:, axis] - fraction + 0.5) % 1 - 0.5)
                fractional = fractional[distance < 1e-5]
            points = set()
            for atom in fractional:
                uv = atom[rem] % 1
                for shift0 in (-1, 0, 1):
                    for shift1 in (-1, 0, 1):
                        pos = uv + [shift0, shift1]
                        if np.all(pos >= -1e-9) and np.all(pos <= 1 + 1e-9):
                            points.add(tuple(np.round(pos, 10)))
            if points:
                positions = np.array(sorted(points)) @ lattice2d
                ax.scatter(
                    *positions.T,
                    s=26,
                    facecolor="#f7f7f7",
                    edgecolor="#292929",
                    linewidth=0.7,
                    zorder=4,
                )
        physical_xy = np.allclose(basis, [[1, 0, 0], [0, 1, 0]], atol=1e-10)
        unit = r"$\AA$" if length_unit == "angstrom" else r"$a_0$"
        ax.set(
            xlabel=f"{'x' if physical_xy else 'In-plane x'} ({unit})",
            ylabel=f"{'y' if physical_xy else 'In-plane y'} ({unit})",
            aspect="equal",
        )
        ax.set_title(
            title or presentation["default_title"],
            loc="left",
            fontsize=13,
            pad=26 if kind == "current" else 12,
        )
        ax.margins(0.08)
        ax.tick_params(direction="out", length=4)
    return fig, scalar, xy, vectors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--kind", choices=("charge", "current"), required=True)
    geometry = parser.add_mutually_exclusive_group(required=True)
    geometry.add_argument(
        "--restart",
        type=Path,
        help="paired native text restart, including Bohr geometry",
    )
    geometry.add_argument(
        "--cell-bohr", type=float, nargs=9, help="three lattice vectors as rows in Bohr"
    )
    parser.add_argument(
        "--channel",
        type=int,
        help="1-based charge channel; required for ISPIN=2/4 (no channel semantics inferred)",
    )
    parser.add_argument(
        "--mode",
        choices=("slice", "project"),
        default="project",
        help="slice: single-plane volume density; project: full-cell sheet integral (default)",
    )
    parser.add_argument(
        "--axis",
        type=int,
        choices=(1, 2, 3),
        default=3,
        help="fractional axis to remove",
    )
    parser.add_argument(
        "--fraction",
        type=float,
        default=0.0,
        help="periodic slice location in [0,1), default cell origin 0",
    )
    parser.add_argument(
        "--length-unit", choices=("angstrom", "bohr"), default="angstrom"
    )
    parser.add_argument(
        "--density-unit",
        choices=("angstrom", "bohr"),
        default="angstrom",
        help="charge only; current stays in native atomic units",
    )
    parser.add_argument(
        "--stride", type=int, default=2, help="current quiver stride, 1..1000"
    )
    parser.add_argument("--clim", type=float, nargs=2)
    parser.add_argument("--title")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--name", default="field")
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=("png", "pdf", "svg"),
        default=["png", "pdf", "svg"],
    )
    parser.add_argument(
        "--lang",
        choices=tuple(TEXT),
        default="en",
        help="report/JSON language; figure labels remain English",
    )
    args = parser.parse_args(argv)
    try:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", args.name):
            raise ValueError("name must be a short plain basename")
        if not 1 <= args.stride <= 1000:
            raise ValueError("stride must be within 1..1000")
        if args.clim and (
            not all(math.isfinite(v) for v in args.clim) or args.clim[0] >= args.clim[1]
        ):
            raise ValueError("color limits must be finite and increasing")
        formats = list(dict.fromkeys(args.formats))
        targets = [
            args.output_dir / f"{args.name}.{extension}"
            for extension in [*formats, "npz", "json", "md"]
        ]
        if any(p.exists() for p in targets):
            raise ValueError("output already exists; choose a fresh name or directory")
        field = read_field(args.input, args.kind)
        if args.restart:
            cell, atoms, geometry_meta = read_restart(args.restart, field)
        else:
            cell, atoms = (
                validate_cell(np.array(args.cell_bohr).reshape(3, 3)),
                np.empty((0, 3)),
            )
            geometry_meta = {
                "source": "explicit --cell-bohr",
                "density_binding_verified": False,
            }
        values = field.values
        if args.kind == "charge":
            if field.ispin > 1 and args.channel is None:
                raise ValueError(
                    "ISPIN=2/4 requires explicit --channel; channel semantics are not inferred"
                )
            channel = 1 if args.channel is None else args.channel
            if not 1 <= channel <= field.ispin:
                raise ValueError("charge channel outside stored channel count")
            values = values[..., channel - 1 : channel]
        elif args.channel is not None:
            raise ValueError("--channel applies only to charge")
        reduced, plane = reduce_field(
            values, cell, axis=args.axis - 1, mode=args.mode, fraction=args.fraction
        )
        fig, scalar, xy, vectors = make_figure(
            reduced,
            cell,
            atoms,
            plane,
            kind=args.kind,
            mode=args.mode,
            axis=args.axis - 1,
            fraction=args.fraction,
            length_unit=args.length_unit,
            density_unit=args.density_unit,
            stride=args.stride,
            clim=args.clim,
            title=args.title
            or (
                f"Density channel {channel}: "
                + (
                    "full-cell sheet integral"
                    if args.mode == "project"
                    else "plane slice"
                )
                if args.kind == "charge" and field.ispin > 1
                else None
            ),
            stored_channel=args.kind == "charge" and field.ispin > 1,
        )
        integrals = volume_integral(values, cell).tolist()
        presentation = field_presentation(
            args.kind,
            args.mode,
            args.density_unit,
            stored_channel=args.kind == "charge" and field.ispin > 1,
        )
        metadata = {
            "schema": "pasp-native-fields-v1",
            "lang": args.lang,
            "kind": args.kind,
            "source": str(field.source),
            "sha256": field.sha256,
            "size_bytes": field.size_bytes,
            "adler32": field.adler32,
            "shape": list(field.values.shape),
            "ispin": field.ispin,
            "channel": channel if args.kind == "charge" else None,
            "geometry": geometry_meta,
            "cell_bohr_rows": cell.tolist(),
            "layout": "Fortran x fastest, y, z, then contiguous component/channel blocks",
            "mode": args.mode,
            **presentation,
            "figure_title": fig.axes[0].get_title(loc="left"),
            "axis": args.axis,
            "fraction": args.fraction if args.mode == "slice" else None,
            "volume_integrals_native_au": integrals,
            "raw_minimum": float(values.min()),
            "raw_maximum": float(values.max()),
            "plane": {
                k: v.tolist() if isinstance(v, np.ndarray) else v
                for k, v in plane.items()
            },
            "length_unit": args.length_unit,
            "charge_density_length_unit": args.density_unit,
            "current_unit": "e/(a0 t0)" if args.mode == "project" else "e/(a0^2 t0)",
            "current_magnitude": "in-plane vector after reduction; integral of vector, not integral of magnitude",
            "normalization": "native density; no volume multiplication of stored values; no clipping",
            "notes": [TEXT[args.lang][2]]
            + ([TEXT[args.lang][3]] if args.kind == "current" else []),
            "color_limits": args.clim,
            "outputs": [str(p.resolve()) for p in targets],
            "python": sys.version.split()[0],
            "numpy": np.__version__,
        }
        if args.kind == "charge" and args.mode == "project":
            metadata["sheet_integral_native_au"] = (
                reduced.sum(axis=(0, 1))
                * plane["area_bohr2"]
                / math.prod(reduced.shape[:2])
            ).tolist()
        import matplotlib

        metadata["matplotlib"] = matplotlib.__version__
        report = (
            f"# {TEXT[args.lang][0]}\n\n{TEXT[args.lang][1]}: `{integrals}`\n\n"
            + f"Representation: `{presentation['representation']}`\n\n"
            + f"Display unit: `{presentation['display_unit']}`\n\n"
            + f"Integration scope: `{presentation['integration_scope']}`\n\n"
            + f"Reduction: {presentation['reduction_measure']}\n\n"
            + "\n\n".join(metadata["notes"])
            + "\n\n```json\n"
            + json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)
            + "\n```\n"
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        with ExitStack() as stack:
            handles = [stack.enter_context(p.open("xb")) for p in targets]
            with matplotlib.rc_context({"svg.fonttype": "none", "pdf.fonttype": 42}):
                for handle, fmt in zip(handles, formats):
                    fig.savefig(
                        handle,
                        format=fmt,
                        dpi=400,
                        bbox_inches="tight",
                        facecolor="white",
                    )
            np.savez_compressed(
                handles[-3],
                reduced_native_au=reduced,
                scalar_display=scalar,
                vertices_xy=xy,
                vectors_plane_native_au=np.empty(0) if vectors is None else vectors,
                cell_bohr=cell,
            )
            handles[-2].write(
                (
                    json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)
                    + "\n"
                ).encode("utf-8")
            )
            handles[-1].write(report.encode("utf-8"))
        import matplotlib.pyplot as plt

        plt.close(fig)
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print(
            json.dumps(
                {
                    "outputs": metadata["outputs"],
                    "volume_integrals_native_au": integrals,
                },
                ensure_ascii=False,
            )
        )
        return 0
    except (OSError, ValueError, MemoryError, OverflowError, IndexError) as exc:
        parser.exit(2, f"plot_fields: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
