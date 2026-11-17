# Si：七组原生 PW 分子动力学

先用[状态机](pw_md_state_machine.md)定位当前阶段，再按本课对应小节操作。[检查单](pw_md_user_checklist.md)用于实际交接，[历史笔记](pw_md_run_notes.md)只解释已有证据边界。

## 可复制的真实文件树

每个下列末级目录均包含 `lattice_model.fdf`、实际引用的 `siesta.ANI`、`dependency-manifest.json` 和阶段README。UPF不附；没有密度、历史输出或预制结果。

- [si_md/NVE](../templates/si_md/NVE/README.md)：2原子，物种 Si；FDF/引用结构/依赖清单齐备，UPF待提供。
- [si_md/NVT/thermo_1](../templates/si_md/NVT/thermo_1/README.md)：64原子，物种 Si；FDF/引用结构/依赖清单齐备，UPF待提供。
- [si_md/NVT/thermo_2](../templates/si_md/NVT/thermo_2/README.md)：64原子，物种 Si；FDF/引用结构/依赖清单齐备，UPF待提供。
- [si_md/NVT/thermo_3](../templates/si_md/NVT/thermo_3/README.md)：64原子，物种 Si；FDF/引用结构/依赖清单齐备，UPF待提供。
- [si_md/NVT/thermo_4](../templates/si_md/NVT/thermo_4/README.md)：64原子，物种 Si；FDF/引用结构/依赖清单齐备，UPF待提供。
- [si_md/NPH](../templates/si_md/NPH/README.md)：2原子，物种 Si；FDF/引用结构/依赖清单齐备，UPF待提供。
- [si_md/NPT](../templates/si_md/NPT/README.md)：2原子，物种 Si；FDF/引用结构/依赖清单齐备，UPF待提供。

## 证据等级

本包标记为 `input-derived / not-runtime-tested`：输入与实际引用结构来自现有案例，构建时只作静态闭包和哈希检查，没有启动 PASP 或 MPI。目录中已有历史输出不能自动升级本模板的证据等级。历史测试、当前输入静态检查、本次实际运行三者分别记录。所有 UPF 因再分发权限未明确而不随包分发，必须由用户合法提供；没有 UPF 时不具备运行完整性。

## 学习目标：从真实 Si 初态到轨迹证据

本课是原生 `DFT.LMD T` 的PW-MD，使用各末级目录真正引用的 `siesta.ANI` 与单物种 `Si.pz-vbc.UPF`。包含NVE、NVT四种恒温器、NPH、NPT共七组；不属于上游有效Hamiltonian的MD/SLD，也不借用其输入。NVE/NPH/NPT为2原子，四组NVT为64原子，以实际结构文件为准。

### 第一阶段：识别初态与电子设置

先选一个末级目录，读原子数、晶胞与是否有显式初始速度。保留真实结构；NVE的位移初态、零初速会产生运动，不能把零初温误作“原子永远不动”。Gamma-only为默认网格，池默认1/1；建议先用1 MPI rank、1线程的用户已知启动方式验证。Gamma只有1实际k点，不能把40k池带入；64原子NVT的最佳并行需要真实测量，不能从网格或带数整除编造。

所有当前模板ENCUT20 Ha；NVE/NPH/NPT保留ALGO6，NVT省略为参考默认ALGO4。四个NVT从历史2 Ha统一改为20 Ha会改变成本与数值精度，**新输入尚未运行或验证精度**。显式质量28.086 amu不能删：参考默认1 amu不是硅元素质量。若需要独立静态电子预检，在新候选目录仅关闭LMD且保持结构/电子参数，记录这是另一个SCF任务；不把其通过等同于动态每一步通过。

### 第二阶段：选择和理解七个演示

| 目录 | 明确的请求 | 步数 / dt | 学习重点 |
| --- | --- | --- | --- |
| NVE | 2原子，零初温、位移初态，solver1 | 400 / 0.5fs | 已建立NVE能量定义后检查漂移；thermostat1请求的阻尼被ensemble1置零 |
| NVT/thermo_1 | 64原子，目标80K、初速20K，Langevin_Gamma0.1 | 4000 / 1fs | Gamma是质量阻尼约定，不能直接写成1/fs |
| NVT/thermo_2 | 64原子，目标80K、初速20K，Andersen_Prob0.02/fs | 4000 / 1fs | 当前带PW_MD前缀；历史无前缀未生效，旧运行用默认0.1不能当新结果 |
| NVT/thermo_3 | 64原子，目标80K、初速20K，SMASS20 | 4000 / 1fs | 保留惯性参数，发行版单位待核对；旧截断样本已被完整2Ha Nose档案替代；当前20Ha输入未运行验证 |
| NVT/thermo_4 | 64原子，目标80K、初速20K，tolp5K/nraise80 | 4000 / 1fs | 速度重标度，检查实际温度窗口与生效周期 |
| NPH | 2原子，44GPa，PMASS400amu，solver2/barostat1 | 400 / 1fs | 近零温初态；普通Ep+Ek不自动等于守恒扩展焓 |
| NPT | 2原子，40GPa，温度1e-8K，tolp1e-8K，nraise40 | 4000 / 1fs | 近零温高压演示，不是有限温度基准 |

这些是案例请求，不能把400/4000步直接叫“短且足够”的生产长度。要做短演示时由已有授权方案确定较少nstep，保留dt/物理条件并记录新输入哈希；不悄悄缩短原模板。NVT有效solver1；NPH/NPT有效solver2、thermostat4、barostat1。requested、PASP.used_info read-back、runtime-effective三栏分开记录，回显可能早于ensemble覆盖。

### 第三阶段：执行与逐步电子门槛

运行每个选中末级目录时用新日志，不复制历史轨迹/密度/锁文件。扫描完整stdout/stderr，特别是 `PW_MD: self-consistent iteration failed`；按唯一步数去重和MPI重复消息分别计数。`LOBPCG error! Renormal` 单列诊断，不自动与SCF失败画等号。检查每一步电子求解，不因最后打印结束就忽略中间失败；旧版没有现代marker时结合实际迭代区块、NELM与终止上下文判断，缺证据标unknown。

历史thermo_3曾4000步请求只见step0–400，146个唯一SCF失败步、exit9，且日志与轨迹step0有来源不一致问题。这些是历史故障线索，不是本包新20Ha输入的结果；后半段有轨迹不能恢复其科学有效性。

### 第四阶段：按原生格式读取轨迹

对实际 `output_MD.dat` 和/或原生轨迹内容识别 `Step/Time/Ep/Ek/Etot/Temp/H/fs`、位置、速度；变量胞另核对每帧晶格与应力及单位，不能假定固定列号。通常nstep=N更新产生step0…N共N+1帧：400应核对401帧，4000应核对4001帧，并检查时间范围、帧连续性、原子数、每帧行数和有限数值。完成标记与帧完整性是独立证据，任一缺失都不能假称完整。

NVE只在能量定义与完整控制确定后计算漂移；NVT/NPT存在热浴/压浴交换，不套NVE漂移验收。NPH需明确扩展焓定义，近零温轨迹也不是热平衡。变量胞Ep可能含压力体积记账，不能直接叫孤立电子基态能量。写明实际统计区间、时长、漂移单位、采样数；后半段窗口不自动认证平衡。

### 第五阶段：交付与后续

交付输入/include/UPF哈希、requested/read-back/effective表、进程与每步SCF状态、轨迹唯一帧数和范围、ensemble适用观测量、统计窗口、故障与下一步。模板仅输入派生，七套都没有附新的运行输出。温度、压力、dt、截断和系统大小的生产收敛要另行制定；禁止从教学演示声称生产精度。


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


## 完整历史档案更新（0.2.2）

完整替换档案：历史 2 Ha、64 Si、Nose 恒温器 3（SMASS=20），1 fs × 4000 步；4001 完整帧，0–4 ps。全部日志步与轨迹一致，正常结束，无 SCF 失败。2–4 ps 温度 79.91318 ± 45.62510 K（总体标准差）；全程 80.02175 ± 46.93557 K。ZIP SHA256: 0f44c3e71a98af2f23dd2f26300f9ebe40d0cc7cf4f3170aa22e58729a6cdf59。旧截断/日志不匹配样本的失败审计保留为 superseded original archive，不能套用于本档案。当前模板为独立的 20 Ha 输入，状态仍 input-derived-not-runtime-tested；历史成功不证明代码故障修复或当前输入已经运行，也未建立 cutoff/dt 收敛或热平衡。

恒温器映射：1 Langevin、2 Andersen、3 Nose、4 速度重标度。档案只作历史证据，本技能不分发运行日志、轨迹或 UPF。

## 0.3.0 包内自动检查

准备运行时，使用 [输入审计](../reference/topics/input-audit.md) 对实际 FDF/目录进行 include、结构、UPF/重启依赖、参考默认和资源一致性检查；缺 IBZ 时不猜点数，不因默认 1/1 池声称性能最优。

已有轨迹时执行：

```bash
python -B "$PASP_DFT_ROOT/knowledge/scripts/analyze_md.py" output_MD.dat --input lattice_model.fdf --log stdout.answer --lang zh-Hans --format json --output md-report.json
```

以上路径由用户替换为匹配本次运行的实际文件。`--input`/`--log` 可省略，缺少时相关证据保留 unknown。统计窗口通过 `--window-start-fs`、`--window-end-fs` 显式给出；不能把后半程自动称作平衡。工具提供逐帧/连续性、请求长度、统计与日志一致性证据；ensemble 的能量/焓定义、温压采样、数值精度和热平衡仍按 [MD 分析](../reference/topics/md-analysis.md) 解释。
