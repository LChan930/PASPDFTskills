# NiO：AFM 与 +U 分支

先用[状态机](pw_spin_plus_u_state_machine.md)定位当前阶段，再按本课对应小节操作。[检查单](pw_spin_plus_u_user_checklist.md)用于实际交接，[历史笔记](pw_spin_plus_u_run_notes.md)只解释已有证据边界。

## 可复制的真实文件树

每个下列末级目录均包含 `lattice_model.fdf`、实际引用的 `siesta.ANI`、`dependency-manifest.json` 和阶段README。UPF不附；没有密度、历史输出或预制结果。

- [nio/01_LDA/01_scf](../templates/nio/01_LDA/01_scf/README.md)：4原子，物种 Ni/O；FDF/引用结构/依赖清单齐备，UPF待提供。
- [nio/01_LDA/02_bands](../templates/nio/01_LDA/02_bands/README.md)：4原子，物种 Ni/O；FDF/引用结构/依赖清单齐备，UPF待提供。
- [nio/02_LDA_U/01_scf](../templates/nio/02_LDA_U/01_scf/README.md)：4原子，物种 Ni/O；FDF/引用结构/依赖清单齐备，UPF待提供。
- [nio/02_LDA_U/02_bands](../templates/nio/02_LDA_U/02_bands/README.md)：4原子，物种 Ni/O；FDF/引用结构/依赖清单齐备，UPF待提供。

## 证据等级

本包标记为 `input-derived / not-runtime-tested`：输入与实际引用结构来自现有案例，构建时只作静态闭包和哈希检查，没有启动 PASP 或 MPI。目录中已有历史输出不能自动升级本模板的证据等级。历史测试、当前输入静态检查、本次实际运行三者分别记录。所有 UPF 因再分发权限未明确而不随包分发，必须由用户合法提供；没有 UPF 时不具备运行完整性。

## 学习目标与四阶段目录

四原子 AFM-II NiO 的结构顺序是 Ni、Ni、O、O；物种顺序 Ni/O。两条分支各自完成 SCF → bands：`01_LDA` 与 `02_LDA_U`。比较同几何、同赝势、同积分条件下 +U 对电子结构的影响；本课不提供经过精度收敛的材料数值结论。

### 第一阶段：LDA AFM 候选与 SCF

进入 `nio/01_LDA/01_scf`。4×8×8 是完整网格 256 点，源注释约化39点不替代本次日志。保留 `DFT.ISPIN 2` 与逐原子四行初始磁矩：

```text
DFT.ISPIN 2
%block DFT.MAGMOM
0 0 2
0 0 -2
0 0 0
0 0 0
%endblock DFT.MAGMOM
```

±2 是两个 Ni 的初始值，不是约束或最后局域磁矩。先把坐标行与磁矩行对齐；总磁矩接近零不能单独证明 AFM 局域态。35 Ha、EDIFF1e-7、NELM200、mixing.method3 是案例选择。原 LDA 输入含 `DFT.nv_pool 1`，本包保留，不宣称它等同 `nb_pool`；核对发行版，未写 `nb_pool` 时按参考默认1处理。SCF 通过后记录自旋、密度、磁序证据。

### 第二阶段：LDA bands

进入匹配 `nio/01_LDA/02_bands`，只移交该 LDA SCF 的合法密度/参考配对。保留 ISPIN2 和同一磁矩顺序。模板 NBAND40 已包含该表示的总态数，不再机械乘二。教学路径来自当前实际晶胞端点的选取与连接，不是完整推荐磁性高对称路径。检查实际200路径点、参考恢复和谱迭代状态后再画图；原生单 writer-channel 不能自行分成 up/down 曲线。

### 第三阶段：独立 +U SCF

进入 `nio/02_LDA_U/01_scf`，保留相同结构/UPF/磁序，加入已存在的实际定义：

```text
DFT.n_manifolds_plus_U 1
%block DFT_plus_U
Ni 3d 0.2
%endblock DFT_plus_U
```

省略的 `DFT.plusU_type` 在本参考默认1；这里 0.2 是裸 Hartree 的 Ueff，约5.4423 eV，不是0.2 eV。省略 IDs 表示全部 Ni 原子，不是任意全局原子编号。Ueff 和投影壳是此案例物理选择，不能复制为所有磁性材料默认。不要直接用 LDA 密度声称得到 +U 收敛态；如果启动复用须明确说明新分支重求解并核对兼容。

### 第四阶段：+U bands 与比较

`nio/02_LDA_U/02_bands` 保留同一 Ueff/壳/站点定义。除合法 `CHGCAR`/`.restart` 配对，还需由匹配 +U SCF 移交适用的 `PLUS_U_NS` 占据辅助数据；密度不能重建这些占据，维数相同也不能证明来源相同。四个阶段分别记录运行状态。通过后以一致能量参考约定和路径比较两分支的图与采样谱特征；不要把 +U 文件存在当作 +U 已激活、收敛或材料验证。

排错：站点磁矩顺序不对先回结构；+U 行数、单位或物种选择不对先修候选定义；缺匹配 PLUS_U_NS 回该分支 SCF；不要把另一分支产物重命名凑齐。+U 与 PWRS/SCF_ONLY 等组合不由本例支持。


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
