---
name: workflow-pw-md
description: Si：七组原生 PW 分子动力学；pasp-dft 内部本地工作流，不是独立安装技能。
---

先读[状态机](../../knowledge/workflows/pw_md_state_machine.md)，定位S0–S7与实际分支，再只读[完整教程](../../knowledge/workflows/pw_md.md)当前阶段。操作交接用[检查单](../../knowledge/workflows/pw_md_user_checklist.md)，历史证据只读[run notes](../../knowledge/workflows/pw_md_run_notes.md)。

本路线具体职责：选择七组之一与演示/生产目标；实际2或64原子Si结构、Si UPF、28.086amu；Gamma/20Ha/真实初态与对应ensemble候选；dt/步数/温压/恒温器，requested与effective；1/1池、初速、电子设置与三层控制检查；已有授权时以用户已知launcher独立运行；逐步SCF、退出、N+1完整帧、ensemble观测量；统计窗、来源、thermo3旧失败与新输入未验证分开。

精确语法/默认/单位/限制交给[本地reference](../pasp-dft-reference/skill.md)；有界只读预检与输出核对使用[本地verifier契约](../pasp-dft-verifier/skill.md)。这些小写skill.md只由控制器读取，不注册新技能、不调用不存在的冒号命令。用户已有授权直接继承，不照搬其他模型的确认标记；缺UPF或运行证据时明示真实缺项。

不得依赖源码、私有路径或外部研讨会脚本。材料运行需要已有执行授权；输出分析可从已有文件直接开始。输入派生不冒充运行测试，文件存在不冒充收敛。结果写用户指定目录；保留语言选择与干净科学图题。


## 完整历史档案更新（0.2.2）

完整替换档案：历史 2 Ha、64 Si、Nose 恒温器 3（SMASS=20），1 fs × 4000 步；4001 完整帧，0–4 ps。全部日志步与轨迹一致，正常结束，无 SCF 失败。2–4 ps 温度 79.91318 ± 45.62510 K（总体标准差）；全程 80.02175 ± 46.93557 K。ZIP SHA256: 0f44c3e71a98af2f23dd2f26300f9ebe40d0cc7cf4f3170aa22e58729a6cdf59。旧截断/日志不匹配样本的失败审计保留为 superseded original archive，不能套用于本档案。当前模板为独立的 20 Ha 输入，状态仍 input-derived-not-runtime-tested；历史成功不证明代码故障修复或当前输入已经运行，也未建立 cutoff/dt 收敛或热平衡。

恒温器映射：1 Langevin、2 Andersen、3 Nose、4 速度重标度。档案只作历史证据，本技能不分发运行日志、轨迹或 UPF。

## 自动化预检与逐帧交接

S4 用包内 `knowledge/scripts/audit_inputs.py` 做递归 include、结构/依赖、默认/条件与已知 ranks/pool 静态检查，详见 [输入审计](../../knowledge/reference/topics/input-audit.md)。S6–S7 使用 `knowledge/scripts/analyze_md.py` 分析真实原生轨迹，可配 `--input` 与 `--log`，按需要显式指定 `--window-start-fs`/`--window-end-fs`。先看两者实际 `--help`；报告写用户新文件。

静态配置、实际读回、轨迹完成、电子求解与物理精度分别保留。未知发行兼容性、缺输入或不匹配日志不能由历史 thermo_3 成功补足；工具不自动选择温压、ensemble 或平衡窗。
