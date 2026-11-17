# BaTiO3：固定晶胞离子优化：状态机

从用户当前文件与意图定位S0–S7，不要求已完成阶段重做。只加载[教程](pw_relax.md)中当前阶段；[历史案例](pw_relax_run_notes.md)不能替代本次证据。

| 状态 | 本路线要完成的具体事实 | 转移条件 |
| --- | --- | --- |
| S0 | 选择polar_plus/cubic_reference/polar_minus | 记录实际输入/产物与来源后进入下一状态。 |
| S1 | Ba/Ti/O与各自结构，不互相覆盖 | 缺证据留在本状态，记录missing/unknown；不要编造补齐。 |
| S2 | 固定胞LRELAX+nstep或独立立方SCF | 记录实际输入/产物与来源后进入下一状态。 |
| S3 | 50步上限/负EDIFFG力阈值/网格差异 | 记录实际输入/产物与来源后进入下一状态。 |
| S4 | 电子与离子阈值单位、质量、池数 | 缺证据留在本状态，记录missing/unknown；不要编造补齐。 |
| S5 | 已有授权时运行所选独立分支 | 记录实际输入/产物与来源后进入下一状态。 |
| S6 | 逐步SCF、实际最大力、终止原因及末结构 | 缺证据留在本状态，记录missing/unknown；不要编造补齐。 |
| S7 | 最终结构→新SCF；比较前统一数值条件 | 记录实际输入/产物与来源后进入下一状态。 |

S4预检将当前输入/include/UPF/重启依赖、物理设置、发行兼容和资源逐项落到具体文件。适用时按[本地verifier契约](../../subskills/pasp-dft-verifier/skill.md)做有界只读复核；控制器仍负责解释与写入，不把授权反复重问。预检失败留候选与缺项，不把它称作可提交输入。输出分析路线的S4是数据解析预检，不制造输入晋级门槛。

S5材料运行仅在已有任务授权覆盖实际执行时进行；仅要求输入/教程/分析时不擅自启动PASP。已有授权的读取、可逆编写和本地分析直接完成。缺关键科学选择时只问所缺信息，不复制上游其他物理模型的确认标记。S6失败时保留日志和产物，结论标失败/未知，不晋级为validated/handoff-ready。

每个关键目录的PROGRESS至少记录：Status、Route/Branch/Stage、输入和依赖哈希、已接受设置、实际命令与ranks、上游来源、Gate evidence、缺失项、允许的下一步。结束状态可以是input-ready-with-missing-UPFs、output-validated或blocked-by-real-data；这三者不能互称已运行成功。
