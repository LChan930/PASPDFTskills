---
name: workflow-pwrs-magnetic
description: Graphene：零磁通与有限磁通；pasp-dft 内部本地工作流，不是独立安装技能。
---

先读[状态机](../../knowledge/workflows/pwrs_magnetic_state_machine.md)，定位S0–S7与实际分支，再只读[完整教程](../../knowledge/workflows/pwrs_magnetic.md)当前阶段。操作交接用[检查单](../../knowledge/workflows/pwrs_magnetic_user_checklist.md)，历史证据只读[run notes](../../knowledge/workflows/pwrs_magnetic_run_notes.md)。

本路线具体职责：确定Bfield路径n0=0或1与SCF/band；同C UPF、同几何，闭包完整；20×20×1 SCF，保留本例选择器调用；场与默认表示、ALGO4/nb_pool1兼容性；实际k池/ranks与各分支独立配对；已有授权时先各SCF，通过才bands；核对新审计中两分支TB及四日志；退出与谱收敛分开；只比较通过同阶段验证的零/有限磁通结果。

精确语法/默认/单位/限制交给[本地reference](../pasp-dft-reference/skill.md)；有界只读预检与输出核对使用[本地verifier契约](../pasp-dft-verifier/skill.md)。这些小写skill.md只由控制器读取，不注册新技能、不调用不存在的冒号命令。用户已有授权直接继承，不照搬其他模型的确认标记；缺UPF或运行证据时明示真实缺项。

不得依赖源码、私有路径或外部研讨会脚本。材料运行需要已有执行授权；输出分析可从已有文件直接开始。输入派生不冒充运行测试，文件存在不冒充收敛。结果写用户指定目录；保留语言选择与干净科学图题。
