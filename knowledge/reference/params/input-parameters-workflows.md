# MD、优化与响应工作流参数参考

本页是随技能打包的参数知识快照（2026-11-16），不是官方手册或所有发行版本的支持承诺。仅在用户确实执行相应任务时使用；以用户的发行说明、配套示例及匹配日志确认兼容性。不需要源码，也不把参数可读或默认存在等同于物理支持。主开关见[核心参数](input-parameters-core.md)，文件与组合见[输入生成](../topics/input-generation.md)。

参考默认值不是步长、质量、温度、精度或材料参数推荐。实数裸值的单位按各行解释，不套用全局统一换算。未列出的枚举、恒温器/场/自旋组合不能从相似名字外推。

## 原生 MD

原生MD使用 `DFT.LMD T` 与 `PW_MD.*`；不要与其他模型的 `MD.*` 混用。磁场或分子Berry的参考配置仅允许solver/thermostat/ensemble/barostat为**3/0/1/0**。显式冲突值可能先被拒绝，不能期望之后覆盖补救。

| 键 | 类型/单位 | 参考默认 | 条件、覆盖与使用边界 |
| --- | --- | --- | --- |
| `PW_MD.lmolBC` | logical | 继承DFT.Bfield | 分子Berry力选项；显式F不关闭轨道场的离子Lorentz力。无场T的分子Berry参考限NC、ISPIN1/2、有隙等条件。 |
| `PW_MD.solver` | integer | 场或lmolBC时3；否则1 | 参考1=Verlet、2=Beeman、3=leapfrog；无场ensemble2强制1，3/4强制2。3需thermostat0，1的恒温器取1..4。 |
| `PW_MD.thermostat` | integer | 场或lmolBC时0；否则1 | 0无恒温器、1Langevin、2Andersen、3Nose类、4速度重标度。无场ensemble3/4强制4；与solver/ensemble联合确认。 |
| `PW_MD.dt` | real，fs | 1 | 按体系验证正且有限步长，默认1fs不是稳定性保证；NAMD覆盖为其外层步长一半。 |
| `PW_MD.temperature` | real，K | 0 | 目标温度，同时决定velocity_temp与tolp的缺省；有限温度任务显式给定。 |
| `PW_MD.nstep` | integer | 10 | 原生MD总步数；NAMD使用自身nstep，不能用此键控制NAMD外层步数。 |
| `PW_MD.velocity_temp` | real，K | 已选temperature | 无显式速度块时决定随机/零温初速；有MD_initial_velocity则不决定初始速度。 |
| `PW_MD.ensemble` | integer | 1 | 1=NVE、2=NVT、3=NPH、4=NPT；2强制solver1，3/4强制solver2、thermostat4、barostat1，其他已知恒体积任务barostat0。 |
| `PW_MD.Langevin_Gamma` | real，质量阻尼约定 | 0 | thermostat1时使用；NVE覆盖0，NVT参考需>=1e-8。不是可直接当1/fs的频率，需按发行单位说明设置。 |
| `PW_MD.barostat` | integer | 0 | 0无、1Parrinello-Rahman；参考最终由ensemble覆盖，3/4为1，其余为0。磁性门禁先检验输入，非0仍可能拒绝。 |
| `PW_MD.Langevin_Gamma_L` | real，晶胞质量阻尼约定 | 0 | 晶胞阻尼相关输入；不能仅凭参数存在就保证某版本具有完整Langevin晶胞动力学，先取得发行资料与验证。 |
| `PW_MD.PMASS` | real，amu | 1000 | barostat1的晶胞惯量；参考换算系数约1.06647至Ha fs²/Bohr²，数值需按任务验证。 |
| `PW_MD.pressure` | real，GPa | 0 | 主要用于ensemble3/4；常体积任务没有同等作用。 |
| `PW_MD.nelmin` | integer | 10 | 后续MD电子计算的最少迭代；还需满足EDIFF与NELM。逐步检查收敛，不假设失败必定终止轨迹。 |
| `PW_MD.Andersen_Prob` | real，1/fs | 0.1 | thermostat2，乘步长成为每步碰撞概率；NVE为0，NVT参考需>=1e-8，确认最终概率在合法范围。 |
| `PW_MD.SMASS` | real，单位需版本确认 | 1000 | thermostat3的惯量；本参考不保证可移植输入量纲。必须正且有限，不能因0未被拒绝就使用；NVE参考改为极大值。 |
| `PW_MD.tolp` | real，K | 0.1×temperature | thermostat4温度容差；NVE参考改为极大值。 |
| `PW_MD.nraise` | integer | 10 | 重标度检查间隔，必须>0。 |

质量阻尼的参考单位为质量/fs，其中质量约定为Ha fs²/Bohr²；晶胞阻尼对应晶胞惯量/fs。具体发行版本资料若不足，不凭参数名字换算成裸频率或作定量推荐。NVT的Langevin默认零阻尼不是可运行恒温配置；应选择并确认有效阻尼或其他受支持恒温器。

| 块 | 形状 | 参考缺省 | 用户含义与边界 |
| --- | --- | --- | --- |
| `MD_initial_velocity` | 每原子一行3实数 | 无块；按velocity_temp生成 | 裸Angstrom/fs；存在时不随机初始化，也不自动去除平均速度。无块随机初速参考去平均并归一化，0K为零速度。 |
| `DFT.MASS` | 按物种次序给全部质量 | 每物种1 | 裸amu；**不是元素质量表**。真实MD必须给正确物种质量；优化也可能受质量缩放影响，不用atom_mass替代。 |

磁场/分子Berry任务还应核查每步电子收敛、力、能量漂移、时间步与初态；输入被接受不证明物理可靠。若版本支持有自旋站点磁矩输出，按[辅助参数](input-parameters-auxiliary.md)提供正且有限的RWIGS。

## 固定胞离子优化

| 键 | 类型 | 参考默认 | 边界 |
| --- | --- | --- | --- |
| `DFT.relax.fixed_cell` | logical | T | 本参考只覆盖固定胞优化；F拒绝，不能声称支持变量胞。 |

同时需要 `DFT.LRELAX T` 与正 `DFT.nstep`。默认nstep0仅初始SCF/力应力，不更新离子。`DFT.EDIFFG`正值为Ha能量变化阈值，负值绝对值为eV/Angstrom力阈值；与电子EDIFF分开。质量块和实际结构必须正确，不用未知默认制作物理收敛结论。

## TDDFT

独立TDDFT使用 `DFT.LTDDFT T`。参考ISPIN2拒绝，ISPIN1关闭原子磁矩输出；其他自旋/外场组合先核对发行资料。NAMD会覆盖多项同名相关设置，不能将以下默认直接当NAMD有效值。

| 键 | 类型/单位 | 参考默认 | 含义与边界 |
| --- | --- | --- | --- |
| `TDDFT.nstep` | integer | 10 | 电子传播步数；NAMD覆盖为其int_step×nstep。 |
| `TDDFT.solver` | integer | 2 | 1=RK2、2=ETRS、3=AETRS、4=ExpMid、5=CN；NAMD另用自身solver_TD。 |
| `TDDFT.exp_order` | integer | 4 | 非CN指数展开阶数，至少1；默认不是精度保证。 |
| `TDDFT.exp_method` | integer | 1 | 1=Taylor、2=Chebyshev；2需发行版本明确支持，不能从名字认定可用；NAMD强制1。 |
| `TDDFT.cn_rmax` | real，残差阈值 | 4e-8 | 仅CN线性方程求解，不是普通SCF收敛阈值。 |
| `TDDFT.cn_solver` | integer | 1 | CN的1=CG、2=PCG，其他值不使用。 |
| `TDDFT.int_step` | integer | 1 | 独立TDDFT的观测间隔，必须>0；NAMD会绑定为自身电子子步数。 |
| `TDDFT.EDIFF_diag` | real，Ha | DFT.EDIFF | 瞬时本征值对角化阈值，不能按eV再换算一次。 |
| `TDDFT.excition` | logical | F | 保留准确拼写excition；初始占据的电子空穴激发相关选项，不是通用激子求解器。 |
| `TDDFT.ext_field` | logical | F | T必须提供完整TD_external_field；F不使用该块。 |
| `TDDFT.dt` | real，fs | 1 | 默认不是实时电子传播推荐步长；按时间尺度与守恒收敛测试，NAMD覆盖。 |
| `TDDFT.output_energy` | logical | F | 能量输出；NAMD强制F。 |
| `TDDFT.output_dipole` | logical | F | 偶极矩输出。 |
| `TDDFT.output_eigval` | logical | F | 瞬时本征值输出；投影还需同时设置此项。 |
| `TDDFT.output_projec` | logical | F | 投影输出，需output_eigval与output_projec均T。 |
| `TDDFT.output_charge` | logical | F | 最终密度输出。 |
| `TDDFT.output_ffield` | logical | F | 最终场输出，需ext_field T。 |
| `TDDFT.output_chgmag` | logical | F | 网格密度/磁化积分观测输出。 |
| `TDDFT.output_magmom` | logical | F | 原子磁矩输出；ISPIN1参考强制F。 |
| `TDDFT.output_chgmid` | logical | F | 传播中密度快照；参考会清空并重建工作目录chgs，先保留已有重要结果。 |
| `TDDFT.nband` | integer | 全局带数 | 本征值/投影使用的带数，NAMD solver_TD4可覆盖为nband_adiabatic。 |

### TD_external_field 块

仅在 `TDDFT.ext_field T` 时使用；第一行为正整数场数，随后每场一行字段：

```text
ftype vx vy vz func omega phi tau t0
```

上面列出的字段共9项（ftype、三矢量分量、func和四实参数）。使用前以用户版本手册或实际已验证输入核实布局，不能凭其他资料的列数补造字段。所有字段需明确给出，没有字段级默认。缺少目标版本的场函数定义时，不拼出声称可运行的外场块。

参考类型包括1电场、2自旋磁场（需ISPIN4）、3/4/5沿相应晶胞轴的折叠电场、6矢势。type2矢量以eV能量形式给定；电场矢量参考采用eV/Angstrom，omega为1/fs、phi为rad、tau/t0为fs。type6的独立物理单位与函数1..6的确切包络定义需发行资料确认，不因类似转换就宣称已验证。尤其不要用未确认的函数编号猜造脉冲。

## NAMD 覆盖层

原生NAMD使用 `DFT.LNAMD T`。本参考的NAMD会关联TDDFT与MD设置，再由自身参数覆盖有效时间步、总步数等；实际日志优先用于核对。不要把独立TDDFT.solver或PW_MD.solver当NAMD主积分器选择。

| 键 | 类型/单位 | 参考默认 | 含义、覆盖与边界 |
| --- | --- | --- | --- |
| `PW_NAMD.solver_MD` | integer | 1 | 参考最终按ensemble覆盖：3/4为2，其余为1；不通过此键声称可任意选择离子积分器。 |
| `PW_NAMD.solver_TD` | integer | 1 | 1=ETRS、2=AETRS、3=MAETRS、4=WangLw；4涉及绝热带数，其他枚举不使用。 |
| `PW_NAMD.dt` | real，fs | 1 | 外层步长；离子子步为一半，电子子步为dt/int_step。默认不保证稳定。 |
| `PW_NAMD.int_step` | integer | 1 | 每外层步的电子子步数，必须>0；不同于独立TDDFT观测间隔，但参考绑定两者。 |
| `PW_NAMD.nstep` | integer | 10 | 外层步数，电子总步数为与int_step的乘积。 |
| `PW_NAMD.nband_adiabatic` | integer | 2×全局带数 | solver_TD4的绝热带数，并覆盖TDDFT.nband；不能据默认断言空带足够。 |
| `PW_NAMD.HDIFF` | real，Ha矩阵变化约定 | 1e-8 | WangLw相关迭代阈值，不是普通SCF的EDIFF。 |
| `PW_NAMD.EDIFF_adiabatic` | real，Ha | DFT.EDIFF | 绝热对角化阈值，不再按eV转换。 |

其他参考覆盖包括exp_method1、output_energy F，以及首次SCF后线性混合0.5。不要由共享键推断磁性NAMD或任意组合受支持；按任务发行资料和验证结果报告。

## RRAM

| 键或块 | 类型/形状 | 参考默认 | 单位与边界 |
| --- | --- | --- | --- |
| `DFT.RRAM.pot` | real | 0 | 偏压相关参数；本参考不提供可移植的能量/电势统一换算保证，需版本资料确认，不给通用偏压数值推荐。 |
| `DFT.RRAM.lambda` | real | 1 | 罚项系数，单位与数值适用性需任务说明，默认不证明物理可靠。 |
| `DFT.RRAM.possplit` | 4实数块 | 必需 | 裸Bohr区域数据；中间两个界面必须有非零间距，不能替用户猜区域。 |
| `DFT.RRAM.poselectrode` | 4实数块 | 必需 | 裸Bohr，两个电极z区间端点，区间宽度非零；参考z向几何不推广任意方向。 |

零偏压也需要有效几何块。参考不支持RRAM+U；对偏压、罚项单位或区间定义不清楚的输入，先列出具体缺项，不把成功读入当有效模型。

## EPC/EPR

仅在 `DFT.LEPC T` 时考虑；`PW_EPC.EPR T` 选择EPR。两者需要与结构、网格及自旋匹配的实际 `dvloc` 数据；二阶EPR还需 `R_index`。普通SCF模板不附带这些选项，数据格式未知时请求配套发行说明或已验证示例，不自行猜文件格式。

| 键 | 类型/单位 | 参考默认 | 含义与限制 |
| --- | --- | --- | --- |
| `PW_EPC.energy_window` | real，eV | 0.2 | 费米能附近能窗，必须正且有限并覆盖所需态；默认不证明收敛。 |
| `PW_EPC.qx_sc` | integer | 1 | x向超胞倍数，>=1；需匹配dvloc网格。 |
| `PW_EPC.qy_sc` | integer | 1 | y向倍数，>=1，同上。 |
| `PW_EPC.qz_sc` | integer | 1 | z向倍数，>=1，同上。 |
| `PW_EPC.read_wfc_qe` | logical | F | 请求读取匹配的QE波函数，独立于共用RWAVE；需确认发行版本支持的数据格式。 |
| `PW_EPC.use_low_memory` | logical | F | EPC文件存储相关低内存选择；实际磁盘空间与耗时需测量，不假定所有响应流程同样适用。 |
| `PW_EPC.pack_size` | integer | 全部非局域投影类型数 | 文件分包相关大小，必须>0；无明确需求通常省略，不用未知常数替代动态默认。 |
| `PW_EPC.2nd_order` | logical | F | EPR二阶选项，T还需要实际R_index文件。 |
| `PW_EPC.2nd_order_RIA` | logical | T | 二阶且F时，qx_sc/qy_sc/qz_sc需全奇数；默认T不证明所有近似已验证。 |
| `PW_EPC.nband_conv` | integer | 全局带数 | EPR收敛带数，1..全局带数；按任务收敛测试。 |

不推荐把 `PW_EPC.test` 或相关诊断选项加入常规计算。本技能不提供它们的跨版本运行保证；确需使用时先取得该版本配套操作说明和已验证输入，不能将缺省零位移等当安全设置。

结果交付应说明实际启用的阶段、有效参数、必需数据、版本依据、输出状态及未验证项。输入语法检查与分析脚本通过均不等于真实MD、光谱、响应或轨迹已经验证。

### Audit evidence and provenance

When auditing existing MD, read [native MD analysis and provenance](../topics/md-analysis.md) together with the input and output guides. Do not infer a final integrator, thermostat or barostat from enum names or a `PASP.used_info` echo alone. Preserve requested, read-back and effective controls separately. Check all unique failed MD steps across the full log; MPI repetitions and LOBPCG renormalization are distinct diagnostics. A missing modern marker does not establish failure.

Use actual trajectory headings and units. Native records may contain `Step`, `Time`, `Ep`, `Ek`, `Etot`, `Temp`, `H`, positions/velocities, and variable-cell lattice/stress blocks. Step zero plus N updates gives N+1 frames. Match initial states across input, log and trajectory before joining rows; retain mismatches independently. Energy sums in thermostatted or variable-cell ensembles are descriptive until the release defines the conserved extended quantity. Report observed windows and duration rather than certifying equilibrium from a latter-half slice.
