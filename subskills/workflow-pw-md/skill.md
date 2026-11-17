---
name: workflow-pw-md
description: Si：七组原生 PW 分子动力学；pasp-dft 内部本地工作流，不是独立安装技能。
---

先读[状态机](../../knowledge/workflows/pw_md_state_machine.md)，定位S0–S7与实际分支，再只读[完整教程](../../knowledge/workflows/pw_md.md)当前阶段。操作交接用[检查单](../../knowledge/workflows/pw_md_user_checklist.md)，历史证据只读[run notes](../../knowledge/workflows/pw_md_run_notes.md)。

本路线具体职责：选择七组之一与演示/生产目标；实际2或64原子Si结构、Si UPF、28.086amu；Gamma/20Ha/真实初态与对应ensemble候选；dt/步数/温压/恒温器，requested与effective；1/1池、初速、电子设置与三层控制检查；已有授权时以用户已知launcher独立运行；逐步SCF、退出、N+1完整帧、ensemble观测量；统计窗、来源、thermo3旧失败与新输入未验证分开。

精确语法/默认/单位/限制交给[本地reference](../pasp-dft-reference/skill.md)；有界只读预检与输出核对使用[本地verifier契约](../pasp-dft-verifier/skill.md)。这些小写skill.md只由控制器读取，不注册新技能、不调用不存在的冒号命令。用户已有授权直接继承，不照搬其他模型的确认标记；缺UPF或运行证据时明示真实缺项。

不得依赖源码、私有路径或外部研讨会脚本。材料运行需要已有执行授权；输出分析可从已有文件直接开始。输入派生不冒充运行测试，文件存在不冒充收敛。结果写用户指定目录；保留语言选择与干净科学图题。
