# 参数索引

| 参数族 | 精确资料 |
| --- | --- |
| 模型、结构、UPF、XC、自旋、SCF、占据、展宽、I/O、对称性、并行 | [核心参数](input-parameters-core.md) |
| 原生 MD、固定胞弛豫、TDDFT、NAMD、EPC 等工作流设置 | [工作流参数](input-parameters-workflows.md) |
| 输出、绘图、磁矩、响应及辅助选项 | [辅助参数](input-parameters-auxiliary.md) |

表中默认值保留依赖表达式，例如 ENCUT_RHO 随 ENCUT、某些 MD 参数由系综覆盖。生成输入先查触发这些默认的 tag，不能孤立地删减。ISPIN=4 不等同于自动启用 SOC；LPRECOND 不当作 PWRS 预处理开关。
