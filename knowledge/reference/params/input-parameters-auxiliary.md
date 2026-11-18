# 结构、路径与辅助参数参考

这是随技能打包的输入知识快照（2026-11-16），不是官方手册或版本支持保证。先与用户发行资料、示例及实际日志核对；缺少源码不影响普通准备和分析。未知的结构、UPF或物理设置必须列为缺项，不用占位数据冒充完整输入。先读[输入生成](../topics/input-generation.md)；普通模板只取当前阶段需要的项目。

## 入口、结构与物种

| 键或块 | 类型/形状 | 参考默认 | 用户含义与限制 |
| --- | --- | --- | --- |
| `Model` | 字符串 | Charge_ordering | 缺省不是DFT，必须明确 `Model DFT`。 |
| `DFT.home_made` | logical | T | 本技能的PW/PWRS选择；F与其他模型路线不在本技能覆盖范围。 |
| `number_of_species` | integer | 1 | 多物种明确给出，与物种索引、原子符号和UPF行数/顺序一致。 |
| `READ_POSCAR` | logical | F | T读取工作目录真实POSCAR；F使用FDF结构。按用户现有结构方式保留。 |
| `SYMPREC` | real | 1e-5 | 对称性容差参考值，适用几何约定与影响需结合版本和实际约化日志核对。 |
| `%include` | FDF指令 | 无 | 保留真实文件及其相对工作目录；核对重复定义的首个生效位置，不靠末尾追加覆盖。 |
| `NumberOfAtoms` | integer | 0 | 有效结构需要正确正原子数，与坐标行数一致；0不构成可计算结构。 |
| `AtomicCoordinatesFormat` | 字符串 | NotScaledCartesianBohr | 缺省为Bohr笛卡尔；有意Angstrom/分数坐标设置必须保留，按配套示例确认准确字面值。 |
| `AtomicCoordinatesAndAtomicSpecies` | 每原子5字段 | 原子数>0时必需 | 每行 `x y z species_index symbol`，符号最多2字符；不是四字段坐标表。符号也需与+U物种选择一致。 |
| `AtomicCoordinatesOrigin` | 3实数块 | (0,0,0) | 与坐标输入相同单位/格式，参与坐标缩放前的原点偏移。 |
| `LatticeConstant` | 带长度单位的real | 0 Bohr | 必须非零；晶格与BandLines均需它，不能因路径使用倒格坐标就删去。 |
| `LatticeVectors` | 3行×3实数 | 两种晶格块均无时单位阵 | 每行一个晶格向量，乘LatticeConstant；与LatticeParameters二选一，不用缺省替代未知晶胞。 |
| `LatticeParameters` | 一行6实数 | 无 | `a b c alpha beta gamma`，前三项乘LatticeConstant，角度degree；与LatticeVectors互斥。 |
| `SuperCell` | 3×3整数块 | 单位阵 | 结构变换，需有效LatticeConstant；核对扩胞后的原子数与物种映射。 |
| `pseudo_pot_files` | 每物种一行文件名 | 必需 | 工作目录真实UPF本地副本；顺序对应species_index，见[输入生成](../topics/input-generation.md)。 |
| `Z_values` | 每物种integer | 由结构元素符号确定；无符号时参考回退1 | 结构符号有效时通常可省；不能把默认概括成所有物种均1，也不替代UPF价电子数。 |

一个五字段坐标行的语法是 `0.0 0.0 0.0 1 Si`，只说明字段次序，不提供晶胞或材料模型。多物种结构需逐行核对符号、物种索引和UPF，不能从该行推导赝势选择。

## k 网格与路径

| 键或块 | 类型/形状 | 参考默认 | 用户含义与限制 |
| --- | --- | --- | --- |
| `kgrid_Monkhorst_Pack` | 三行，每行3整数+1实数 | 单位矩阵与零偏移 | 普通PW/PWRS缺省Gamma，显式给完整三行；不能用原始网格乘积替代实际约化点数。 |
| `BandLinesScale` | 字符串 | pi/a | 本参考的字面值为 `pi/a` 或 `ReciprocalLatticeVectors`；保留用户有意坐标约定。 |
| `BandLines` | 多行块 | 无路径 | 每行 `nkl kx ky kz [label]`；整数nkl用于路径插值与总点数，需非零LatticeConstant。用实际展开的总点数安排池。 |

不要用 `kgrid_cutoff` 替代本技能普通PW/PWRS的显式网格；本页未给其可移植任务保证。`SpinSpiral` 或 `Spin.Spiral` 名称出现在其他输入中也不构成此版本支持PW自旋螺旋的证据。路径语法和文件读取见[能带绘图](../topics/band-plotting.md)，资源见[并行池](../topics/kpoint-band-parallelism.md)。

## +U 与站点磁矩

| 键或块 | 类型/形状 | 参考默认 | 单位与限制 |
| --- | --- | --- | --- |
| `DFT.n_manifolds_plus_U` | integer | 0 | 非负壳/选择记录数；与DFT_plus_U块存在性及行数一致。只有0且无块才是关闭。 |
| `DFT.plusU_type` | integer | 1 | 1为Ueff，2为U/J；只用这两个值，type2 g壳参考拒绝。 |
| `DFT_plus_U` | 记录数对应的行 | 记录数0时不提供 | type1每行 `species nl Ueff [IDs...]`；type2为 `species nl U J [IDs...]`。Ueff/U/J均裸Ha。 |
| `DFT.RWIGS` | 每物种1实数的块 | 全0 | Angstrom；普通非共线尾部及有自旋MD的站点积分需正且有限半径，不能当自动元素半径省略。 |

`DFT_plus_U` 中 `nl` 为两字符壳标记（一位主量子数加s/p/d/f/g），`species` 与结构符号对应。IDs是**该物种内**原子序号；省略代表全部该物种原子，不是全局任意原子。行数精确匹配count；避免重复/重叠选择、未知符号、`*` 或 `/` 控制字符；本参考行长上限200字符，支持行尾 `#` 或 `!` 注释。

参考不支持PWRS、SCF_ONLY或RRAM与+U组合。SCF到能带还需匹配占据辅助数据；不能只复制CHGCAR就宣称完成+U交接。RWIGS是站点积分球，不是Hubbard投影壳半径，也不由通用atomic_radius代替。文件交接与SOC/UPF关系见[PW指南](../modules/pw.md)。

## Berry、Chern、电场与偶极

| 键 | 类型 | 参考默认 | 单位、条件与限制 |
| --- | --- | --- | --- |
| `DFT.LBERRY.NPPSTR` | integer | 16 | 每条k串点数，替换所选方向采样；按任务收敛测试。 |
| `DFT.LBERRY.IGPAR` | integer | 1 | 倒格矢方向索引，参考需对角网格矩阵。 |
| `DFT.LBERRY.NINT` | integer | 1 | Chern选定带组起点，准确拼写NINT。普通求态流程检查占据与隔离；新版直接波函数流程须满足1<=NINT<=NEND<=实际读入带数。 |
| `DFT.LBERRY.NEND` | integer | 普通求态流程为实际共同占据带数；直接波函数流程须显式提供 | 普通求态流程终点不超过共同占据带数。新版LCHERN1+LNSCT+RWAVE1明确选择带组（可含未占据带）；若恢复能谱则检查相邻带隔离，不推断缺失占据。详见[两种陈数流程](../modules/pw.md#chern-calculation-after-scf)。 |
| `DFT.LCHERN.NKX` | integer | 12 | 正整数，二维全网格第一方向点数；参考单k池/单band池、对角网格，沿用偏移。 |
| `DFT.LCHERN.NKY` | integer | 12 | 正整数，二维全网格第二方向点数，第三方向为1；同NKX限制。 |
| `DFT.Efield.IGPAR` | integer | 3 | 电场流程的倒格方向，不继承LBERRY.IGPAR默认；绝缘占据等条件仍需满足。ISPIN1参考要求偶数电子。 |
| `DFT.DIP.EDIR` | integer | 3 | 偶极修正轴方向，仅使用1..3；主开关准确拼作DFT.LDIPFEILD。 |

参考不提供 `DFT.DIP.EMAXPOS`、`DFT.DIP.EOPREG` 的可用能力保证，不从其他软件或旧输入猜造这些设置。拓扑或响应参数可读并不证明目标材料满足隔离带、绝缘性、赝势及自旋条件。

## 独立 unit cell

以下用于任务确实需要独立参考晶胞时；普通单胞计算不重复添加。

| 键或块 | 类型/形状 | 参考默认 | 单位与限制 |
| --- | --- | --- | --- |
| `unit_cell_in_Ang` | 3×3实数块 | 主晶胞 | Angstrom；显式块优先于READ_POSCAR_UC。 |
| `READ_POSCAR_UC` | logical | F | 上述块缺失时，T读取工作目录实际POSCAR_UC。 |
| `unit_cell.na` | integer | 主结构原子数 | 改变后必须有对应独立原子坐标，不能沿用错误行数。 |
| `Atoms_in_unit_cell_Ang` | 每独立晶胞原子一行 | 原子数相同时复制主结构 | 每行 `x y z species_index`，坐标Angstrom；原子数不同时该块必需。 |

## 特殊外势与范围外参数

| 键 | 类型 | 参考默认 | 条件与限制 |
| --- | --- | --- | --- |
| `DFT.Bfield.FFT.Ny` | integer | 10 | 仅DFT.inputV T的特殊外势任务；参考将奇数调为偶数。不是普通磁PWRS GRID_NY。 |
| `DFT.Bfield.FFT.nxcap` | integer | 10 | 同属特殊外势任务的横向截断计数；不替代普通PWRS网格或DFT.PWL.n0。 |

本页不列MC、TB、有效Hamiltonian或其他模型的通用键全集。不要用 `Spin_values` 替代 `DFT.MAGMOM`，用 `atomic_radius` 替代 `DFT.RWIGS`，用 `atom_mass` 替代原生MD的 `DFT.MASS`，或把通用 `DensityOfStates` 块当原生PW/PWRS DOSCAR控制。普通PW电子数由UPF价电子和tot_charge决定，不由其他模型的 `Charge_atoms`、`ZVAL` 或 `chempot` 推断。

历史 `PWL.*` 名称不能直接迁移到当前PWRS；但 `DFT.PWL.n0` 仍是本参考磁通控制，详见[兼容性](../topics/legacy-parameters.md)。CHGCAR、WAVECAR、`.restart` 及+U占据数据是计算文件，不是额外FDF键。仅有文件名或成功读入不能证明交接有效。
