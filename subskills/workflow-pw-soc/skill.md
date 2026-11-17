---
name: workflow-pw-soc
description: Bi2Se3：SR 与 FR 赝势比较；pasp-dft 内部本地工作流，不是独立安装技能。
---

先读[状态机](../../knowledge/workflows/pw_soc_state_machine.md)，定位S0–S7与实际分支，再只读[完整教程](../../knowledge/workflows/pw_soc.md)当前阶段。操作交接用[检查单](../../knowledge/workflows/pw_soc_user_checklist.md)，历史证据只读[run notes](../../knowledge/workflows/pw_soc_run_notes.md)。

本路线具体职责：确定SR或FR/SOC及当前阶段；Bi/Se精确SR/FR UPF和相对论元数据；ISPIN4/五零磁矩/RWIGS块候选；SR30Ha/FR40Ha差异与比较目的；UPF、XC/表示兼容、独立参考配对；已有授权时两分支分别SCF→bands；实际SOC激活、谱状态与TB；无结果维持input-only；报告数值对照差异，不声称已得SOC光谱。

精确语法/默认/单位/限制交给[本地reference](../pasp-dft-reference/skill.md)；有界只读预检与输出核对使用[本地verifier契约](../pasp-dft-verifier/skill.md)。这些小写skill.md只由控制器读取，不注册新技能、不调用不存在的冒号命令。用户已有授权直接继承，不照搬其他模型的确认标记；缺UPF或运行证据时明示真实缺项。

不得依赖源码、私有路径或外部研讨会脚本。材料运行需要已有执行授权；输出分析可从已有文件直接开始。输入派生不冒充运行测试，文件存在不冒充收敛。结果写用户指定目录；保留语言选择与干净科学图题。
