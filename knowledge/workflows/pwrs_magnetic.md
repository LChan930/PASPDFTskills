# Graphene：零磁通与有限磁通

先用[状态机](pwrs_magnetic_state_machine.md)定位当前阶段，再按本课对应小节操作。[检查单](pwrs_magnetic_user_checklist.md)用于实际交接，[历史笔记](pwrs_magnetic_run_notes.md)只解释已有证据边界。

## 可复制的真实文件树

每个下列末级目录均包含 `lattice_model.fdf`、实际引用的 `siesta.ANI`、`dependency-manifest.json` 和阶段README。UPF不附；没有密度、历史输出或预制结果。

- [graphene/01_zero_flux/01_scf](../templates/graphene/01_zero_flux/01_scf/README.md)：2原子，物种 C；FDF/引用结构/依赖清单齐备，UPF待提供。
- [graphene/01_zero_flux/02_band](../templates/graphene/01_zero_flux/02_band/README.md)：2原子，物种 C；FDF/引用结构/依赖清单齐备，UPF待提供。
- [graphene/02_finite_flux/01_scf](../templates/graphene/02_finite_flux/01_scf/README.md)：2原子，物种 C；FDF/引用结构/依赖清单齐备，UPF待提供。
- [graphene/02_finite_flux/02_band](../templates/graphene/02_finite_flux/02_band/README.md)：2原子，物种 C；FDF/引用结构/依赖清单齐备，UPF待提供。

## 证据等级

本包标记为 `input-derived / not-runtime-tested`：输入与实际引用结构来自现有案例，构建时只作静态闭包和哈希检查，没有启动 PASP 或 MPI。目录中已有历史输出不能自动升级本模板的证据等级。历史测试、当前输入静态检查、本次实际运行三者分别记录。所有 UPF 因再分发权限未明确而不随包分发，必须由用户合法提供；没有 UPF 时不具备运行完整性。

## 学习目标与四目录

Graphene 两个分支保留相同几何和 `C_LDA_SR.ABIv0.4.UPF`，各含 `01_scf` 与 `02_band`。控制变量是 `DFT.PWL.n0` 的0/1，**两者都保持 `DFT.Bfield T`**；零磁通是该路径下的控制，不等于关闭Bfield的普通PW。输入的表示和默认 model/band 选择照实保留，不因教学套用其他模型标签。

### 第一阶段：零磁通 SCF

进入 `graphene/01_zero_flux/01_scf`，读实际 include 的晶胞和坐标，再检查碳单物种。模板是20×20×1积分网格、35 Ha、SIGMA0.001裸Hartree、默认Fermi–Dirac、EDIFF1e-7与LCHARG1。`ENCUT_RHO` 省略时按当前35 Ha的四倍，不添加固定无关值。自动带数按真实初始化记录，不擅自固定为偶数。

```text
DFT.Bfield T
DFT.PWL.n0 0
DFT.ENCUT 35 Hartree
DFT.RS.PRECONDITIONER 4
```

保留例中选择器调用值，不给未公开方法命名或推导。先核对目标发行版的操作兼容性：当前参考PWRS限ALGO4、band池1，NC、自旋/XC/场/过滤组合不能按普通PW随意推广。40个k池不是40 ranks的普适配置；实际约化点、所有强制全k条件与ranks都要核对。

### 第二阶段：有限磁通独立 SCF

进入 `graphene/02_finite_flux/01_scf`。与零磁通分支逐项比较，只把已明确的n0改为1并保留同一几何、UPF和数值方案；不同场要建立自己的SCF密度和参考。输入注释中的磁场数值仅针对此具体晶胞，是极高场教学模型，不作为实验场常识或通用n0换算。不要把零磁通产物直接重命名用作有限磁通已收敛结果。

### 第三阶段：各分支的 band 候选

分别进入对应 `02_band`；源目录名称用单数band，本包保持它。使用本分支验证后的密度/参考配对，保留 Bfield、n0、UPF、结构与35 Ha，切换 `DFT.lbandstructure T` 与实际 FDF 中的完整路径。路径段涉及各倒格矢方向，不能用普通二维六角路径替换后仍宣称同一案例。检查每阶段实际展开k点数和资源。

### 第四阶段：先判断失败，再考虑画图

较早盘点未见TB的缺口已由本次新审计更新：两分支现在均有 `TB.bands`，SCF和band日志的Bfield/n0分别对应T/0与T/1，四份日志均正常结束。正常结束仍需与电子和谱迭代收敛分别验证；旧失败/重试日志不能与当前输出混为一次运行。对当前运行检查错误、退出、参考恢复、谱迭代和实际输出；只在完整输出通过后绘图。源 band 文件的旧注释已在本模板修正为有限磁通 band 阶段，实际n0=1保持不变；以字段认分支。比较零/有限磁通的物理趋势只接受同阶段、同数值条件且已验证的结果。

排错：无TB或band失败交日志诊断，不从CHGCAR生成伪能带；k池不整除先调整资源保持物理网格；禁止把不支持组合的初始化通过解释为完整SCF/谱支持。磁场分支和默认普通PW行为分开解释。


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

## 电荷与电流数据

当前输出审计电荷积分均为8e；只有有限磁通SCF有CRTCAR。进一步的场格式、坐标/分量/单位与可视化门槛见[场绘图参考](../reference/topics/field-plotting.md)，使用本包 `knowledge/scripts/plot_fields.py` 时先查 `--help` 并按实际格式选择参数，不在此虚构CLI。缺电流文件的分支标missing，不从能带或电荷推造电流；既有结果来源与本模板新运行证据分开。
