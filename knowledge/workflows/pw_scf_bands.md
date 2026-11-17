# BaTiO3：从 SCF 到能带

先用[状态机](pw_scf_bands_state_machine.md)定位当前阶段，再按本课对应小节操作。[检查单](pw_scf_bands_user_checklist.md)用于实际交接，[历史笔记](pw_scf_bands_run_notes.md)只解释已有证据边界。

## 可复制的真实文件树

每个下列末级目录均包含 `lattice_model.fdf`、实际引用的 `siesta.ANI`、`dependency-manifest.json` 和阶段README。UPF不附；没有密度、历史输出或预制结果。

- [batio3/01_scf](../templates/batio3/01_scf/README.md)：5原子，物种 Ba/Ti/O；FDF/引用结构/依赖清单齐备，UPF待提供。
- [batio3/02_bands](../templates/batio3/02_bands/README.md)：5原子，物种 Ba/Ti/O；FDF/引用结构/依赖清单齐备，UPF待提供。

## 证据等级

本包标记为 `input-derived / not-runtime-tested`：输入与实际引用结构来自现有案例，构建时只作静态闭包和哈希检查，没有启动 PASP 或 MPI。目录中已有历史输出不能自动升级本模板的证据等级。历史测试、当前输入静态检查、本次实际运行三者分别记录。所有 UPF 因再分发权限未明确而不随包分发，必须由用户合法提供；没有 UPF 时不具备运行完整性。

## 学习目标与文件流

用同一五原子立方 BaTiO3 完成“电子密度收敛 → 固定密度路径能带 → 绘图”。输入结构包含 Ba、Ti、O 三物种，笛卡尔 Angstrom；Ba/Ti/O 的 UPF 顺序不可换。SCF 的 6×6×6 网格服务布里渊区积分，bands 的 Gamma–X–M–Gamma–R–X 路径服务绘图；两者的点数与资源不能互换。

### 第一阶段：SCF 电子基态

进入 `batio3/01_scf`。先读结构的晶格和五行坐标，再检查 `Z_values` 为 56 22 8，与 Ba/Ti/O 文件一一对应。35 Ha、NELM150、EDIFF1e-7 是教学起点，保留 `DFT.LCHARG 1` 以输出密度。原注释“20 reduced k points”和 nk_pool20/nb_pool2 只能结合匹配输入的真实日志和 ranks 使用，不能凭注释认证当前点数。

```text
DFT.ENCUT 35 Hartree
DFT.NELM 150
DFT.EDIFF 1.0d-7
DFT.LCHARG 1
```

运行后检查收敛记录、电子数、SCF EF 单位与密度写出。当前参考能带交接需要成对的 `CHGCAR` 与 `CHGCAR.restart`，后者记录 SCF 来源与 EF，必须绑定这份密度的原始字节。仅老密度文件不证明已建立能带参考。

### 第二阶段：路径能带

进入独立 `batio3/02_bands` 目录。复制**已验证同一次 SCF**的密度和对应 `.restart`，保持原字节；不得改 EF/status 或拼接不同运行的文件。保持相同结构、UPF、ENCUT、电子数、自旋及 Hamiltonian。模板显式 NBAND20、NELM300、EDIFF1e-6 和 `DFT.lbandstructure T`；完整 BandLines 已在 FDF 中。不要把路径采样当作 SCF 积分网格。原 40/1 池需按实际展开路径点和 ranks 检查。

检查日志的 `PASP_BAND_REFERENCE source=SCF_RESTART` 与 `PASP_BAND_RESULT status=EIGENVALUES_CONVERGED`（当前参考格式）。MAXITER 即使写出 `TB.bands` 也不能称能带迭代已收敛。旧版缺现代标记时保留 unknown，结合实际版本证据，不能造一个 marker。

### 第三阶段：图与采样能隙

将 `TB.bands`、对应 SCF/band 日志和配对来源交给 [输出分析课](output_analysis.md)。原生能量是 Hartree，默认绘图输出 eV，以文件记录参考减一次。默认图题保持 `Electronic band structure`，物理收敛、来源和限制写进报告/JSON，图内不自动添加 ISPIN 或警告副标题。路径上的带隙不等于全布里渊区基本带隙。绘图成功不补足运行收敛证据。

排错：缺 `.restart` 回到同设置 SCF 建立合法配对；密度哈希/几何不匹配不要修改元数据绕过；bands MAXITER 检查真实谱收敛与求解设置；UPF 缺失先补依赖，不把失败当算法问题。


## 如何建立并运行当前阶段

1. 打开本课链接的阶段 README，复制该**末级目录**到自己的新工作目录；不要在技能目录里运行。保留 `lattice_model.fdf` 与它 `%include` 的 `siesta.ANI`。不要拿旁边未引用的 `cell.str` 替换结构。
2. 按 `dependency-manifest.json` 的顺序与精确文件名，将合法取得的 UPF 放到运行目录。核对 SHA-256、元素、价电子、XC、相对论元数据；相同文件名不足以证明相同赝势。替换赝势后作为新计算验证。
3. 在 `PROGRESS.md` 写入：任务/分支/阶段、输入哈希、结构与 UPF 哈希、修改理由、已授权设置、实际 launcher、MPI ranks、池数、证据与下一步。已授权的常规操作直接继续；仅在缺失科学选择或实际提交授权时询问用户。
4. 完成当前状态机 S4 的预检。运行需要用户已经授权，并且使用其已知可用的 PASP.x 启动方式。本包不假定命令行参数或安装路径，也不依赖研讨会共享脚本。下面是**需要替换的命令位置，不是可原样执行命令**：

```text
cd <当前阶段的新运行目录>
<用户已验证的 PASP.x 启动命令> > stdout.log 2> stderr.log
```

启动命令是否包含输入文件参数、MPI/scheduler 及线程配置，以用户已有成功运行方式为准；不要虚构 `--dry-run` 等 PASP 参数。保留退出码和新日志。没有运行授权时，交付候选输入和精确下一步即可。

5. 按本课 S6 验证实际内容：进程退出、正确模型初始化、每次电子求解收敛、阶段完成、输出完整性分别判断。文件存在、退出 0、初始化完成都不等于物理收敛。失败时保留原日志，从新目录修订候选；通过后才移交下阶段。


## 精简输入和默认值

本包保留真实示例输入，注释不改变计算设置。新建输入只写物理需求、非默认设置和实际结构 include，不追加冗余默认标签。参考快照中 `DFT.ENCUT_RHO` 为所选 ENCUT 的四倍，不能硬写成固定 40 Ha；`DFT.NBAND` 的自动值依赖初始化，不凭经验伪造常数。ALGO/ISPIN 默认 4/1、池默认 1/1 不需机械重复。重启整数标志用 0/1。`lbandstructure T` 的 SCF 配对读入不需要额外重复 `RCHARG=1` 或 SCF 网格。自旋、+U、SOC、场和 MD 的条件设置必须按各课保留，不能因精简而删掉必要物理控制。

精确字段、单位和条件默认见 [core 参数](../reference/params/input-parameters-core.md)、[workflow 参数](../reference/params/input-parameters-workflows.md)、[auxiliary 参数](../reference/params/input-parameters-auxiliary.md)。运行版行为与本参考快照不同时，保留差异并取目标发行版证据。


## 资源与来源检查

核对当前阶段 MPI ranks。`DFT.nk_pool` 必须同时整除 ranks 与**实际生成/约化后的全局 k 点数**，不是网格乘积或高对称节点数。`DFT.nb_pool` 整除 ranks/nk_pool；普通 PW 不普遍要求总带数被 band 池整除。池数乘积不必等于 ranks。PWRS 与 SCF_ONLY 的 band 池为 1，PWRS 另需 ALGO=4。未知实际点数时，候选输入删去两个资源键以采用参考默认 1/1，或在已授权资源内减少 ranks。不得为整除而改变网格、磁序、对称性或路径。SCF 与 bands 独立检查。模板原池数是历史设置，不是通用可运行承诺。

参见[并行参考](../reference/topics/kpoint-band-parallelism.md)、[输入生成](../reference/topics/input-generation.md)、[验证层次](../reference/topics/validation.md)、[PW模块](../reference/modules/pw.md)、[PWRS模块](../reference/modules/pwrs.md)。
