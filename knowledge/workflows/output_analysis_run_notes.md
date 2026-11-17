# 已有输出：日志、能带、能级、DOS 与 MD：历史运行与证据笔记

记录日期：2026-11-17。此页是历史案例定位，不是当前运行证明、材料默认值或新计算授权。

三个Python助手具有既有解析与绘图行为，迁移后的验证由打包验收记录负责。支持读取不等于每种材料/ensemble有测试结果；未找到经验证native DOS教学输出，本课明确保留此缺口。

## 本包实际完成的检查

本包标记为 `input-derived / not-runtime-tested`：输入与实际引用结构来自现有案例，构建时只作静态闭包和哈希检查，没有启动 PASP 或 MPI。目录中已有历史输出不能自动升级本模板的证据等级。历史测试、当前输入静态检查、本次实际运行三者分别记录。所有 UPF 因再分发权限未明确而不随包分发，必须由用户合法提供；没有 UPF 时不具备运行完整性。

模板FDF和所有被引用结构按原字节复制，依赖manifest保留逐文件哈希与UPF头元数据。UPF未附，不复制CHGCAR、.restart、PLUS_U_NS、PASP.used_info、TB.bands、output_MD.dat、锁或旧日志。本包的完成不表示任何材料已收敛；真正运行结果应在用户目录留独立报告。

## 怎样追加本次证据

记录run ID、命令/版本已知信息、输入/include/UPF哈希、退出、各层收敛/完整性、实际产物哈希和引用位置。静态检查、进程成功、算法收敛、精度收敛分别写。现代marker缺失时结合发行资料与实际legacy区块判断，不能自动当失败或自动当通过。没有运行就明确input-only；不要用历史曲线补数字。

下一步按[状态机](output_analysis_state_machine.md)定位，用户操作见[完整课](output_analysis.md)与[检查单](output_analysis_user_checklist.md)。
