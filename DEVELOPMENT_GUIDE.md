# pasp_DFT 维护指南

本文面向维护者，约定信息放置、路由扩展、输入依赖、分析证据与发布检查。用户安装与调用见 [README](README.md)，当前技能版本读取 [VERSION](VERSION)。保持原生 PW/PWRS 范围；LCAO 及其他模型的规则不复制到本包。

## 1. 信息归属与运行边界

| 位置 | 维护内容 | 避免放入的内容 |
| --- | --- | --- |
| [SKILL.md](SKILL.md) | 职责、根路径、workflow/reference/mixed 路由、支持范围 | 参数字典、长流程、材料设置 |
| [控制器](subskills/pasp-dft-orchestrator/skill.md) | 七条任务路线与跨阶段交接 | 每条路线的详细分支规则 |
| `subskills/workflow-*/skill.md` | 该路线的最小入口、状态机和知识加载顺序 | 重复长篇 reference |
| `knowledge/workflows/<name>.md` | 稳定输入/输出契约、阶段、可调项和检查点 | 某次运行的数值与现场路径 |
| `*_state_machine.md` / `*_user_checklist.md` | 阶段条件、当前可做动作、交接事实 | 未建立事实的“已完成”标记 |
| `*_run_notes.md` | 历史实例、已观察行为及验证范围 | 对当前用户目录的实时断言 |
| [reference](knowledge/reference/STRUCTURE.md) | 精确键、类型、单位、默认、条件与格式 | 未注明依据的外软件类推 |
| [templates](knowledge/templates/README.md) | 最小完整输入、依赖清单与派生说明 | UPF、旧输出或大量原始案例的无差别复制 |
| `knowledge/scripts/` | 确定性的离线解析与绘图接口 | PASP 内部功能的无依据替代 |

用户运行环境只有合法的 `PASP.x`、发行资料、输入、赝势与结果也应能使用本包。公共文档和接口不得要求私有仓库、源码路径、内部源文件/过程名、编译工具或实现模块。开发中校准出的稳定行为，应整理成用户可理解的输入/输出规则及兼容性范围。未公开的实空间选项只保留允许公开的调用条件，不命名或解释内部算法。

不增加必需的 Git 命令、编译流程、版本探测参数、dry-run 或未文档化的 PASP 开关。需要执行时沿用用户已知启动方式；技能加载和离线检查本身不是启动材料计算的指令。已有授权按上下文继续，不建立重复审批流程。

## 2. 路径、发现与平台层

资源根目录来自实际加载的顶层入口，入口为链接时解析到实际包。裸 `knowledge/...`、`subskills/...` 相对该根；Markdown 链接及 `./`、`../` 相对文档。输入、run 和报告相对用户工作区，不能依赖当前目录恰好是包根目录。

维护和示例中用已解析的绝对 `PASP_DFT_ROOT` 调用脚本，并对路径加引号；它只是示例变量，不是脚本要求的环境变量。保留同目录脚本依赖，例如能级分析读取同包的 `plot_bands.py`。不要通过创建额外 `skills/` 别名、切换到包内或把结果写入包内修补路径问题。

规范技能名为 `pasp-dft`，UI 显示名由 [agents/openai.yaml](agents/openai.yaml) 的 `pasp_DFT` 提供。`subskills/` 是本地指令，不使用冒号嵌套调用，也不假定它们被平台注册。只读核查的唯一包内契约为 [pasp-dft-verifier](subskills/pasp-dft-verifier/skill.md)；平台注册、工具权限与链接由实际部署处理，本包不能声称存在尚未提供的安装器或 wrapper。

## 3. 扩展 workflow 与 reference

新增任务路线前，先确认用户在问任务过程，而不是字段查询。新增或改造路线时同步检查：

1. `knowledge/workflows/<name>.md`：目标、适用问题、输入、阶段、输出与下游依赖。
2. 同前缀状态机、用户检查单；有历史观察时另放 run-notes。
3. `subskills/workflow-<name>/skill.md`：先定位状态，再按需读细节。
4. 控制器、入口支持范围和 README 路线表：只登记实际可达资源。
5. 所需 reference、模板及脚本：建立精确依赖和查询入口，避免复制全文。

每个关键阶段写清“可调整什么、控制什么、何时查 reference、改后检查什么”。阶段条件应与当前工作流实际风险相称；不从其他模型搬入无关层级、硬门禁或确认标志。只读核查汇报事实和未知项，不代替主控制器选物理参数、修改输入或提交计算。

新增参考按 [QUERY_GUIDE](knowledge/reference/QUERY_GUIDE.md) 放到 `topics/`、`files/`、`params/` 或 `modules/`，同步相关索引与调用链接。精确定义归 reference，流程只链接所需条目。没有资料的字段明确缺口；不要凭 VASP/QE 同名键、相邻模型或旧拼写猜测别名和语义。

历史记录应注明材料、输入来源、实际执行范围和结果限制。旧 run 中的成功、计时或数值只能支持该 run；不能因文件或目录存在便提升当前阶段。当前目录的结果核查以用户指定文件为主，不暗中用别的案例补成缺失数据。

## 4. 默认值、最小输入与依赖清单

字段的精确定义由 [参数索引](knowledge/reference/params/INDEX.md) 与 [输入生成](knowledge/reference/topics/input-generation.md) 维护。区分以下四类：

| 类型 | 记录方式 | 维护时的检查 |
| --- | --- | --- |
| 缺键默认 | 名称、类型、单位、适用版本范围 | 不把默认解释为材料精度推荐 |
| 条件默认 | 触发条件与依赖表达式 | 删除显式键后是否改变含义 |
| 强制覆盖 | 谁覆盖谁、何时发生 | 显式冲突不能按普通默认解释 |
| 组合限制 | 支持/拒绝的任务组合与证据 | 不把单项可读推广成组合可用 |

例如 `ENCUT_RHO` 缺省依赖已选 `ENCUT`；MD 部分默认依赖场、温度或系综。维护者应核对依赖键，而不是把默认表展平成无条件数值。包内快照与用户发行资料/实际回显不一致时保留差异，不能自动“修正”为快照。

新建最小输入保留真实结构或完整 include、必需块、物种/UPF 映射及有意的非默认设置。明确选择 DFT 模型；不批量展开无关 MD、场、滤波或响应参数，也不盲目删掉用户有意明确的默认项。修改前查字段的精确语法、单位、首个定义/重复键规则及当前阶段可调范围。

模板应能在没有外部示例目录时理解，并附 README 与 `dependency-manifest.json`。逐项区分：

- 随包输入与真实结构/include 闭包；
- 用户合法提供的每物种 UPF、身份/哈希与已知元数据；
- 上游生成的密度、参考元数据、波函数或 +U 占据；
- 环境启动资料与非必需辅助文件。

不得把缺少 UPF 的模板称为开箱可跑，或把原来的历史输出塞进模板充当新计算证据。输入基线、候选修改和 `runs/<run-id>/` 分开，README 说明上游来源、下游实际消费文件与当前缺项。阶段间只复制直接依赖并记录来源，不整包搬运无关旧输出。

## 5. 科学设置与资源安排

结构、赝势、XC、磁序、自旋/SOC、采样网格/路径、带数、展宽和收敛目标属于科学选择；MPI ranks 与池布局属于资源安排。不得为了满足机器规模而改变科学设置或降低精度。

按 [k 点/band 池参考](knowledge/reference/topics/kpoint-band-parallelism.md) 检查：

- `nk_pool` 同时整除 MPI ranks 与当前阶段实际生成、约化后的全局 k 点数；SCF 网格乘积不是默认的实际点数。
- 路径能带按 `BandLines` 实际展开总点数；SCF 和 bands 分别配置，不能照抄池数。
- `nb_pool` 整除 `Nproc/nk_pool`。普通 PW 适用求解流程允许不均匀带分配，不普遍要求带数整除 band 池数。
- `nk_pool*nb_pool` 不必等于 ranks；完整 PWRS 与 SCF_ONLY 保持单 band 池，其他特殊任务还有限制。
- 实际点数未知时保留 1/1 默认或省略其键，说明效率未知；不能发明探测模式或擅自启动计算取得点数。

关闭空间对称性不一定关闭时间反演约化。匹配日志的全局点数优先，不能用 root rank 的本地点数代替。初始化成功、整数分配合法与实际加速是不同证据；性能比较须同精度并记录 ranks、线程、硬件、池数、点数、带数和计时范围。

## 6. 重启与 SCF → bands 交接

[PW 参考](knowledge/reference/modules/pw.md) 与 [CHGCAR.restart](knowledge/reference/files/CHGCAR.restart.md) 负责格式和兼容条件。SCF 前驱须具有被接受的生产状态、匹配几何/自旋/电子数/UPF 与物理设置，保留密度和配对元数据的原始字节。元数据的密度长度和校验和不能替代完整物理兼容性检查。

当前快照中 `SCF_ONLY` 在常规交接文件写出前结束，不能作为快捷能带前驱；需要普通 SCF 密度时按参考设置整数 `LCHARG`。路径阶段保留 SCF 参考，不从路径重算体相费米能；只加 `RCHARG` 不能补齐缺失参考。+U 交接还需核对 `PLUS_U_NS` 的物种、站点、U/J 与关联子空间。

缺失、损坏、未知版本或混配的重启资料如实报告；不得编辑状态、重建参考或拿另一 run 的同名文件绕过问题。路径本征值准则、SCF 停止准则和参数收敛分别记录。

## 7. 日志、报告与绘图证据

### 文件身份和状态

日志可以任意文件名或无后缀。按用户明确路径和内容识别，多候选以输入、初态、输出关系和来源配对；目录、时间和后缀只是线索。保留 stdout/stderr 与后续失败，不能让早期成功掩盖最后的截断阶段。

[analyze_outputs.py](knowledge/scripts/analyze_outputs.py) 的退出 0 表示分析完成，不能解释为计算成功。正常结束、调度完成、SCF/路径准则、数值精度与物理结论分开写；`MAXITER`、数值失败、未知协议和缺失证据保留。通用日志摘要不保证 MD 每帧结构/速度/应力完整，也不解码全部原生产物。

### 语言、单位与能带

日志、能级与场报告提供英语（默认）、简体中文和繁体中文；使用 `en`、`zh-Hans`、`zh-Hant`。JSON 键、状态、路径和 raw 证据保持稳定。[plot_bands.py](knowledge/scripts/plot_bands.py) 无 `--lang`；报告语言不等于图内注释语言。

[能带绘图](knowledge/reference/topics/band-plotting.md) 默认 eV，支持 Ha/Hartree、Ry/Rydberg、meV 和带正有限换算因子的自定义单位。原生能量为 Hartree，参考只减一次；`--reference-ha`、`--ef-hartree` 不随显示单位变化。已移位 `plot.dat` 不当作完整原生谱读取。

图内保留材料/方法题名、坐标、路径与必要图例；来源、收敛、缺失自旋信息和解释限制放外部报告/JSON。不能按带号的一半划分上下自旋；`--ispin` 只记录外部来源。路径断点须有依据，不能从标签或距离跳跃自行生成。

[能级分析](knowledge/reference/topics/eigenvalue-analysis.md) 中，整数占据带数是明确假设；缺占据时仅做参考两侧诊断。采样边、同 k 直接差与整布里渊区基本带隙分开。保留打印精度，单位转换不增加信息。DOS 与 MD 按各自参考解释，本包未提供通用 DOS/PDOS 绘图器或已验证原生 DOS 样本。

### 电荷/电流场的显示语义

[场绘图参考](knowledge/reference/topics/field-plotting.md) 是 `plot_fields.py` 的格式、网格和积分约定来源。原生格式与 VASP 同名文件不可互换；使用真实配对几何，核对 x 最快的网格顺序、精确数据量、通道、有限值与单位。电荷 restart 的校验能绑定密度，不能把这一绑定扩展到另一个电流文件。

`slice` 是指定分数位置单平面上的体密度，`project` 是沿省略分数轴跨完整周期晶胞的柱积分。前者默认电子/Å³，后者默认电子/Å²；二者不是同一量的两种风格。单层与多层须根据真实几何说明；整胞投影在多层时累加所有层，不能称为单层。有限厚度层窗口积分尚未实现。

周期采样不重复端点；平面位置由原子坐标决定。保留斜晶胞真实网格和法向长度，斜柱积分不冒充正交光线投影。电荷负值保留在统计和积分中；电流先做向量积分与显示平面投影，再求图示模，不能换成逐点模的积分。

电流只解释已支持的原生局域量与已知原子单位；`ISPIN=2/4` 电流读取不受支持。缺失文件记 missing，不生成零场，也不外推自旋流、输运量或连续性验证。图、NPZ、JSON 和 Markdown 的几何、单位、原始积分、哈希与生成路径应一致；报告限制放图外。

## 8. 验证、发布与交接

先核对实际文件和各脚本 `--help`，再选择与本次变更相关的已有测试。纯文档改动优先检查可达链接、CLI 示例、路径可迁移性、名称和版本一致性；不要为了文档验证启动材料计算或安装无关依赖。新增脚本或行为变更才增加能观察正确性的针对性验证，不用测试锁定文案。

技能创建工具可用时，以实际工具位置运行：

```bash
python -X utf8 -B "$SKILL_CREATOR_ROOT/scripts/quick_validate.py" "$PASP_DFT_ROOT"
python -B "$PASP_DFT_ROOT/knowledge/scripts/analyze_outputs.py" --help
python -B "$PASP_DFT_ROOT/knowledge/scripts/analyze_eigenvalues.py" --help
python -B "$PASP_DFT_ROOT/knowledge/scripts/plot_bands.py" --help
python -B "$PASP_DFT_ROOT/knowledge/scripts/plot_fields.py" --help
```

`SKILL_CREATOR_ROOT` 仅在有该维护工具时绑定为实际位置，不是用户运行依赖。`quick_validate` 只验证入口格式/名称和部分脚手架问题；它不能证明路由可用、科学正确、所有链接存在或图形质量。Windows 维护环境用 UTF-8 读取中文。科学 Markdown 使用单美元行内公式、独占行的双美元展示公式；代码示例中的技能调用不当作公式。检查公式源语法与渲染支持时分别记录结论。

每次发布核对：

- [ ] 三份顶层文档职责清楚；七条路线及相关索引、状态机、模板入口可达。
- [ ] 所有新增本地链接指向实际文件；从无关工作目录、含空格的部署路径也能定位脚本与同包依赖。
- [ ] 示例选项、互斥项、单位和输出语义符合当前 CLI；三个报告语言没有误归到能带绘图器。
- [ ] 公开运行文档无私有路径、内部源文件/过程名、源码依赖或未公开算法说明。
- [ ] 模板必需/条件依赖与文件哈希一致；既有数值输入没有被文档改动顺带修改。
- [ ] 图外保留科学限制；未运行、未收敛、未知、缺数据与已通过契约检查清楚区分。
- [ ] 记录变更前文件清单与 SHA-256、所用解释器、验证命令/结果及尚未验证项。
- [ ] 在同一候选包完成审查后再同步安装副本与发布归档，保留可追溯备份；备份放技能发现目录之外。
- [ ] `VERSION`、发布文件名/manifest 和内容来自同一候选包；UI 规范名/显示名保持一致，技能版本不混同 PASP 二进制版本。

交接记录列出实际修改文件、测试范围、输出位置和未解决问题。对复杂行为修改可做独立有界审查；审查发现须落实到具体资源和证据，不通过额外确认流程替代可完成的验证。

## 确定性自动化契约

公开 CLI 包括 `audit_inputs.py`、`analyze_md.py`、`analyze_relax.py`、`analyze_outputs.py`、`analyze_eigenvalues.py`、`plot_bands.py` 和 `plot_fields.py`。输入审计、MD 与弛豫路由执行包内工具，再核对 JSON 与原始证据。三者支持 `--lang en|zh-Hans|zh-Hant` 和 `--format markdown|json`，输出独占创建。保持退出码契约与实际 `--help` 一致。输入审计完成可含 ERROR/UNKNOWN，MD 与弛豫检测到运行或数据问题时可返回非零。物理精度需要独立证据。

输入审计读取随包参数表作为有界登记快照。未知键保留未知，requested、参考 default、可推导 effective 与实际 read-back 分开。缺少发行资料、匹配重启来源、IBZ 或数值收敛时不得补造证据。不得为了通过池整除而更改采样或物理设置。详见 [输入审计](knowledge/reference/topics/input-audit.md)。

MD 自动化应覆盖原生逐帧完整性、有限值、原子标识、步/时间与请求长度核对、显式窗口统计和日志一致性；输入/日志缺失则降低证据范围。NVE/NVT/NPH/NPT 的守恒量和热力学解释继续按 [MD 分析](knowledge/reference/topics/md-analysis.md) 判断，物理精度由实际收敛测试建立。

弛豫日志分析覆盖步 0、离子步、完整原子表和末次完整坐标。发布验证覆盖真实固定晶胞日志、截断、步数上限、正能量阈值和 SCF 失败。详见 [弛豫分析](knowledge/reference/topics/relaxation-analysis.md)。

发布时对所有公开 CLI 执行 `--help`，并以真实用户文件完成新增工具的功能与负例测试。新增脚本链接与参数示例须在候选包验证。先完成同一候选包，再构建 ZIP、逐文件 SHA-256 和安装映射。整个已安装前像必须一致，备份在技能发现目录之外。安装只写变更/新文件，不能删除或覆盖并行修改。

```bash
python -B "$PASP_DFT_ROOT/knowledge/scripts/audit_inputs.py" --help
python -B "$PASP_DFT_ROOT/knowledge/scripts/analyze_md.py" --help
python -B "$PASP_DFT_ROOT/knowledge/scripts/analyze_relax.py" --help
```
