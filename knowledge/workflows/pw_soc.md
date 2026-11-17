# Bi2Se3：SR 与 FR 赝势比较

先用[状态机](pw_soc_state_machine.md)定位当前阶段，再按本课对应小节操作。[检查单](pw_soc_user_checklist.md)用于实际交接，[历史笔记](pw_soc_run_notes.md)只解释已有证据边界。

## 可复制的真实文件树

每个下列末级目录均包含 `lattice_model.fdf`、实际引用的 `siesta.ANI`、`dependency-manifest.json` 和阶段README。UPF不附；没有密度、历史输出或预制结果。

- [bi2se3/01_no_SOC/01_scf](../templates/bi2se3/01_no_SOC/01_scf/README.md)：5原子，物种 Bi/Se；FDF/引用结构/依赖清单齐备，UPF待提供。
- [bi2se3/01_no_SOC/02_bands](../templates/bi2se3/01_no_SOC/02_bands/README.md)：5原子，物种 Bi/Se；FDF/引用结构/依赖清单齐备，UPF待提供。
- [bi2se3/02_SOC/01_scf](../templates/bi2se3/02_SOC/01_scf/README.md)：5原子，物种 Bi/Se；FDF/引用结构/依赖清单齐备，UPF待提供。
- [bi2se3/02_SOC/02_bands](../templates/bi2se3/02_SOC/02_bands/README.md)：5原子，物种 Bi/Se；FDF/引用结构/依赖清单齐备，UPF待提供。

## 证据等级

本包标记为 `input-derived / not-runtime-tested`：输入与实际引用结构来自现有案例，构建时只作静态闭包和哈希检查，没有启动 PASP 或 MPI。目录中已有历史输出不能自动升级本模板的证据等级。历史测试、当前输入静态检查、本次实际运行三者分别记录。所有 UPF 因再分发权限未明确而不随包分发，必须由用户合法提供；没有 UPF 时不具备运行完整性。

## 学习目标：把 SOC 的输入链与结果证据分开

采用五原子 Bi2Se3，物种顺序 Bi/Se，四目录是 SR SCF/bands 与 FR SCF/bands。四份实际输入和结构已打包，UPF 只提供精确清单。**本课没有已经验证的 SOC 能带结果**；不能从输入存在、全相对论文件名或无 SOC 运行推断 SOC 光谱完成。

### 第一阶段：SR 分支 SCF

进入 `bi2se3/01_no_SOC/01_scf`。核对 `Bi_ONCV_PZ_sr.upf`、`Se_ONCV_PZ_sr.upf` 的 scalar/has_so 头信息与哈希，保持结构和价电子设置。实际 ENCUT30 Ha、6×6×6、ISPIN4、五行零初始磁矩，`DFT.RWIGS` 为 Bi/Se 各 1.3/1.1 Angstrom 的**块**。ISPIN4 是非共线表示，不单独证明 SOC 开启。源 SR 池8/5需要对应32个实际约化点和40 ranks 等条件才可使用；不得凭注释推算当前约化点。

### 第二阶段：SR bands

只有 SR SCF 输出验证并具有合法密度/参考配对后，才进入 `01_no_SOC/02_bands`。模板沿用30 Ha、ISPIN4、RWIGS、SR UPF，显式 NBAND64，并使用 Gamma–Z–F–Gamma–L 教学路径。这一步需要的重启产品不随模板分发。

### 第三阶段：FR/SOC 分支 SCF

进入独立 `bi2se3/02_SOC/01_scf`。保持同一真实结构，使用 FR UPF：

```text
DFT.ISPIN 4
%block pseudo_pot_files
Bi_ONCV_PZ_fr.upf
Se_ONCV_PZ_fr.upf
%endblock pseudo_pot_files
```

从 UPF 元数据验证 fully-relativistic/has_so，结合当前运行回显判断 SOC，而不是添加虚构的 SOC 标签。参考限制非共线梯度 XC 的兼容性，本案例 PZ LDA 不能推广为所有非共线 GGA。FR 分支实际 ENCUT40 Ha，源注释在 SR bands 提到40 Ha与实际30 Ha不一致，以实际字段为准。

**现有 SR30/FR40 不构成只改变 SOC 的单变量数值对照。** 输入如实保留；若用户目标是隔离 SOC 效应，应在其已授权科学方案中统一适用的数值参数，并分别检查截断收敛，不能用教程悄悄改写原输入或宣称差异全由 SOC 导致。

### 第四阶段：FR/SOC bands

FR SCF 成功后，用自己的匹配密度/参考配对进入 `02_SOC/02_bands`，保持40 Ha、FR UPF、ISPIN4和同路径。不要复用 SR 配对跨 Hamiltonian。检查谱迭代、参考来源、TB 内容后交 [输出分析](output_analysis.md)；未运行的阶段交付输入计划，不能交付伪造谱或带隙。

UPF 公开来源记录：cndaqiang/ONCVPSP_LDA，commit `8305870fe4d064f864ef431783cf11aa7482b842`，`sg15_PZ_3.3.1`。文件含 D. R. Hamann ONCVPSP 3.3.1 引用请求及未指定版本的 GNU GPL 文字，另有 SG15 CC BY-SA 4.0 来源语境；没有据此擅自认定全部文件再分发权。各 manifest 给出可定位的公开 URL 和哈希，用户自行合法取得；元数据不保证可转移性或无 ghost state。

排错：scalar 赝势不能凭 ISPIN4变为 SOC；混错 FR/SR 或价电子改变必须独立重算并重新验证；缺运行结果时停在 input-only，不用别的材料结果代替。


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
