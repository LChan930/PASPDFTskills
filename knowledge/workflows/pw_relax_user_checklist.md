# BaTiO3：固定晶胞离子优化：用户操作检查单

结合[完整教程](pw_relax.md)和[状态机](pw_relax_state_machine.md)使用；勾选必须对应实际证据。

- [ ] 选择polar_plus/cubic_reference/polar_minus；证据路径/缺项：______。
- [ ] Ba/Ti/O与各自结构，不互相覆盖；证据路径/缺项：______。
- [ ] 固定胞LRELAX+nstep或独立立方SCF；证据路径/缺项：______。
- [ ] 50步上限/负EDIFFG力阈值/网格差异；证据路径/缺项：______。
- [ ] 电子与离子阈值单位、质量、池数；证据路径/缺项：______。
- [ ] 已有授权时运行所选独立分支；证据路径/缺项：______。
- [ ] 逐步SCF、实际最大力、终止原因及末结构；证据路径/缺项：______。
- [ ] 最终结构→新SCF；比较前统一数值条件；证据路径/缺项：______。

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

历史边界见[run notes](pw_relax_run_notes.md)；无法获得的事实保留unknown，不填写假定成功结果。
