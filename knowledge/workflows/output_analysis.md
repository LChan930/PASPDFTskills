# 已有输出：日志、能带、能级、DOS 与 MD

先用[状态机](output_analysis_state_machine.md)定位当前阶段，再按本课对应小节操作。[检查单](output_analysis_user_checklist.md)用于实际交接，[历史笔记](output_analysis_run_notes.md)只解释已有证据边界。

## 分析资料与证据

本路线直接使用用户已有输出，不附运行输入或预制结果。分析脚本的契约测试只验证解析与绘图行为；材料结论仍需匹配的实际运行证据。只读分析不要求补齐 UPF 或启动 PASP；需要核对赝势相关结论时，明确缺少的文件或元数据。

## 学习目标与起点

从用户现有输出直接开始，不强迫创建输入/运行目录或提交新计算。先按文件**内容**识别日志、SCF本征值表、原生bands、DOS、MD轨迹；名字可以不同，`TB.bands` 名称本身不证明格式。原始文件只读，报告和图片写到用户指定的新目录。本课没有可供冒充结果的输出模板；DOS也没有已验证的原生范例。

### 第一阶段：盘点输入和来源

选定要解释的实际文件，记录大小、哈希、运行ID、关联input/include/UPF、日志、单位与SCF参考来源。候选文件不等于匹配证据：同目录不同时间的stdout/trajectory可能不是一组。对于能级明确表号、自旋表示、占据/电子数；没有填充证据不强行宣布VBM/CBM。原生band writer-channel=1不能自动推断自旋极化是否分辨，ISPIN只作为外部来源记录。

### 第二阶段：先读日志

以下命令假定 `SKILL_ROOT` 由控制器解析为本包物理根目录，`RUN_DIR`、`REPORT_DIR` 是用户工作区的实际路径。脚本输入/输出绝不写到技能目录；先创建用户自己的报告目录，选择全新文件名。

```bash
python "$SKILL_ROOT/knowledge/scripts/analyze_outputs.py" "$RUN_DIR" --format json --output "$REPORT_DIR/run-report.json"
```

默认报告英文，可显式选择 `--lang en`、`--lang zh-Hans`、`--lang zh-Hant`。扫描子目录必须用户需要时加 `--recursive`，避免把多个运行误合并。检查模型初始化、进程/结束、SCF/能带迭代、警告与输出候选，并保留raw日志片段。脚本摘要是有界提取，不能代替材料精度验证或全MD帧结构检查。

### 第三阶段：能级与能带分析

已确认原生band格式时运行：

```bash
python "$SKILL_ROOT/knowledge/scripts/analyze_eigenvalues.py" "$RUN_DIR/TB.bands" --input-kind bands --format json --output "$REPORT_DIR/eigenvalues.json"
python "$SKILL_ROOT/knowledge/scripts/plot_bands.py" "$RUN_DIR/TB.bands" --output-dir "$REPORT_DIR" --name bands --unit eV --title "Electronic band structure"
```

绘图默认PNG/PDF/SVG与JSON，输入能量为Hartree，默认减文件头参考一次。需要手选参考时用 `--reference-ha`（Ha），绝对能量用 `--absolute`，不能同时选。自定义能量单位需同时提供正有限 `--units-per-hartree`；不能把eV数值直接当Ha。路径断点仅在确认时用 `--break-before` 的1-based样点，不能从标签自动推断断线。

若解析SCF本征值，切换 `--input-kind scf` 并按实际内容选 `--table`；占据分类使用经证实的 `--occupied-bands` 或 `--ef-hartree`，两者互斥，缺来源时只作参考两侧谱诊断。不是所有自旋模式都适合整数带数二分。采样HOMO/LUMO分离、直接间隙与整BZ基本带隙分别写，不用一条高对称路径声明全局间隙。

图内只保留科学坐标、图例、材料/任务题名；不要自动加ISPIN、unknown、自旋缺失、收敛警告字幕。JSON与文字报告写清文件参考未独立验证、spin-resolved能力、源精度/舍入以及关联运行状态；图好看不改变证据状态。

### 第四阶段：DOS 分支

先阅读 [DOS参考](../reference/topics/dos.md)。需要确认原生数据格式、能量单位/零点、k权重及其归一、自旋简并/通道、展宽核和宽度、每胞/每原子归一，积分应与对应电子数/能带计数核对。没有这些条件就只识别数据，不虚构DOS命令行选项、不把路径点等权当BZ积分。本包没有专用native DOS模板或测试输出；不拿通用能带脚本声称已生成可验证DOS。

### 第五阶段：MD 分支

读取 [Si MD课](pw_md.md) 与 [MD分析参考](../reference/topics/md-analysis.md)：先匹配实际include和初态，再分requested/read-back/effective，扫描每步SCF故障并按真实原生帧计数。报告ensemble适用的能量或焓、温度/压力区间与统计窗口。通用日志脚本不能单独证明每帧坐标/速度/晶格/应力完整。

### 第六阶段：交接分析产物

交付新报告、JSON、图及源文件哈希；每个结论附来源/单位/参考/占据/运行状态及限制。数据不全写missing/unknown，不能创造结果补齐。重复运行用新输出名，脚本拒绝覆盖是正常保护；必要依赖如numpy/matplotlib缺失时说明并按用户环境安装授权处理，不假称绘图已完成。






## 资源与来源检查

分析不启动材料计算；原运行资源是解释来源的一部分，不为画图申请MPI。

参见[并行参考](../reference/topics/kpoint-band-parallelism.md)、[输入生成](../reference/topics/input-generation.md)、[验证层次](../reference/topics/validation.md)、[PW模块](../reference/modules/pw.md)、[PWRS模块](../reference/modules/pwrs.md)。

## 电荷 / 电流场分支

对真实电荷或电流输出，先按[场绘图参考](../reference/topics/field-plotting.md)识别网格、晶格、分量、单位与积分约定。先明确需要的是单平面局域体密度（`--mode slice`，默认 $e/\text{Å}^3$）还是整胞层积分面密度（`--mode project`，默认 $e/\text{Å}^2$），并在命令中显式指定模式、切片位置或整胞积分范围。单层材料仍可画这两种量；不能仅凭“单层”选模式。若用户要某一物理层的积分，先确定层边界；当前脚本未实现有限层窗口，全胞投影会合并所有层。电流也要区分局域体电流密度与积分后的面电流。再查本包 `knowledge/scripts/plot_fields.py --help` 使用实际支持的选项。Graphene新审计中两分支电荷积分为8e，只有有限磁通SCF提供CRTCAR；仅对存在的匹配数据作图，缺失的电流记录missing。物理参考和运行验证放报告/JSON，图题保持科学内容，明确切片或整胞积分；核对色标维度与JSON/Markdown中的 `representation`、`display_unit`、`integration_scope` 一致。
