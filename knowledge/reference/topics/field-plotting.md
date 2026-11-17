# Native real-space charge and current plots

Use `knowledge/scripts/plot_fields.py` with Python 3.10+, NumPy and Matplotlib.
No PASP source, executable or private repository is required. This reader supports
native PASP text grids, not VASP CHGCAR. Files are read-only; existing outputs are
refused. `--help` lists all options. Reports and JSON accept `--lang en` (default),
`zh-Hans`, or `zh-Hant`; scientific figure labels remain English.

## Public format contract

| Quantity | First-line integers | Payload and units |
|---|---|---|
| Charge channels | `nx ny nz ISPIN` | Exactly `nx*ny*nz*ISPIN` numbers; density in electrons per Bohr cubed for ISPIN=1 |
| Local charge current | `nx ny nz 3 ISPIN` | Exactly `nx*ny*nz*3` numbers; Cartesian x, y, z blocks, in $e/(a_0^2t_0)$; ISPIN=1 only |

Each grid has x fastest, followed by y, z, and finally channel/component. Fortran
`D`/`d` exponents are accepted. Positive dimensions, exact counts and finite
values are required. The charge file contains no embedded cell or atoms and no
density-times-volume scaling. Multi-channel charge files require explicit
`--channel N`; channel physics is not inferred from ISPIN alone. Current files
with ISPIN=2/4 are refused because a spin-current interpretation is unsupported.

Supply geometry with the paired `--restart CHGCAR.restart` text file containing
`CELL_BOHR` and `ATOMS_BOHR`, or with `--cell-bohr` followed by nine numbers (three
lattice vectors as rows, in Bohr). For charge, the restart's density byte count,
Adler-32 and ISPIN are checked. Use the matching actual geometry; stale teaching
structure files are unsuitable. Current geometry comes from an explicitly chosen
restart, but its density checksum does not bind a separate current file.

Native current is the local kinetic electronic charge current,
$\mathbf j=-\mathrm{Re}\sum w\psi^*\boldsymbol\pi\psi$. The magnetic kinetic
momentum includes the vector potential; electron charge already supplies the
minus sign. Do not multiply by another negative electronic charge, cell volume,
or electron count. No separate paramagnetic/diamagnetic terms are available in
this file. The local quantity does not include an explicit nonlocal
pseudopotential commutator contribution. Missing current is unavailable data;
never construct an all-zero current map as a substitute.

## 先区分：单平面密度、整胞层积分面密度、单层材料

“单层密度”容易同时指某个平面的局域值、单层材料的电子密度，或某一物理层的积分。先明确要回答的问题，再显式选择 `--mode`。材料只有一层，并不意味着图已经沿厚度积分。

| 要观察的量 | 数学操作 | 电荷单位（默认显示） | 本脚本选项 |
|---|---|---|---|
| 单平面局域体密度切片 | 固定一个平面的位置，取该处密度；不乘厚度 | $e/\text{Å}^3$ | `--mode slice --axis 3 --fraction F` |
| 整胞层积分面密度 | 沿省略方向覆盖一个完整周期胞，包含胞内所有物理层与真空区 | $e/\text{Å}^2$ | `--mode project --axis 3` |
| 某一物理层的面密度 | 先定义该层的上下边界或分区，再在该范围积分 | $e/\text{Å}^2$ | 当前未实现层窗口；不能用全胞 `project` 自动分层 |
| 单层材料 | 描述结构层数，不是密度的降维操作 | 取决于实际选择的量 | 仍需在 `slice` 与整胞 `project` 之间明确选择 |

以省略方向垂直于 $xy$ 平面的晶胞为例，原始量是三维体密度 $\rho(x,y,z)$。单平面切片只是把 $z$ 固定为 $z_0$：

$$
\rho_{\mathrm{slice}}(x,y;z_0)=\rho(x,y,z_0).
$$

因此切片仍以每体积计量。若沿一整个胞高 $L_z$ 积分，长度因子使体密度变为面密度：

$$
\rho_{\mathrm{sheet}}(x,y)=\int_0^{L_z}\rho(x,y,z)\,\mathrm dz.
$$

这张面密度图保留面内分布，合并厚度方向的信息；它不是某个 $z_0$ 处的值，也不是沿厚度的平均值。若要单独研究某一物理层，必须另行给出 $z_1,z_2$ 等边界：

$$
\rho_{\mathrm{layer}}(x,y)=\int_{z_1}^{z_2}\rho(x,y,z)\,\mathrm dz.
$$

上式只说明目标量；本脚本不提供该有限层窗口操作。多层体系的全胞积分会把各层贡献合在一起。对单层材料，整胞积分也包含真空中的密度尾部；一个原子平面的切片则只采样该平面。

电流同理：切片保留局域电流密度 $\mathbf j(x,y,z_0)$，单位为 $e/(a_0^2t_0)$；整胞积分得到面电流 $\mathbf J_{\mathrm{sheet}}=\int\mathbf j\,\mathrm dz$，单位为 $e/(a_0t_0)$。先积分矢量，再取面内分量的模，不能先取模再积分。

默认图题和色标明确写出 `plane slice` / `Plane` 或 `full-cell sheet integral` / `Sheet`。`--title` 可改图题，色标的量与单位仍由所选模式决定。JSON 和 Markdown 同时记录 `representation`、`display_unit`、`native_reduced_unit`、`integration_scope` 与降维方式，便于核查自定义题名。

## Slice, column integral and Cartesian geometry

Native sampling is periodic: $\mathbf r=(i/n_x)\mathbf a_1+(j/n_y)\mathbf a_2+(k/n_z)\mathbf a_3$, without a duplicated endpoint.
`--mode slice --axis 3 --fraction 0` interpolates periodically at the cell-origin
plane; it is the graphene plane only when the matched geometry places graphene
there. A fraction such as 0.5 selects the mid-cell plane, which may be vacuum.
`--mode project` integrates the omitted fractional column with normal length
measure. It is an integral, not an average. If $h$ is cell height normal to the
retained plane, the density sheet is

$$
\rho_{\mathrm{sheet}}(i,j)=\frac{h}{n_z}\sum_k\rho(i,j,k).
$$

For an omitted lattice vector perpendicular to the plane, this is the normal
projection. If that vector also has an in-plane component, it is an oblique
fractional-column integral represented on the retained cell face; it is not an
orthogonal-ray projection. The script never silently treats a skew cell as a
rectangle. An orthonormal plane basis supplies Cartesian coordinates and current
components; axis 3 of an xy-oriented cell gives ordinary x and y.

The volume integral is `sum(rho)*abs(det(cell))/prod(grid_shape)`. The sheet
integral uses the true parallelogram area. Raw negative density samples remain
in statistics and integrals. Periodic interpolation in the figure does not alter
saved scalar samples. Current magnitude is computed *after* vector integration
and projection into the displayed plane, so it differs from the integral of a
pointwise magnitude; normal current is omitted from the color map but retained
in the three-component volume integrals and saved reduced array.

Charge plots default to electrons per square Angstrom for projections and per
cubic Angstrom for slices; `--density-unit bohr` keeps atomic length units.
`--length-unit bohr` changes coordinate labels independently. Current remains in
known atomic units: $e/(a_0t_0)$ for sheets and $e/(a_0^2t_0)$ for slices. No
unknown physical unit conversion is guessed. Multi-channel charge plots display
the selected stored density channel; establish its physical meaning separately.

## Examples

Resolve `SKILL_ROOT` to the installed skill's absolute root directory. Run these
commands from the user's calculation directory so relative input and output
paths refer to that directory; changing into the skill directory is unnecessary.

```bash
python "$SKILL_ROOT/knowledge/scripts/plot_fields.py" CHGCAR --kind charge --restart CHGCAR.restart --mode project --output-dir figures --name charge_sheet
python "$SKILL_ROOT/knowledge/scripts/plot_fields.py" CHGCAR --kind charge --restart CHGCAR.restart --mode slice --fraction 0 --output-dir figures --name charge_slice
python "$SKILL_ROOT/knowledge/scripts/plot_fields.py" CRTCAR --kind current --restart CHGCAR.restart --mode project --stride 2 --output-dir figures --name current_sheet --lang zh-Hans
```

Choose distinct names such as `charge_slice` and `charge_sheet` when producing
both modes. The backward-compatible default basename remains `field`; it does
not encode the mode and existing outputs are refused. The CLI defaults to
`project`, so pass `--mode` explicitly in analysis commands.

Outputs are PNG, PDF and SVG by default, an NPZ containing unchanged reduced
samples, plane vectors and Cartesian mesh, and JSON/Markdown provenance with
SHA-256, geometry, raw extrema and integrals. `--formats png pdf` limits image
formats; `--clim MIN MAX` supplies a shared scale for comparisons in the chosen
display units. `--stride` controls arrow sampling; arrows keep a physical scale
and include a native-unit key. Periodic atom markers come from actual restart
coordinates. Charge differences require compatible geometries, grids and units;
subtract signed samples without clipping and use a diverging scale.

Before interpreting a map, confirm file/restart identity, density integral,
current availability and the actual stage's field settings. A small integrated
current can coexist with finite local circulation; it does not establish a
continuity test or transport current. Native band plots are a separate workflow:
use `plot_bands.py` and `analyze_eigenvalues.py`, and distinguish path-sampled
separations from a Brillouin-zone fundamental gap.
