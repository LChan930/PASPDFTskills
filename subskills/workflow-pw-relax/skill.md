---
name: workflow-pw-relax
description: BaTiO3：固定晶胞离子优化；pasp-dft 内部本地工作流，不是独立安装技能。
---

先读[状态机](../../knowledge/workflows/pw_relax_state_machine.md)，定位S0–S7与实际分支，再只读[完整教程](../../knowledge/workflows/pw_relax.md)当前阶段。操作交接用[检查单](../../knowledge/workflows/pw_relax_user_checklist.md)，历史证据只读[run notes](../../knowledge/workflows/pw_relax_run_notes.md)。

本路线具体职责：选择polar_plus/cubic_reference/polar_minus；Ba/Ti/O与各自结构，不互相覆盖；固定胞LRELAX+nstep或独立立方SCF；50步上限/负EDIFFG力阈值/网格差异；电子与离子阈值单位、质量、池数；已有授权时运行所选独立分支；逐步SCF、实际最大力、终止原因及末结构；最终结构→新SCF；比较前统一数值条件。

S6–S7 使用包内 `knowledge/scripts/analyze_relax.py` 读取本次弛豫日志，可附匹配的 FDF。按报告核对逐步能量、原子最大力、离子终止、进程完成及电子证据。末次完整坐标保留日志精度，结构交接另查匹配的原生全精度产物。见 [弛豫分析](../../knowledge/reference/topics/relaxation-analysis.md)。

精确语法/默认/单位/限制交给[本地reference](../pasp-dft-reference/skill.md)；有界只读预检与输出核对使用[本地verifier契约](../pasp-dft-verifier/skill.md)。这些小写skill.md只由控制器读取，不注册新技能、不调用不存在的冒号命令。用户已有授权直接继承，不照搬其他模型的确认标记；缺UPF或运行证据时明示真实缺项。

不得依赖源码、私有路径或外部研讨会脚本。材料运行需要已有执行授权；输出分析可从已有文件直接开始。输入派生不冒充运行测试，文件存在不冒充收敛。结果写用户指定目录；保留语言选择与干净科学图题。
