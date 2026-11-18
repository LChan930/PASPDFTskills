# PW/PWRS 输入生成与必需文件

适用于 `Model DFT`、`DFT.home_made T` 的 PW/PWRS 用户。以下参数与组合是随技能打包的参考快照（2026-11-16），不是官方版本支持保证。先核对用户发行包的手册、示例、版本资料与实际日志；未确认时标记兼容性待查，不要求源码。分类表为[核心参数](../params/input-parameters-core.md)、[结构与辅助参数](../params/input-parameters-auxiliary.md)、[MD 与响应参数](../params/input-parameters-workflows.md)。

## 先收集实际资料

至少确认计算阶段、工作目录、启动方式、结构、每物种实际 UPF、所需自旋/电荷、精度目标以及已有输入/include。没有材料或赝势资料时列出缺项，可提供明确标记的结构草稿，不能称为可运行输入。不要猜造 `PASP.x` 命令行开关、版本命令或 dry-run；使用用户已知的 launcher 与输入约定，核对实际读取的是 `PASP.input`、`lattice_model.fdf` 还是其他用户指定文件。

新建输入按以下顺序处理：

1. 明确写 `Model DFT`；其缺省模型不是 DFT。`DFT.home_made` 参考默认 T，可省略。先选单一主任务；MD、TDDFT、NAMD、能带和 EPC 等开关不是顺序执行队列，避免堆叠。
2. 保留完整实际结构或 `%include`。FDF 结构需非零 `LatticeConstant`、晶格、`NumberOfAtoms` 和每原子五字段 `x y z species_index symbol`。`LatticeVectors` 与 `LatticeParameters` 二选一；也可用 `READ_POSCAR T` 配实际 POSCAR。多物种明确 `number_of_species`，核对原子索引、符号与 UPF 顺序。不要从其他软件猜造必需的 `ChemicalSpeciesLabel` 块。
3. 根据 UPF 元数据核对元素、价电子、交换关联泛函、NC/US/PAW 类型及 SR/FR/SOC 信息。总电子数为赝势价电子和减 `DFT.tot_charge`，正电荷表示移除电子。文件名不能替代元数据；不把一个物种的 SR/FR 文件互换。
4. 选择符合物理任务的截断、带数、k 网格/路径、展宽、自旋初猜及收敛目标。默认值只是缺键时的参考，不是材料精度推荐。普通 PW 不添加无关 MD、滤波、磁场或预条件控制。
5. 检查主输入和全部 include 中的重复键与块。不要假设追加同名键就能覆盖；按实际生效的首个定义审计，在原位置修改。保留用户有意明确的默认值，不盲目精简。

## 小型输入骨架

以下为**非完整模板**，仅说明组装方式。使用前必须提供真实的 `structure.fdf` 与经核对的 UPF，并按用户体系补足数值与物理设置；文件名不是随包提供的数据。

```text
Model DFT
%include structure.fdf

%block pseudo_pot_files
species1.upf
%endblock pseudo_pot_files
```

这是单物种、默认 Gamma 网格的普通 PW 骨架。默认 ENCUT、带数、温度/展宽和收敛阈值均未验证适用于用户材料。完整交付应替换成真实文件名并提供实际结构，注明已选择和未收敛测试的物理参数；不能把该骨架当完成的材料输入。

需要 SCF 网格时，给完整三行，每行三个整数和一个偏移；以下只是语法示例，`4×4×4` 不代表推荐采样密度：

```text
%block kgrid_Monkhorst_Pack
4 0 0 0.0
0 4 0 0.0
0 0 4 0.0
%endblock kgrid_Monkhorst_Pack
```

路径能带改用完整 `BandLines` 和有意选择的 `BandLinesScale`，保留非零 `LatticeConstant` 及目标 `DFT.NBAND`。不要把 SCF 网格复制进能带输入当作路径，也不要只给高对称点标签而缺坐标与点数。

## 赝势与工作目录

`pseudo_pot_files` 按物种顺序每行一个文件名，支持带引号的相对或绝对路径。路径含 `/`、空格或逗号时，必须把整个路径放在单引号或双引号内；未加引号的 `/` 会终止列表读取，不能因文件存在就判为有效。简单本地文件名 `C.upf` 可不加引号，但统一加引号最清楚。Linux/集群示例：

```text
%block pseudo_pot_files
  '../potentials/C.upf'
  "/shared/pseudo library/O.upf"
%endblock pseudo_pot_files
```

两行仅表示两个物种的路径语法，不能脱离实际物种数量和顺序照搬。相对路径基于 PASP 进程启动工作目录，不基于包含此块的 include 文件位置；不会按 shell 规则展开 `~` 或环境变量。保持完整路径短于 256 个 ASCII 字符以避免文件名缓冲区截断，非 ASCII 路径还须核对目标环境编码。绝对路径须在计算节点可访问；不要把 Windows 本机路径直接当成 Linux 路径。也可将每阶段实际 UPF 原字节复制到阶段工作目录，用带引号的本地文件名以提高可移植性。SCF 与能带须保持相同已核对赝势，记录来源、字节数和 SHA-256，并核对 launcher 实际切换后的工作目录。

## 默认、覆盖、条件与限制

“条件默认”仅在缺键时生效；“覆盖”可能取代显式值；“条件使用”不代表所有组合支持。下表属于参考快照，特殊组合须与用户版本资料或实际错误信息核对。

| 触发或任务 | 参考行为 | 生成/审计要点 |
| --- | --- | --- |
| ENCUT 与 ENCUT_RHO | ENCUT_RHO 缺省为所选 ENCUT 的 4 倍 | 两者显式给值需带能量单位。PWRS 轨道不按普通 PW 截断球解释；密度截断与网格另查 PWRS 指南。 |
| NBAND=0 | 根据电子数、基组上限与自旋自动选择 | 显式非零 NBAND 不自动自旋倍增；根据占据和空带需求选择，不硬编码未知体系带数。 |
| all-k | `DFT.luse_all_kpoints T` 使 `DFT.lusesym F` | 只关空间对称性仍可能时间反演约化；并行池用实际总点数。 |
| 轨道磁场 | Bfield 强制 RS、all-k、apply_Hpsi，关闭空间对称性 | `DFT.PWL.n0` 默认1代表非零通量；零通量需显式0。Bfield 不自动打开 Zeeman，也不自动选预处理模式4。 |
| Zeeman | Zfield 强制 all-k、apply_Hpsi，关闭空间对称性，但不强制 RS | 独立 `Zfield` 块缺失参考默认零并警告；Bfield 与 luseBasZ 同时适用时可取轨道磁场，独立块不再决定该值。 |
| 有限电场、MD/NAMD/TDDFT | 参考使用全 k 并关闭对称性 | LEfield 缺 `DFT.Efield` 块默认非零 z 场0.001原子单位；必须有意指定场。 |
| 完整 PWRS | ALGO=4，单 band 池；kinetic/vnl 为 T | 反向 F 设置不能改成普通 PW。核对 NC、XC、自旋、SOC 与滤波限制。 |
| 预条件 | `DFT.RS.PRECONDITIONER` 默认0；模式3/4为可选择项 | LPRECOND 不是实空间预处理接口；模式3需零有效磁通，模式4需磁场及参考支持规范。详见[兼容性](legacy-parameters.md)。 |
| DENSITY_FFT_BOX | 专用、严格受限的磁 PWRS 能量流程 | 不是一般精度开关；要求 SCF_ONLY、ISPIN1、ALGO4、单 band 池、mode0、LPRECOND F、线性混合、局域 NC/无投影/NLCC、Slater/PZ LDA 等；不得推广重启或能带。显式网格三维全0或全>=2。 |
| 初始磁矩 | ISPIN!=1 时缺 MAGMOM 默认每原子(0,0,1) | 即使共线也按每原子三分量给定。目标磁态必须明确，不能把缺块解释为非磁。 |
| 站点球积分 | RWIGS 默认每物种0，不能当自动原子半径 | 普通非共线尾部及有自旋 MD 涉及站点磁矩时，给每物种正且有限的 Angstrom 半径。它不定义 Hubbard 壳。 |
| +U | count默认0、type默认1；裸Ueff或U/J单位Ha | count、块、物种、壳和站点选择一致。参考不支持 PWRS/SCF_ONLY/RRAM +U、type2 g壳；SCF/能带另需占据辅助数据。 |
| SCF_ONLY | 在常规密度/波函数交接文件写出前结束 | 不作为能带前驱。普通 SCF 需交接时用整数 `DFT.LCHARG 1`；检查收敛与匹配的密度/参考文件。 |
| 路径能带 | 自动读取匹配 SCF 密度及参考文件，BandLines 优先 | 不需为此冗余 `RCHARG 1`；只有 CHGCAR 不足，MAXITER 结果不当作合格前驱。SCF 与路径资源分别配置。 |
| 优化 | LRELAX T 且 DFT.nstep>0 才有离子更新 | nstep默认0只做初始计算；参考只支持 fixed_cell T。DFT.nstep 不同于 PW_MD.nstep 与 RS.MD。 |
| MD | lmolBC默认继承Bfield；场或分子Berry时solver/thermostat默认3/0，否则1/1 | 场/分子Berry仅接受3/0/1/0的solver/thermostat/ensemble/barostat组合，显式冲突不靠后续覆盖补救。无场ensemble2强制solver1，3/4强制2/4/1。 |
| MD 数据 | velocity_temp默认跟随temperature；显式速度块优先 | 质量默认全1不代表元素质量，真实轨迹必须给正确DFT.MASS；NVT默认零阻尼不能作为可用Langevin设置。 |
| NAMD | 自身时间步、子步数与总步数覆盖相关TDDFT/MD设置 | 用自身solver_TD选电子积分器；参考强制exp_method1、output_energy F，初始SCF后线性混合0.5。不要外推磁性支持。 |
| TDDFT | ext_field T 必须有 TD_external_field；投影需output_eigval | ISPIN2参考拒绝，ISPIN1关闭原子磁矩输出；output_chgmid会替换工作目录chgs，保留原数据后再运行。 |
| EPC/EPR | 需匹配的dvloc；二阶EPR还需R_index | 不是普通SCF选项。二阶且RIA F时超胞倍数需全奇数；未明确的响应格式与组合先取发行资料。 |
| RRAM | 需要possplit及poselectrode的有效区域 | 零偏压不免除几何输入，区间宽度需非零；偏压/罚项单位需版本资料确认，不给通用数值推荐。 |

## 验证与交付

逐阶段列出结构、物种/UPF 元数据与摘要、输入/include、工作目录、所选物理设置及版本依据。按[k 点与并行池](kpoint-band-parallelism.md)使用约化后全局点数；未观察到点数时保留1/1默认，并说明效率未知，不为了整除改变对称性。

先完成文件与输入一致性检查，再按授权运行。输入静态检查不证明目标二进制可读、SCF 收敛或精度达标。结果状态与文件交接分别按[验证与报告](validation.md)、[PW 用户指南](../modules/pw.md)解释；启动环境问题见[提交排错](workshop.md)。

## 包内静态审计

生成候选输入后，按 [输入审计契约](input-audit.md) 使用 `knowledge/scripts/audit_inputs.py` 读取确切 FDF 或运行目录。工具覆盖可确定的 include/块、结构/物种/UPF 与阶段依赖、有限登记表默认/条件及 ranks/pool 一致性。`--irreducible-kpoints` 只接受本阶段已证实的全局约化点数；未知则省略。工具不自动挑选物理参数，也不认证目标发行版或运行收敛。
