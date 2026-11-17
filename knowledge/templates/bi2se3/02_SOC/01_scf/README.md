# Bi2Se3：SR 与 FR 赝势比较 — bi2se3/02_SOC/01_scf

状态：**input-derived / not-runtime-tested / 需要用户提供UPF**。

本包标记为 `input-derived / not-runtime-tested`：输入与实际引用结构来自现有案例，构建时只作静态闭包和哈希检查，没有启动 PASP 或 MPI。目录中已有历史输出不能自动升级本模板的证据等级。历史测试、当前输入静态检查、本次实际运行三者分别记录。所有 UPF 因再分发权限未明确而不随包分发，必须由用户合法提供；没有 UPF 时不具备运行完整性。

## 文件与依赖

本目录含实际 [lattice_model.fdf](lattice_model.fdf) 和它引用的 [siesta.ANI](siesta.ANI)。结构有 5 个原子，坐标/晶格单位和原子顺序见实际include。未引用cell.str不作为结构。全部本地include递归闭包已收集；密度、日志、锁、历史轨迹、共享启动脚本均未复制。

[dependency-manifest.json](dependency-manifest.json) 给出每个输入和必需UPF的SHA-256、字节数、物种顺序、价电子与相对论头信息。UPF未随包分发，按精确basename放到本运行目录；不要只改文件名冒充相同赝势。UPF头的0 Ry推荐值不视作有效截断建议。

| 物种序号 | 元素 | 必需文件（未附） | UPF XC | 相对论头 | 价电子 |
| --- | --- | --- | --- | --- | --- |
| 1 | Bi | `Bi_ONCV_PZ_fr.upf` | PZ | full | 15.00 |
| 2 | Se | `Se_ONCV_PZ_fr.upf` | PZ | full | 6.00 |

运行交接必需项：无预置重启产物；输出必须由当前独立运行生成。

## 逐项阅读原生输入

以下是实际输入中关键行的用途，完整block与其顺序直接打开FDF读取，不重新生成占位结构。

| 字段 | 此输入实际值 | 为什么保留 / 如何理解 |
| --- | --- | --- |
| `Model` | `DFT` | 选择原生 DFT；未写 PW/PWRS 派生开关时按当前参考默认解释 |
| `DFT.ENCUT` | `40 Hartree` | 波函数截断，显式 Hartree；示例不是精度收敛结果 |
| `DFT.ISPIN` | `4` | 自旋表示；不是图中自动分辨自旋通道的证明 |
| `DFT.EDIFF` | `1.0d-7` | 电子迭代阈值，Hartree；不是离子力阈值 |
| `DFT.LCHARG` | `1` | 整数 1 请求写密度，为匹配能带交接提供条件 |

结构include、`Z_values`（若存在）、UPF顺序和磁矩原子顺序必须相符。未显式Z_values不机械补齐冗余默认。默认ENCUT_RHO为所选ENCUT四倍；自动带数依赖初始化。已有非默认物理值按原例保留，不能为了资源整除更改。

## 实际操作与输出验收

复制本末级目录到用户新工作区 → 补齐UPF与必要的本分支SCF交接 → 按[完整教程](../../../../workflows/pw_soc.md)当前阶段操作 → 预检 → 已授权时用用户已知launcher运行 → 保存新的stdout/stderr/退出码 → 按该课具体输出门槛核对 → 写PROGRESS并交接。

本包不附run.sh：研讨会共享脚本不在本独立技能中，复制旧相对路径启动器会失效。实际命令、MPI ranks与scheduler由已有用户运行环境提供；不发明PASP命令行开关。

核对当前阶段 MPI ranks。`DFT.nk_pool` 必须同时整除 ranks 与**实际生成/约化后的全局 k 点数**，不是网格乘积或高对称节点数。`DFT.nb_pool` 整除 ranks/nk_pool；普通 PW 不普遍要求总带数被 band 池整除。池数乘积不必等于 ranks。PWRS 与 SCF_ONLY 的 band 池为 1，PWRS 另需 ALGO=4。未知实际点数时，候选输入删去两个资源键以采用参考默认 1/1，或在已授权资源内减少 ranks。不得为整除而改变网格、磁序、对称性或路径。SCF 与 bands 独立检查。模板原池数是历史设置，不是通用可运行承诺。

失败时保留本次日志和输入哈希，不复制旧结果凑齐。历史输出观察见[run notes](../../../../workflows/pw_soc_run_notes.md)，它们不证明本目录已运行。下一阶段和验收问题见[用户检查单](../../../../workflows/pw_soc_user_checklist.md)。
