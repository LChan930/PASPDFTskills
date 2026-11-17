# BaTiO3：固定晶胞离子优化

先用[状态机](pw_relax_state_machine.md)定位当前阶段，再按本课对应小节操作。[检查单](pw_relax_user_checklist.md)用于实际交接，[历史笔记](pw_relax_run_notes.md)只解释已有证据边界。

## 可复制的真实文件树

每个下列末级目录均包含 `lattice_model.fdf`、实际引用的 `siesta.ANI`、`dependency-manifest.json` 和阶段README。UPF不附；没有密度、历史输出或预制结果。

- [batio3_relax/polar_plus](../templates/batio3_relax/polar_plus/README.md)：5原子，物种 Ba/Ti/O；FDF/引用结构/依赖清单齐备，UPF待提供。
- [batio3_relax/cubic_reference](../templates/batio3_relax/cubic_reference/README.md)：5原子，物种 Ba/Ti/O；FDF/引用结构/依赖清单齐备，UPF待提供。
- [batio3_relax/polar_minus](../templates/batio3_relax/polar_minus/README.md)：5原子，物种 Ba/Ti/O；FDF/引用结构/依赖清单齐备，UPF待提供。

## 证据等级

本包标记为 `input-derived / not-runtime-tested`：输入与实际引用结构来自现有案例，构建时只作静态闭包和哈希检查，没有启动 PASP 或 MPI。目录中已有历史输出不能自动升级本模板的证据等级。历史测试、当前输入静态检查、本次实际运行三者分别记录。所有 UPF 因再分发权限未明确而不随包分发，必须由用户合法提供；没有 UPF 时不具备运行完整性。

## 学习目标与三个控制

用五原子 BaTiO3 学习固定晶胞下离子位置优化。`batio3_relax/polar_plus` 是实际根案例的极性初态；`cubic_reference` 是中心对称结构的独立 SCF 能量控制；`polar_minus` 是另一极性初态的独立优化。三个目录不是自动串行覆盖同一结构的三步。物种顺序为 Ba/Ti/O，实际结构由各自 `siesta.ANI` 决定。

### 第一阶段：读初态，准备固定胞优化

先逐一比较晶格与 Ti 等原子坐标，记录初始结构哈希。polar_plus 为6×6×6，另两组4×4×4；三组都保留35 Ha、全 k 请求、电子EDIFF1e-7以及案例的mixing设置。根案例nk_pool36是资源请求，不凭6×6×6就认定当前实际点数。原质量块 137.327/47.867/15.999 按物种顺序提供，不使用默认1 amu充当元素质量。

```text
DFT.LRELAX T
DFT.nstep 50
DFT.EDIFFG -0.02
```

这表示最多50步离子更新，负 EDIFFG 的绝对值是0.02 eV/Angstrom力阈值；它与 Hartree 电子EDIFF不同。参考 `DFT.relax.fixed_cell` 默认T，本课不追加冗余键，不能将其改F后宣称有变量胞优化支持。cubic_reference 没有 LRELAX，是单独 SCF，不应解释为优化步0之后的最终结构。

### 第二阶段：运行并核对离子与电子两层状态

在独立新目录运行选定分支。每个离子步检查电子收敛、力是否有限、原子数和晶格是否保留。`F.dat` 是力相关证据线索，必须读实际单位/步数；有文件或跑满50步不等于满足力阈值。找到实际结束原因，区分达到力/能量标准、达到步数上限、电子失败或进程异常。固定胞还需核对初末晶格，不能仅凭输入开关断言实际不变。

### 第三阶段：提取与移交最终结构

从匹配本次已验证输出中识别最终离子坐标、晶格、物种顺序与单位，另写新结构并记录来源帧/步，不把输入 `siesta.ANI` 原样当作最终结构。若没有明确最终结构记录，将提取标为未完成。用新结构准备独立 SCF 以建立新的电子基态与后续 bands 配对；优化期间旧密度元数据不能跨几何冒充匹配参考。

### 第四阶段：比较控制并报告限制

比较 polar_plus、polar_minus、cubic_reference 前统一适用数值设置并做精度验证。当前网格不同，不能把原有不同设置能量差当作已收敛极化势垒。最后交接每个分支实际初末结构、电子与离子收敛、最大力/步数/单位、是否上限终止、计算参数与输出哈希。模板未附经验证的最终结构或优化曲线。

排错：SCF失败先解决电子层再判断离子；力未达标不能把退出0当成功；对称初态可能保持在对称点，是否需要破缺由物理方案决定，不自动增加随机扰动；无最终坐标不得伪造优化结果。


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
