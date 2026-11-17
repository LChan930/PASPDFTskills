# Si：七组原生 PW 分子动力学：历史运行与证据笔记

记录日期：2026-11-17。此页是历史案例定位，不是当前运行证明、材料默认值或新计算授权。

当前Si目录已安装七套新输入：NVE、NVT四恒温器、NPH、NPT。构建仅静态读取。NVT20Ha、带前缀Andersen0.02/fs以及当前velocity_temp拼写相对历史有变，历史轨迹不能充作本输入的结果。旧thermo_3曾4000步请求仅0–400轨迹、146唯一SCF失败步、exit9，日志/轨迹step0来源不一致；新输入尚未证明故障修复。NPH/NPT近零温、高压演示保留。

## 本包实际完成的检查

本包标记为 `input-derived / not-runtime-tested`：输入与实际引用结构来自现有案例，构建时只作静态闭包和哈希检查，没有启动 PASP 或 MPI。目录中已有历史输出不能自动升级本模板的证据等级。历史测试、当前输入静态检查、本次实际运行三者分别记录。所有 UPF 因再分发权限未明确而不随包分发，必须由用户合法提供；没有 UPF 时不具备运行完整性。

模板FDF和所有被引用结构按原字节复制，依赖manifest保留逐文件哈希与UPF头元数据。UPF未附，不复制CHGCAR、.restart、PLUS_U_NS、PASP.used_info、TB.bands、output_MD.dat、锁或旧日志。本包的完成不表示任何材料已收敛；真正运行结果应在用户目录留独立报告。

## 怎样追加本次证据

记录run ID、命令/版本已知信息、输入/include/UPF哈希、退出、各层收敛/完整性、实际产物哈希和引用位置。静态检查、进程成功、算法收敛、精度收敛分别写。现代marker缺失时结合发行资料与实际legacy区块判断，不能自动当失败或自动当通过。没有运行就明确input-only；不要用历史曲线补数字。

下一步按[状态机](pw_md_state_machine.md)定位，用户操作见[完整课](pw_md.md)与[检查单](pw_md_user_checklist.md)。


## 完整历史档案更新（0.2.2）

完整替换档案：历史 2 Ha、64 Si、Nose 恒温器 3（SMASS=20），1 fs × 4000 步；4001 完整帧，0–4 ps。全部日志步与轨迹一致，正常结束，无 SCF 失败。2–4 ps 温度 79.91318 ± 45.62510 K（总体标准差）；全程 80.02175 ± 46.93557 K。ZIP SHA256: 0f44c3e71a98af2f23dd2f26300f9ebe40d0cc7cf4f3170aa22e58729a6cdf59。旧截断/日志不匹配样本的失败审计保留为 superseded original archive，不能套用于本档案。当前模板为独立的 20 Ha 输入，状态仍 input-derived-not-runtime-tested；历史成功不证明代码故障修复或当前输入已经运行，也未建立 cutoff/dt 收敛或热平衡。

恒温器映射：1 Langevin、2 Andersen、3 Nose、4 速度重标度。档案只作历史证据，本技能不分发运行日志、轨迹或 UPF。
