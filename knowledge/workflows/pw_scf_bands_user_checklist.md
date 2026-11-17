# BaTiO3：从 SCF 到能带：用户操作检查单

结合[完整教程](pw_scf_bands.md)和[状态机](pw_scf_bands_state_machine.md)使用；勾选必须对应实际证据。

- [ ] 明确五原子BaTiO3的SCF或路径能带目标；证据路径/缺项：______。
- [ ] Ba/Ti/O UPF与siesta.ANI闭包；证据路径/缺项：______。
- [ ] 6³积分SCF候选与LCHARG1；证据路径/缺项：______。
- [ ] 35Ha/电子阈值/资源与目标路径；证据路径/缺项：______。
- [ ] 核对物种、实际k点池与SCF候选；证据路径/缺项：______。
- [ ] 已有授权时运行SCF并移交合法配对到bands；证据路径/缺项：______。
- [ ] SCF参考、谱迭代、TB内容分别通过；证据路径/缺项：______。
- [ ] 图/JSON/采样能隙限制与来源交付；证据路径/缺项：______。

- [ ] UPF是否由用户合法提供？物种顺序、文件精确名、SHA-256、XC/相对论/价电子与manifest一致；缺项继续标记不完整。
- [ ] 输入静态检查、初始化、退出、电子求解、阶段完成、物理精度是否分别记录，未将文件存在当作收敛？
- [ ] 当前产物和历史观察分开，未宣称新计算已经执行；图题保持科学内容，限制放文字/JSON。
- [ ] 报告默认English；需中文时显式选择zh-Hans/zh-Hant。原始文件未覆盖，结果在用户目录。

交接记录可直接填写：

```text
Status / Route / Branch / Stage:
Run ID / input and include hashes:
UPF filenames and hashes / missing dependencies:
Accepted settings / changes and purpose:
Command / MPI ranks / actual k count / pools:
Output paths / hashes / convergence and completeness evidence:
Historical observations kept separate:
Unknown / failed / next permitted action:
```

历史边界见[run notes](pw_scf_bands_run_notes.md)；无法获得的事实保留unknown，不填写假定成功结果。
