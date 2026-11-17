---
name: workflow-output-analysis
description: 已有输出：日志、能带、能级、DOS 与 MD；pasp-dft 内部本地工作流，不是独立安装技能。
---

先读[状态机](../../knowledge/workflows/output_analysis_state_machine.md)，定位S0–S7与实际分支，再只读[完整教程](../../knowledge/workflows/output_analysis.md)当前阶段。操作交接用[检查单](../../knowledge/workflows/output_analysis_user_checklist.md)，历史证据只读[run notes](../../knowledge/workflows/output_analysis_run_notes.md)。

本路线具体职责：按内容识别用户已有日志/谱/DOS/MD；只读文件哈希、配对来源与缺失项；选分析对象、输出目录与表号；单位/参考/占据/自旋/权重与语言；核对解析格式与命令选项，无输入晋级要求；执行已授权本地分析，写用户新产物；核对JSON、图/计数/单位与原始证据一致；交付报告图、来源、unknown和限制。

精确语法/默认/单位/限制交给[本地reference](../pasp-dft-reference/skill.md)；有界只读预检与输出核对使用[本地verifier契约](../pasp-dft-verifier/skill.md)。这些小写skill.md只由控制器读取，不注册新技能、不调用不存在的冒号命令。用户已有授权直接继承，不照搬其他模型的确认标记；缺UPF或运行证据时明示真实缺项。

不得依赖源码、私有路径或外部研讨会脚本。材料运行需要已有执行授权；输出分析可从已有文件直接开始。输入派生不冒充运行测试，文件存在不冒充收敛。结果写用户指定目录；保留语言选择与干净科学图题。
