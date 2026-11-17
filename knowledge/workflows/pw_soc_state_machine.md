# Bi2Se3：SR 与 FR 赝势比较：状态机

从用户当前文件与意图定位S0–S7，不要求已完成阶段重做。只加载[教程](pw_soc.md)中当前阶段；[历史案例](pw_soc_run_notes.md)不能替代本次证据。

| 状态 | 本路线要完成的具体事实 | 转移条件 |
| --- | --- | --- |
| S0 | 确定SR或FR/SOC及当前阶段 | 记录实际输入/产物与来源后进入下一状态。 |
| S1 | Bi/Se精确SR/FR UPF和相对论元数据 | 缺证据留在本状态，记录missing/unknown；不要编造补齐。 |
| S2 | ISPIN4/五零磁矩/RWIGS块候选 | 记录实际输入/产物与来源后进入下一状态。 |
| S3 | SR30Ha/FR40Ha差异与比较目的 | 记录实际输入/产物与来源后进入下一状态。 |
| S4 | UPF、XC/表示兼容、独立参考配对 | 缺证据留在本状态，记录missing/unknown；不要编造补齐。 |
| S5 | 已有授权时两分支分别SCF→bands | 记录实际输入/产物与来源后进入下一状态。 |
| S6 | 实际SOC激活、谱状态与TB；无结果维持input-only | 缺证据留在本状态，记录missing/unknown；不要编造补齐。 |
| S7 | 报告数值对照差异，不声称已得SOC光谱 | 记录实际输入/产物与来源后进入下一状态。 |

S4预检将当前输入/include/UPF/重启依赖、物理设置、发行兼容和资源逐项落到具体文件。适用时按[本地verifier契约](../../subskills/pasp-dft-verifier/skill.md)做有界只读复核；控制器仍负责解释与写入，不把授权反复重问。预检失败留候选与缺项，不把它称作可提交输入。输出分析路线的S4是数据解析预检，不制造输入晋级门槛。

S5材料运行仅在已有任务授权覆盖实际执行时进行；仅要求输入/教程/分析时不擅自启动PASP。已有授权的读取、可逆编写和本地分析直接完成。缺关键科学选择时只问所缺信息，不复制上游其他物理模型的确认标记。S6失败时保留日志和产物，结论标失败/未知，不晋级为validated/handoff-ready。

每个关键目录的PROGRESS至少记录：Status、Route/Branch/Stage、输入和依赖哈希、已接受设置、实际命令与ranks、上游来源、Gate evidence、缺失项、允许的下一步。结束状态可以是input-ready-with-missing-UPFs、output-validated或blocked-by-real-data；这三者不能互称已运行成功。
