---
name: workflow-pw-spin-plus-u
description: NiO：AFM 与 +U 分支；pasp-dft 内部本地工作流，不是独立安装技能。
---

先读[状态机](../../knowledge/workflows/pw_spin_plus_u_state_machine.md)，定位S0–S7与实际分支，再只读[完整教程](../../knowledge/workflows/pw_spin_plus_u.md)当前阶段。操作交接用[检查单](../../knowledge/workflows/pw_spin_plus_u_user_checklist.md)，历史证据只读[run notes](../../knowledge/workflows/pw_spin_plus_u_run_notes.md)。

本路线具体职责：确定LDA或+U以及SCF/bands；Ni/O UPF、四原子AFM行顺序；独立两分支SCF，初始Ni ±2；Ueff0.2Ha/3d/全部Ni与40总态；物种磁矩和+U记录数、池数、配对一致；已有授权时各分支SCF→bands，+U保留PLUS_U_NS；各自电子/谱收敛与+U激活证据；同条件比较，单writer-channel不冒充自旋分辨。

精确语法/默认/单位/限制交给[本地reference](../pasp-dft-reference/skill.md)；有界只读预检与输出核对使用[本地verifier契约](../pasp-dft-verifier/skill.md)。这些小写skill.md只由控制器读取，不注册新技能、不调用不存在的冒号命令。用户已有授权直接继承，不照搬其他模型的确认标记；缺UPF或运行证据时明示真实缺项。

不得依赖源码、私有路径或外部研讨会脚本。材料运行需要已有执行授权；输出分析可从已有文件直接开始。输入派生不冒充运行测试，文件存在不冒充收敛。结果写用户指定目录；保留语言选择与干净科学图题。
