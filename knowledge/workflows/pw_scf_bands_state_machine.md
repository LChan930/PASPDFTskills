# BaTiO3：从 SCF 到能带：状态机

从用户当前文件与意图定位S0–S7，不要求已完成阶段重做。只加载[教程](pw_scf_bands.md)中当前阶段；[历史案例](pw_scf_bands_run_notes.md)不能替代本次证据。

| 状态 | 本路线要完成的具体事实 | 转移条件 |
| --- | --- | --- |
| S0 | 明确五原子BaTiO3的SCF或路径能带目标 | 记录实际输入/产物与来源后进入下一状态。 |
| S1 | Ba/Ti/O UPF与siesta.ANI闭包 | 缺证据留在本状态，记录missing/unknown；不要编造补齐。 |
| S2 | 6³积分SCF候选与LCHARG1 | 记录实际输入/产物与来源后进入下一状态。 |
| S3 | 35Ha/电子阈值/资源与目标路径 | 记录实际输入/产物与来源后进入下一状态。 |
| S4 | 核对物种、实际k点池与SCF候选 | 缺证据留在本状态，记录missing/unknown；不要编造补齐。 |
| S5 | 已有授权时运行SCF并移交合法配对到bands | 记录实际输入/产物与来源后进入下一状态。 |
| S6 | SCF参考、谱迭代、TB内容分别通过 | 缺证据留在本状态，记录missing/unknown；不要编造补齐。 |
| S7 | 图/JSON/采样能隙限制与来源交付 | 记录实际输入/产物与来源后进入下一状态。 |

S4预检将当前输入/include/UPF/重启依赖、物理设置、发行兼容和资源逐项落到具体文件。适用时按[本地verifier契约](../../subskills/pasp-dft-verifier/skill.md)做有界只读复核；控制器仍负责解释与写入，不把授权反复重问。预检失败留候选与缺项，不把它称作可提交输入。输出分析路线的S4是数据解析预检，不制造输入晋级门槛。

S5材料运行仅在已有任务授权覆盖实际执行时进行；仅要求输入/教程/分析时不擅自启动PASP。已有授权的读取、可逆编写和本地分析直接完成。缺关键科学选择时只问所缺信息，不复制上游其他物理模型的确认标记。S6失败时保留日志和产物，结论标失败/未知，不晋级为validated/handoff-ready。

每个关键目录的PROGRESS至少记录：Status、Route/Branch/Stage、输入和依赖哈希、已接受设置、实际命令与ranks、上游来源、Gate evidence、缺失项、允许的下一步。结束状态可以是input-ready-with-missing-UPFs、output-validated或blocked-by-real-data；这三者不能互称已运行成功。
