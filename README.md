# pasp_DFT 使用说明

`pasp-dft` 是面向原生 PW/PWRS DFT 的自包含技能包，显示名为 **pasp_DFT**，规范调用名为 **`$pasp-dft`**。它帮助准备和检查输入、理解计算阶段，以及分析用户已有的日志、能级、能带、DOS、MD 和电荷/电流场。LCAO、有效哈密顿量及其他模型使用各自的技能。

计算指导以用户合法持有的 `PASP.x`、配套发行资料、输入、UPF 赝势和实际结果为依据；离线分析已有输出时不需要运行 `PASP.x`。包内知识是兼容性快照，不是对所有 PASP 发行版本的功能保证。

## 1. 安装、发现与调用

将**完整的 `pasp-dft/` 目录**复制到目标工具支持的技能发现位置。项目安装通常为 `<project>/.agents/skills/pasp-dft/`；保留 `SKILL.md`、`VERSION`、`agents/`、`subskills/` 与 `knowledge/` 的层级。若平台使用其他发现目录，可按该平台规则配置同一完整包或其链接。不要只复制入口，不要假定本包包含独立安装脚本、平台 agent 注册文件或自动创建的 Claude 链接。

重新载入平台的技能列表，确认规范名 `pasp-dft`；界面可能显示 `pasp_DFT`。例如：

```text
使用 $pasp-dft，检查这个 PW SCF 输入是否具备继续做路径能带的条件。
使用 $pasp-dft，解释我指定的 stdout 文件，报告用简体中文。
使用 $pasp-dft，绘制这份原生电荷数据，说明切片与整胞积分的区别。
```

本地 `subskills/*/skill.md` 是按需读取的指令文件，不是需要分别注册的技能。不要用 `pasp-dft:workflow-pw-scf-bands` 这样的冒号式调用。版本查询读取本包 [VERSION](VERSION)，不要把技能版本当作 `PASP.x` 版本。

### 路径约定

技能根目录是实际加载的顶层 `SKILL.md` 所在目录，入口为链接时沿链接解析到实际资源包。裸 `knowledge/...` 和 `subskills/...` 相对技能根目录；Markdown 链接、显式 `./` 与 `../` 相对当前文档。用户的输入、运行目录和报告仍属于用户工作区。

下文 shell 示例使用 `PASP_DFT_ROOT` 表示该根目录的绝对路径。Bash 中可从**已安装的项目根目录**初始化一次：

```bash
PASP_DFT_ROOT="$(cd .agents/skills/pasp-dft && pwd -P)"
```

之后可在任意用户计算目录执行脚本。若当前目录不是安装项目根目录，直接把变量设为实际解析出的绝对根目录；不要创建根目录 `skills/` 别名来迁就示例。PowerShell 中同样使用实际绝对路径，例如：

```powershell
$PASP_DFT_ROOT = 'C:/path/to/project/.agents/skills/pasp-dft'
Get-Content "$PASP_DFT_ROOT/VERSION"
python -B "$PASP_DFT_ROOT/knowledge/scripts/analyze_outputs.py" --help
```

这些路径是部署示意，需要替换。脚本输入和输出的相对路径始终相对执行命令时的用户目录；无需切换进技能包，也不把结果写入包内。

## 2. 目录与职责

```text
pasp-dft/
├── README.md
├── DEVELOPMENT_GUIDE.md
├── SKILL.md
├── VERSION
├── agents/openai.yaml
├── subskills/
│   ├── pasp-dft-orchestrator/skill.md
│   ├── pasp-dft-reference/skill.md
│   ├── pasp-dft-verifier/skill.md
│   └── workflow-*/skill.md           # 七条路线
└── knowledge/
    ├── workflows/                   # 主流程、状态机、检查单、历史笔记
    ├── reference/
    │   ├── QUERY_GUIDE.md
    │   ├── STRUCTURE.md
    │   ├── topics/
    │   ├── files/
    │   ├── params/
    │   ├── modules/
    │   └── toc/
    ├── templates/                   # 24 组真实输入与依赖清单
    └── scripts/
        ├── audit_inputs.py
        ├── analyze_md.py
        ├── analyze_outputs.py
        ├── analyze_eigenvalues.py
        ├── plot_bands.py
        └── plot_fields.py
```

| 层 | 负责的内容 |
| --- | --- |
| [入口](SKILL.md) | 判断 workflow、reference 或混合问题，读取最小相关资料 |
| [控制器](subskills/pasp-dft-orchestrator/skill.md) | 选择路线与阶段，组织输入、运行或结果交接 |
| [参考查询](subskills/pasp-dft-reference/skill.md) | 精确字段、单位、默认值、条件覆盖及文件格式 |
| [只读核查](subskills/pasp-dft-verifier/skill.md) | 有界事实收集，提供证据、缺项与局部结论；不选择科学参数或提交计算 |
| [模板](knowledge/templates/README.md) | 输入起点、include 闭包及外部/上游依赖；不代表本次计算结果 |

工作流的 `*_state_machine.md` 管阶段转换，`*_user_checklist.md` 用于交接，`*_run_notes.md` 记录历史观察。历史数值不能当作当前用户目录已经产生的结果。维护规则见 [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)。

## 3. 七条工作流

| 目标 | 本地路线 | 详细流程 |
| --- | --- | --- |
| 普通 PW SCF、固定密度路径能带与 SCF 参考交接 | [PW SCF/bands](subskills/workflow-pw-scf-bands/skill.md) | [BaTiO3](knowledge/workflows/pw_scf_bands.md) |
| 共线磁性、AFM、DFT+U 与相应能带 | [磁性/+U](subskills/workflow-pw-spin-plus-u/skill.md) | [NiO](knowledge/workflows/pw_spin_plus_u.md) |
| 非共线与有/无 SOC 对照 | [SOC](subskills/workflow-pw-soc/skill.md) | [Bi2Se3](knowledge/workflows/pw_soc.md) |
| 固定晶胞离子弛豫 | [弛豫](subskills/workflow-pw-relax/skill.md) | [BaTiO3 极性构型](knowledge/workflows/pw_relax.md) |
| PWRS、零/有限磁通和磁边界 | [PWRS 磁场](subskills/workflow-pwrs-magnetic/skill.md) | [Graphene](knowledge/workflows/pwrs_magnetic.md) |
| 原生 `DFT.LMD`，NVE/NVT/NPH/NPT 的适用分支 | [原生 MD](subskills/workflow-pw-md/skill.md) | [Si 七组 MD](knowledge/workflows/pw_md.md) |
| 已有日志、能级、能带、DOS、MD、电荷/电流场 | [输出分析](subskills/workflow-output-analysis/skill.md) | [分析流程](knowledge/workflows/output_analysis.md) |

“怎么开始、下一步是什么、这一步改哪些设置”先走 workflow；“某个键的含义、语法、默认或文件格式”先走 reference。混合问题先确定阶段，再查该阶段需要的精确资料。基础文件说明和入门概念属于 reference，不额外增加一条工作流。

参考入口为 [查询指南](knowledge/reference/QUERY_GUIDE.md) 与 [结构说明](knowledge/reference/STRUCTURE.md)：参数看 [params/INDEX.md](knowledge/reference/params/INDEX.md)，文件看 [files/INDEX.md](knowledge/reference/files/INDEX.md)，组合问题看 `topics/`，PW/PWRS 方法范围看 `modules/`。

## 4. 使用前准备与模板边界

准备计算输入时，需要真实结构、物种顺序、每物种匹配的 UPF、计算目标、用户已有的启动方式及必要上游文件。`PASP.x` 与 MPI/调度环境按用户已有部署使用；本包不要求源码、私有仓库、Git、编译器，也不要求运行未获发行资料支持的版本探测命令。

[24 组模板](knowledge/templates/README.md) 覆盖 BaTiO3、NiO、Bi2Se3、Graphene 与 Si MD。每组有实际 `lattice_model.fdf`、`siesta.ANI`、README 和 `dependency-manifest.json`。它们是从输入整理的参考起点，未在本次文档整理中执行 PASP；UPF、密度/重启参考、+U 占据及历史输出没有随模板提供。请按各 manifest 补齐依赖，核对后再称为可运行输入。

最小输入保留真实结构/include、必需块与有意设置的非默认项。默认值不是精度推荐；条件默认或覆盖规则须查 [输入生成](knowledge/reference/topics/input-generation.md) 和参数表。资源安排使用 [实际 k 点与 band 池约束](knowledge/reference/topics/kpoint-band-parallelism.md)，SCF 与能带分别配置，不为池数整除改变物理采样或对称性。

路径能带需要匹配、被接受的 SCF 密度与参考元数据，典型为原字节的 `CHGCAR` 和 `CHGCAR.restart`；+U 还可能需要匹配的 `PLUS_U_NS`。只有密度文件、有限能量或正常退出都不足以建立合格交接。详见 [PW 参考](knowledge/reference/modules/pw.md)。

## 5. 离线脚本与依赖

| 脚本 | 用途 | 所需环境 |
| --- | --- | --- |
| [audit_inputs.py](knowledge/scripts/audit_inputs.py) | include/块、结构/UPF 依赖、默认/条件设置与并行池静态审计 | Python 3.10+，仅标准库；保留包内参数表 |
| [analyze_md.py](knowledge/scripts/analyze_md.py) | 原生逐帧完整性、时间/步数、统计窗与日志一致性 | Python 3.10+，分析仅标准库 |
| [analyze_outputs.py](knowledge/scripts/analyze_outputs.py) | 日志证据摘要、阶段状态、文件清点 | Python 3.10+，仅标准库 |
| [analyze_eigenvalues.py](knowledge/scripts/analyze_eigenvalues.py) | 原生 bands 或 stdout `EIGENVAL` 表、条件采样带边 | Python 3.10+、NumPy；保留同目录 `plot_bands.py` |
| [plot_bands.py](knowledge/scripts/plot_bands.py) | 原生能带 PNG/PDF/SVG 与 JSON | Python 3.10+、NumPy、Matplotlib |
| [plot_fields.py](knowledge/scripts/plot_fields.py) | 原生电荷/电流网格、切片/积分、图与证据报告 | Python 3.10+、NumPy、Matplotlib |

仅阅读文档和准备输入无需安装绘图库。分析使用现有合适环境；这些脚本不启动 PASP 或 MPI。先查看相应 `--help`，不要把 Python 辅助脚本选项传给 `PASP.x`。

### 输入静态审计

六个公开 CLI 均从实际技能根目录调用。先按当前版本的 `--help` 选择选项；下面的输入路径由用户替换，输出必须是尚不存在的新文件。

```bash
python -B "$PASP_DFT_ROOT/knowledge/scripts/audit_inputs.py" --help
python -B "$PASP_DFT_ROOT/knowledge/scripts/audit_inputs.py" lattice_model.fdf --lang zh-Hans --format json --output input-audit.json
python -B "$PASP_DFT_ROOT/knowledge/scripts/audit_inputs.py" run-directory --ranks 8 --irreducible-kpoints 4 --format markdown --output input-audit.md
```

最后一行的 ranks 与 irreducible-kpoints 仅演示接口，必须替换成实际分配的进程数与本阶段已证实的**全局约化 k 点数**。没有点数证据就省略该选项，不能用 SCF 网格乘积冒充 IBZ 点数。目录输入依实际 CLI 的主文件选择规则解析；多候选时指定确切 FDF。

审计递归读取 include，检查块/重复与未知键、结构/物种/UPF 和阶段依赖，并基于包内有限参数登记表记录显式设置、参考默认及可证明的条件值。未知键可能是新发行版扩展；缺重启/UPF 是缺少证据，不能伪造兼容性或已运行结论。退出 0 表示审计完成，仍需读 ERROR/WARN/UNKNOWN；退出 2 表示 CLI/输入不可读或报告写入失败。默认值不是物理推荐。完整范围见 [输入审计](knowledge/reference/topics/input-audit.md)。

### 原生 MD 自动分析

```bash
python -B "$PASP_DFT_ROOT/knowledge/scripts/analyze_md.py" --help
python -B "$PASP_DFT_ROOT/knowledge/scripts/analyze_md.py" output_MD.dat --input lattice_model.fdf --log stdout.answer --lang zh-Hans --format json --output md-report.json
python -B "$PASP_DFT_ROOT/knowledge/scripts/analyze_md.py" output_MD.dat --input lattice_model.fdf --window-start-fs 2000 --window-end-fs 4000 --format markdown --output md-window.md
```

轨迹是实际原生格式，文件名不限。`--input` 与 `--log` 可省略；没有输入/日志时相关 requested/read-back、电子停止证据保留 unknown。窗口以 fs 为单位，示例 2000–4000 fs 只适用于覆盖该区间的轨迹，不自动代表平衡段。工具检查完整帧、有限值、原子标识、步/时间连续性与可对照的请求长度，统计能量、温度及已支持的晶胞/压力信息；具体字段和限制见 [MD 分析](knowledge/reference/topics/md-analysis.md)。

`analyze_md.py` 退出 1 表示确定的帧/长度/日志或文件错误，CLI 参数错误为 2；退出 0 仍不认证物理收敛。NVT/NPT 不套用 NVE 守恒判据，扩展焓/能量定义、统计窗、热平衡、时间步和截断收敛仍须解释。日志摘要不能替代逐帧分析，两份报告可以互补。

两个新工具默认英文，支持 `--lang en|zh-Hans|zh-Hant`、`--format markdown|json` 与拒绝覆盖的 `--output`；省略输出文件则向标准输出写报告。它们不要求源码、私有脚本或 PASP 执行。

### 日志、能级与能带

下面假设 `PASP_DFT_ROOT` 已解析，当前目录是用户选定的结果目录。`stdout.answer`、`spectrum` 是用户实际文件名的示例；文件名可以自定义或无扩展名。为新报告预先创建父目录；示例输出名均应尚不存在。

```bash
python -B "$PASP_DFT_ROOT/knowledge/scripts/analyze_outputs.py" --help
python -B "$PASP_DFT_ROOT/knowledge/scripts/analyze_outputs.py" stdout.answer --lang zh-Hans --output log-report.md
python -B "$PASP_DFT_ROOT/knowledge/scripts/analyze_eigenvalues.py" spectrum --input-kind bands --unit Ha --lang zh-Hant --output levels-report.md
python -B "$PASP_DFT_ROOT/knowledge/scripts/plot_bands.py" spectrum --output-dir figures --name bands-ev --unit eV --title "Electronic band structure"
```

目录日志扫描默认不递归，需分析子目录时显式使用 `--recursive`。报告默认英语，输入/MD/日志/能级/场报告可选 `--lang en`、`zh-Hans`、`zh-Hant`；JSON 键、状态码和原始证据保持稳定。**`plot_bands.py` 没有 `--lang`**，科学图内使用清楚的标题、坐标和必要图例，收敛与来源限制写在图外报告和 JSON。

能带/能级默认 eV，也支持 meV、Ha/Hartree、Ry/Rydberg；自定义单位须同时给正有限 `--units-per-hartree`。`--reference-ha`、`--ef-hartree` 始终使用 Hartree。原生 bands 的绝对能量按文件头参考只减一次；已移位的 `plot.dat` 不能再减一次，也不是此原生读取器的完整输入。

没有已证实的占据带数时，能级示例仅做参考能量两侧诊断；`--occupied-bands` 必须来自实际填充依据。路径采样间隙不能直接称为全布里渊区基本带隙，单一原生能级列表也不能自行拆为上下自旋。详见 [日志分析](knowledge/reference/topics/output-analysis.md)、[能级分析](knowledge/reference/topics/eigenvalue-analysis.md) 和 [能带绘图](knowledge/reference/topics/band-plotting.md)。

### 电荷与电流场

原生 `CHGCAR`/`CRTCAR` 不是 VASP 格式；场文件不含完整晶胞与原子信息。需提供配对 restart 或显式 `--cell-bohr`，并核对格式、网格、分量、单位与生产阶段。示例显式选择显示语义：

```bash
python -B "$PASP_DFT_ROOT/knowledge/scripts/plot_fields.py" CHGCAR --kind charge --restart CHGCAR.restart --mode slice --axis 3 --fraction 0 --output-dir figures --name charge-plane --lang zh-Hans
python -B "$PASP_DFT_ROOT/knowledge/scripts/plot_fields.py" CHGCAR --kind charge --restart CHGCAR.restart --mode project --axis 3 --output-dir figures --name charge-sheet
python -B "$PASP_DFT_ROOT/knowledge/scripts/plot_fields.py" CRTCAR --kind current --restart CHGCAR.restart --mode project --axis 3 --stride 2 --output-dir figures --name current-sheet --lang zh-Hant
```

`slice` 是指定分数坐标处单平面的**体密度**，默认电荷单位电子/Å³；它不是有限厚度层的积分。`project` 是沿省略分数轴跨完整晶胞的柱积分，默认电荷单位电子/Å²，既不是平均值，也不是另一种体密度。单层体系可据实际几何讨论整胞的层积分；多层体系的整胞结果包含所有层，不能直接标成某一单层。当前脚本没有有限层厚窗口积分。

切片平面应由真实原子位置与几何决定，分数坐标 `0.5` 可能落在真空。斜晶胞的分数柱积分不一定等于沿法线的正交投影。`--density-unit bohr` 改变电荷密度长度单位，`--length-unit` 独立改变坐标单位；电流保持已知原子单位。多通道电荷须显式选择 `--channel` 并另证物理意义；当前电流读取仅支持 `ISPIN=1`。

场绘图默认导出 PNG/PDF/SVG、NPZ、JSON 与 Markdown；图中只放科学内容，原始极值、积分、哈希、几何与限制在图外记录。缺失电流不能用零场补造，局域电流图不直接证明输运或连续性。完整格式、单位和积分规则见 [场绘图参考](knowledge/reference/topics/field-plotting.md)、[CHGCAR](knowledge/reference/files/CHGCAR.md) 与 [CRTCAR](knowledge/reference/files/CRTCAR.md)。

## 6. 当前证据与限制

正常结束、脚本退出 0、电子停止准则、数值参数收敛及物理正确性分别判断。`MAXITER` 留下的有限谱或力仍须标为未收敛。分析脚本成功只证明相应文件被读取，不证明原计算成功；来源不明、旧格式和截断日志应保留未知项。详见 [验证与报告](knowledge/reference/topics/validation.md)。

本包没有通用原生 DOS/PDOS 读取绘图器，也没有已验证的原生 DOS 输出模板；[DOS 参考](knowledge/reference/topics/dos.md) 用于核对格式、展宽、单位和归一，不能把路径点等权当作体相 DOS 积分。日志摘要也不能替代 [MD 帧与守恒量检查](knowledge/reference/topics/md-analysis.md)。

输入模板、解析测试与历史案例分别说明各自覆盖范围。未知版本支持、缺失 UPF/上游产物、未检查的占据/自旋、未验证的精度和缺失场数据都应写在随附报告中。技能包不提供源码、未公开算法说明或二进制探测要求；结果解释仍以用户当前文件和可获得的发行证据为准。
