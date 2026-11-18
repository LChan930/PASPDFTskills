# 核心 DFT 参数参考

本页是随技能打包的 PW/PWRS 参数知识快照（2026-11-16），不是官方手册或任何发行版本的支持承诺。与用户的发行资料、配套示例及实际日志核对；未知版本标记兼容性未验证，不要求源码。默认值只描述缺键时的参考行为，不是材料精度推荐。先读[输入生成](../topics/input-generation.md)，只添加当前任务所需设置。

表中 T/F 为布尔值；整数0/1开关不能一概改成布尔值。`real` 为实数；裸数参数不自动接受物理单位。`ENCUT`、`ENCUT_RHO` 等明确标记为“带单位”的量显式写单位。依赖其他键的默认值应按有效设置解释，不复制成常数。

## 入口、表示与任务

| 键 | 类型 | 参考默认 | 含义、条件与限制 |
| --- | --- | --- | --- |
| `DFT.inputV` | logical | F | 特殊外势任务，不是普通赝势SCF；与SCF_ONLY冲突，不加入一般模板。 |
| `DFT.Zfield` | logical | F | Zeeman开关；强制all-k、apply_Hpsi并关闭空间对称性，不强制RS。场矢量用独立Zfield块或磁场关联设置。 |
| `DFT.Bfield` | logical | F | 轨道磁场；强制RS、all-k、apply_Hpsi并关闭空间对称性。反向RS F无效；磁通n0默认1，不自动选预条件模式4或Zeeman。 |
| `DFT.LEfield` | logical | F | 有限电场任务；关闭对称性并使用全k。缺DFT.Efield块为非零z场0.001原子单位，需有意指定；有绝缘性等限制。 |
| `DFT.nk_pool` | integer | 1 | 正整数；整除MPI ranks及约化后实际全局k点数，单rank为1；Chern限1。见[并行池](../topics/kpoint-band-parallelism.md)。 |
| `DFT.nb_pool` | integer | 1 | 正整数；整除每k池ranks；PWRS与SCF_ONLY限1。普通PW band并行按算法与版本核查。 |
| `DFT.LTDDFT` | logical | F | 实时电子传播；关闭对称性、使用全k，附加设置见[工作流参数](input-parameters-workflows.md)。 |
| `DFT.LMD` | logical | F | 原生DFT分子动力学，关闭对称性、使用全k；不与其他模型的MD键混用。 |
| `DFT.LNAMD` | logical | F | 非绝热动力学，关闭对称性、使用全k；有自身时间步与积分器设置。 |
| `DFT.RS` | logical | F | PWRS表示；Bfield可强制T。完整RS限ALGO4、单band池；RS.kinetic与RS.vnl为T。 |
| `DFT.SCF_ONLY` | logical | F | 受限SCF能量流程；不写常规密度/波函数交接文件，与MD/TDDFT/能带/电场等组合冲突，参考不支持+U。零退出码不保证收敛。 |

多个主任务开关不是执行队列；按[输入生成](../topics/input-generation.md)选择当前阶段，避免混用。

## 文件、后处理与场控制

| 键 | 类型 | 参考默认 | 含义、条件与限制 |
| --- | --- | --- | --- |
| `DFT.use_apply_Hpsi` | logical | F | Hamiltonian作用相关选项，Bfield/Zfield强制T；不是所有ALGO统一的矩阵自由开关。 |
| `DFT.delta_tau` | real | 0.005 | 裸Bohr位移，有限且>0；同一标量用于三个方向。不是MD时间步。 |
| `DFT.LDIPFEILD` | logical | F | 偶极修正；保留准确拼写FEILD，不猜造LDIPFIELD。附加方向键见[辅助参数](input-parameters-auxiliary.md)。 |
| `DFT.lusesym` | logical | T | 空间对称性；all-k、场与动力学可能强制F。仅设F仍可能时间反演约化。 |
| `DFT.luse_all_kpoints` | logical | F | T表示全k并使lusesym F；场和动力学可强制T。不要为并行整除而改动。 |
| `DFT.PWL.n0` | integer | 1 | Bfield T时使用，沿a3的磁通量子数；默认有限磁通，0不等于关闭磁分支。不是过时参数。 |
| `DFT.luseBasZ` | logical | F | 磁分支的Zeeman关联选项。需同时Zfield T才有相应Zeeman作用；T时独立Zfield块不决定场值。 |
| `DFT.lbandstructure` | logical | F | 固定密度路径能带；读取匹配SCF密度与参考文件；BandLines优先，不需复制SCF网格或额外RCHARG1。 |
| `DFT.spin_exchange` | logical | F | 自旋交换相关任务；ISPIN1参考拒绝。开关不能证明输出交换量的物理充分性。 |
| `DFT.spin_exchange_Rcut` | real | 0 | 裸Bohr截断；0不是自动覆盖所有所需邻壳的保证，需按任务选范围。 |
| `DFT.LCHARG` | integer | 0 | 1请求写密度CHGCAR及参考.restart；SCF_ONLY不写。+U还需占据数据；不是布尔开关。 |
| `DFT.LWAVE` | integer | 0 | 1请求波函数输出；SCF_ONLY不写。核对版本的实际文件与重启条件。 |
| `DFT.RCHARG` | integer | 0 | 1请求初始化密度；可与RWAVE1共存，波函数读入不覆盖该密度，普通SCF随后正常更新。能带自动读密度，RCHARG可省；参见[重启组合](../modules/pw.md#density-and-wavefunction-restart)。 |
| `DFT.RWAVE` | integer | 0 | 1请求读WAVECAR初始轨道，可与RCHARG1共存；ALGO1不读，受限FFT_BOX禁止。需匹配基组/自旋/k点等，读文件不等于兼容或收敛。参见[重启组合](../modules/pw.md#density-and-wavefunction-restart)。 |
| `DFT.LCURRENT` | integer | 0 | 电流输出；受SCF_ONLY与FFT_BOX限制，不作为普通模板必需项。 |
| `DFT.LVLOC` | logical | F | 局域势输出；类型不同于LCHARG，SCF_ONLY不写。 |
| `DFT.RVLOC` | logical | F | 特定非自洽任务读取局域势，不是一般SCF密度重启替代。 |
| `DFT.LBERRY` | integer | 0 | Berry极化相关任务，使用重建的k串；与Chern/分子Berry不同，另需相关条件。 |
| `DFT.LBERRY.READCHG` | integer | 0 | Berry任务的密度读取触发，仍需匹配文件。 |
| `DFT.LCHERN` | integer | 0 | Chern任务；参考限NC、ISPIN1/2、单k池/单band池及足够完整能带。不能推广到任意自旋与赝势。 |
| `DFT.LRRAM` | logical | F | RRAM任务；SCF_ONLY冲突，参考不支持+U，需区域块与确认单位。 |
| `DFT.LNSC` | logical | F | 非自洽任务，需按目标准备文件；与SCF_ONLY冲突，不能当普通自洽开关。 |
| `PW_EPC.EPR` | logical | F | DFT.LEPC T时选择EPR；单独T不触发响应任务。 |
| `DFT.LEPC` | logical | F | EPC/EPR主开关，需响应辅助数据；不要与其他主任务堆叠。 |
| `DFT.LRELAX` | logical | F | 固定胞离子优化；nstep默认0时仅初始计算，不发生离子循环。 |
| `DFT.nstep` | integer | 0 | 离子优化步数；不是PW_MD.nstep，也不是有限差分半宽RS.MD。 |

## 混合

| 键 | 类型 | 参考默认 | 含义与限制 |
| --- | --- | --- | --- |
| `DFT.mixing` | real | 0.1 | 电荷混合系数；线性、Pulay、Broyden中的具体适用不同。FFT_BOX要求有限且0<值<=1；NAMD参考改为线性0.5。 |
| `DFT.mixing_mag` | real | 0.1 | Pulay磁通道等的混合；不是所有自旋更新的统一系数。+U占据混合区分电荷/磁通道。 |
| `DFT.mixing.Pulay_m` | integer | 6 | Pulay/Broyden历史长度；使用正整数，未拒绝非法值不表示支持。 |
| `DFT.mixing.method` | integer | 2 | 1=线性，2=Pulay，3=Broyden；只用已知枚举，FFT_BOX限1。 |

线性密度混合的各分量使用mixing；Pulay磁通道使用mixing_mag，电荷通道使用mixing；Broyden使用mixing。不要通过参数名字推断所有流程均采用相同规则。

## 截断、电子、自旋与阈值

| 键 | 类型/单位 | 参考默认 | 含义与限制 |
| --- | --- | --- | --- |
| `DFT.ENCUT` | 带能量单位的real | 10 Ha | 普通PW轨道截断；不是材料推荐，PWRS不按此截断轨道网格。 |
| `DFT.ENCUT_RHO` | 带能量单位的real | 已选ENCUT的4倍 | 密度截断并影响FFT网格；不是固定40Ha，专用FFT_BOX另有网格约定。 |
| `DFT.ALGO` | integer | 4 | 参考枚举：1稠密、2矩阵LOBPCG、3作用式LOBPCG、4robust、5PCG、6Davidson；PWRS仅4，band并行另核查。非法枚举不因未报错就可用。 |
| `DFT.NBAND` | integer，总带数 | 0 | 0表示自动：电子数给出约20%空带且至少4条，再受基组上限与自旋影响。显式非零值不自动自旋倍增；按目标占据和空带选。 |
| `DFT.EDIFF` | real，裸Ha | 1e-4 | 参考SCF能量/本征值等变化阈值，不是密度残差；能带以本征值变化判定。精度仍需收敛测试。 |
| `DFT.EDIFFG` | real，符号决定意义 | 1e-4 | 正值比较能量变化（Ha）；负值的绝对值为力阈值（eV/Angstrom）。不能统一按Ha解释。 |
| `DFT.ISPIN` | integer | 1 | 1无自旋、2共线、4非共线。2/4的MAGMOM每原子仍需三分量；SOC还依赖UPF，不由4单独证明。ISPIN4梯度XC有参考限制。 |
| `DFT.NELM` | integer | 500 | 最大电子迭代数；最大步数不是收敛保证，最后一轮可能仍标记MAXITER。路径能带至少需两轮才可能按变化量收敛。 |
| `DFT.ISMEAR` | integer | -1 | -1或正整数使用OccupationFunction（默认FD）；显式MP另用OccupationMPOrder默认1，不能把正ISMEAR当MP阶数。0为Gaussian展宽；不照搬其他软件枚举。 |
| `DFT.NEDOS` | integer | 301 | Gaussian原生DOS采样点；需至少2点且与ISMEAR0相关。其他值/模式不自动获得有效DOS。见[DOS](../topics/dos.md)。 |
| `DFT.SIGMA` | real，裸Ha | 0.007 | 展宽参数；使用正且有限的物理值，零或非法输入不安全。 |
| `DFT.tot_charge` | real，电子电荷数 | 0 | 总电子数=UPF价电子和减此值，正值移除电子。 |
| `DFT.VLOC_RCUT` | 带长度单位的real | 10 Bohr | 普通NC局域势相关径向截断；有限且>=0，0为完整径向范围的参考选择，不等于非局域/Hubbard截断。 |

自动带数参考规则可表为：先将电子数的一半乘1.2，向零取整后加1，与4取较大值，再受最小基组容量限制；ISPIN不为1时再倍增。需精确控制目标态数时显式给NBAND并核对日志，不把自动规则当固定占据证据。

## PWRS、滤波与预条件

| 键 | 类型/单位 | 参考默认 | 含义与限制 |
| --- | --- | --- | --- |
| `DFT.LPRECOND` | logical | F | 不是PWRS 实空间预处理接口，不推荐加入新的实空间预处理输入；FFT_BOX要求F。旧输入见[兼容性](../topics/legacy-parameters.md)。 |
| `DFT.RS.PRECONDITIONER` | integer | 0 | 0恒等、1邻域、2周期动能、3选项3、4选项4。2需磁FFT适用条件；3需零有效磁通，4需Bfield与参考规范；3/4限ALGO4、单band池。 |
| `DFT.RS.GAPP.TAU` | real，裸原子单位约定 | 1.63 | 模式3参数；有限且>0，未启用时也可能校验。 |
| `DFT.RS.GAPP.WEIGHT` | real，裸原子单位约定 | 2.73 | 模式3参数；有限且>=0，不猜造独立SI单位。 |
| `DFT.RS.GAPP.DELTA` | real，裸原子单位约定 | 7.89 | 模式3参数；有限且>0，不是DFT.delta_tau。 |
| `DFT.RS.MAGNETIC_GAUSSIAN.TIME` | real，裸Ha^-1 | 0.18818924310286425 | 模式4的TIME调用参数；有限且>0，不是MD时间步。 |
| `DFT.RS.MAGNETIC_GAUSSIAN.AMPLITUDE` | real，裸Ha^-1 | 7.02028330509751 | 模式4的AMPLITUDE调用参数；有限且>=0。 |
| `DFT.RS.MAGNETIC_GAUSSIAN.LOCAL` | real，裸Ha^-1 | 0.10093129881850713 | 模式4的LOCAL调用参数；有限且>0，默认值不是材料精度保证。 |
| `DFT.RS.kinetic` | logical | 普通PW F；完整RS T | 普通PW的实空间动能替代不等于完整RS；RS中显式F不改变强制选择。 |
| `DFT.RS.vnl` | logical | 普通PW F；完整RS T | 非局域实空间替代；完整RS中为T。滤波与赝势/SOC限制需单独核对。 |
| `DFT.RS.MD` | integer | 5 | 有限差分半宽，参考支持1..5；不是分子动力学。网格至少需能容纳相应模板，警告不等于自动修复。 |
| `DFT.RS.FILTER` | integer | 0 | vnl实空间设置适用时：0原始、1滤波选项1、2滤波选项2、3零通量双网格。1..3参考不支持SOC，3不支持有限通量；0不证明无aliasing。 |
| `DFT.RS.DENSITY_FFT_BOX` | logical | F | 专用磁RS能量流程，受下述严格限制；不是一般PW/PWRS精度选项。 |
| `DFT.RS.GRID_NX` | integer | 0 | 仅FFT_BOX显式网格；三维全0或全>=2，不能只设置一维。 |
| `DFT.RS.GRID_NY` | integer | 0 | 同NX。 |
| `DFT.RS.GRID_NZ` | integer | 0 | 同NX。 |

FFT_BOX参考限制包括磁RS、支持规范、SCF_ONLY、ISPIN1、ALGO4、单band池、预条件0、LPRECOND F、线性混合且系数有限/在(0,1]、局域NC/无非局域投影/无NLCC、Slater/PZ LDA，以及禁止多数输出、重启及其他工作流。显式网格全0表示采用截断相关网格；全>=2时才是显式三维网格。使用前需要对应发行资料或已验证输入，不能从单个参数可读推断整个组合可用。

## 常用块

| 块 | 形状 | 参考缺省 | 单位与边界 |
| --- | --- | --- | --- |
| `kgrid_Monkhorst_Pack` | 三行，每行3整数+1实数 | 单位矩阵，零偏移，即Gamma | 三行完整提供；路径能带BandLines优先。 |
| `DFT.MAGMOM` | 每原子一行3实数 | 每原子(0,0,1) | ISPIN!=1时使用，常用mu_B约定；按目标磁态给定，不证明最终基态。 |
| `DFT.Efield` | 一行3实数 | (0,0,0.001) | 仅LEfield T时，裸原子单位Ha/(e Bohr)，默认非零。 |
| `Zfield` | 一行3实数 | (0,0,0)，并警告 | 裸Tesla；块名无DFT前缀。luseBasZ适用时独立块不决定该值。 |
| `pseudo_pot_files` | 每物种一行文件名 | 必需，无默认文件 | 普通PW/PWRS必须有；顺序对应物种。使用工作目录本地文件名，并核对实际UPF元数据。 |

普通SCF、能带与+U文件交接见[PW指南](../modules/pw.md)。任何默认、合法整数或文件生成都不能单独证明支持、收敛或精度。
