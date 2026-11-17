---
name: workflow-pw-scf-bands
description: BaTiO3：从 SCF 到能带；pasp-dft 内部本地工作流，不是独立安装技能。
---

先读[状态机](../../knowledge/workflows/pw_scf_bands_state_machine.md)，定位S0–S7与实际分支，再只读[完整教程](../../knowledge/workflows/pw_scf_bands.md)当前阶段。操作交接用[检查单](../../knowledge/workflows/pw_scf_bands_user_checklist.md)，历史证据只读[run notes](../../knowledge/workflows/pw_scf_bands_run_notes.md)。

本路线具体职责：明确五原子BaTiO3的SCF或路径能带目标；Ba/Ti/O UPF与siesta.ANI闭包；6³积分SCF候选与LCHARG1；35Ha/电子阈值/资源与目标路径；核对物种、实际k点池与SCF候选；已有授权时运行SCF并移交合法配对到bands；SCF参考、谱迭代、TB内容分别通过；图/JSON/采样能隙限制与来源交付。

精确语法/默认/单位/限制交给[本地reference](../pasp-dft-reference/skill.md)；有界只读预检与输出核对使用[本地verifier契约](../pasp-dft-verifier/skill.md)。这些小写skill.md只由控制器读取，不注册新技能、不调用不存在的冒号命令。用户已有授权直接继承，不照搬其他模型的确认标记；缺UPF或运行证据时明示真实缺项。

不得依赖源码、私有路径或外部研讨会脚本。材料运行需要已有执行授权；输出分析可从已有文件直接开始。输入派生不冒充运行测试，文件存在不冒充收敛。结果写用户指定目录；保留语言选择与干净科学图题。
