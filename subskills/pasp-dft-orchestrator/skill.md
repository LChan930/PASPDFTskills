# 原生 DFT 工作流控制器

先读取用户实际提供的文件与目标，区分准备输入、运行、诊断和已有结果分析。只按当前阶段加载资料。文件名或目录名不能代替内容识别；MD 不等于有效哈密顿量动力学，TB.bands 也不证明当前模型是紧束缚。

| 用户目标 | 本地指令 |
| --- | --- |
| 普通 PW SCF、固定密度路径能带、密度和费米能交接 | [打开工作流](../workflow-pw-scf-bands/skill.md) |
| ISPIN=2 磁性、AFM NiO、DFT+U 及相应能带 | [打开工作流](../workflow-pw-spin-plus-u/skill.md) |
| ISPIN=4、非共线与有/无 SOC 对照 | [打开工作流](../workflow-pw-soc/skill.md) |
| 固定晶胞离子弛豫、BaTiO3 极性构型 | [打开工作流](../workflow-pw-relax/skill.md) |
| PWRS、零/有限磁通、磁边界及运行选项 | [打开工作流](../workflow-pwrs-magnetic/skill.md) |
| 原生 DFT.LMD 的 NVE/NVT/NPH/NPT | [打开工作流](../workflow-pw-md/skill.md) |
| 已有日志、固定晶胞离子弛豫、能级、能带绘图、DOS、MD 结果分析 | [打开工作流](../workflow-output-analysis/skill.md) |

选择最直接的工作流；交叉任务先定位主阶段，再补充必要参考。已由用户确定的任务不重复询问许可。材料、磁序、赝势、计算类型等关键物理事实缺失时，只询问阻碍当前阶段的问题；已有授权范围内的整理和检查继续进行。

## 当前阶段与交接

各教程的状态机负责具体步骤。准备输入时检查主文件、全部 include、真实结构、物种顺序与赝势依赖。候选输入与实际运行结果分开，不复制旧输出作为新运行的证据。README/PROGRESS 只记录实际阶段、参数选择、输入来源、缺项和下一步，不能凭目录存在提升状态。

生成最小输入：保留结构 include、必需块和有意设置的非默认项。参数默认及覆盖关系只从 [参数索引](../../knowledge/reference/params/INDEX.md) 查询；不把参考表全部复制成模板。SCF 和能带分别安排资源，不为凑池数改变网格或对称性。

## 执行与输出

只使用用户实际已知的启动方式、可执行文件和调度环境，不猜测版本查询参数、探测模式或 PASP 命令行开关。执行、提交和覆盖操作按用户授权进行，保留结果与必要备份。

输出按内容识别，没有固定日志后缀；多份候选日志按输入、时间和初态配对，不按扩展名推断。报告默认英语，可选简体/繁体中文。分析辅助脚本位于 `knowledge/scripts/`，先查看对应 `--help`。完成标记、退出码、电子收敛、数值精度和物理正确性分别报告。

电荷密度与电流密度绘图属于已有输出分析路线。使用 [场绘图参考](../../knowledge/reference/topics/field-plotting.md) 和 `knowledge/scripts/plot_fields.py`，核对原生网格顺序、外部晶胞、切片/投影及单位；缺失场文件不生成替代数据。

能带图默认 eV，允许 Hartree 或用户指定的受支持单位。图内只保留材料/方法标题、坐标、路径与必要图例；收敛状态、缺失自旋信息等写在图外报告/JSON。参见 [绘图规范](../../knowledge/reference/topics/band-plotting.md)。

有独立只读核查需要且平台允许委派时，提供文件、问题、范围和交付格式，使用 [核查契约](../pasp-dft-verifier/skill.md)。核查不替代主控制器的科学判断，也不制造额外的重复确认流程。

## 包内自动化优先

准备或检查 PW/PWRS 输入时，先读 [输入审计契约](../../knowledge/reference/topics/input-audit.md)，运行实际根目录的 `knowledge/scripts/audit_inputs.py`；使用确切 FDF 或运行目录，按已知分配传 `--ranks`，只在有全局约化 k 点证据时传 `--irreducible-kpoints`。解释 ERROR/WARN/UNKNOWN，默认与条件覆盖不是物理推荐，静态通过不晋级为运行/收敛通过。

已有固定晶胞离子弛豫日志走 [输出分析](../workflow-output-analysis/skill.md)，同一弛豫任务运行后的核对走 [弛豫](../workflow-pw-relax/skill.md) 的 S6–S7。两处使用包内 `knowledge/scripts/analyze_relax.py`，按证据报告离子终止、进程完成、电子状态与阈值诊断。接口和单位见 [弛豫分析](../../knowledge/reference/topics/relaxation-analysis.md)。

已有 MD 轨迹走 [输出分析](../workflow-output-analysis/skill.md) 或 [MD](../workflow-pw-md/skill.md)，执行包内 `knowledge/scripts/analyze_md.py`，可附匹配 `--input`、`--log` 及明确的 fs 统计窗。逐帧检查和统计交给确定性工具；ensemble 守恒量、平衡及数值收敛由原始证据解释。不临时重写相同解析器，也不要求用户持有源码或研讨会私有脚本。
