# NiO：AFM 与 +U 分支：用户操作检查单

结合[完整教程](pw_spin_plus_u.md)和[状态机](pw_spin_plus_u_state_machine.md)使用；勾选必须对应实际证据。

- [ ] 确定LDA或+U以及SCF/bands；证据路径/缺项：______。
- [ ] Ni/O UPF、四原子AFM行顺序；证据路径/缺项：______。
- [ ] 独立两分支SCF，初始Ni ±2；证据路径/缺项：______。
- [ ] Ueff0.2Ha/3d/全部Ni与40总态；证据路径/缺项：______。
- [ ] 物种磁矩和+U记录数、池数、配对一致；证据路径/缺项：______。
- [ ] 已有授权时各分支SCF→bands，+U保留PLUS_U_NS；证据路径/缺项：______。
- [ ] 各自电子/谱收敛与+U激活证据；证据路径/缺项：______。
- [ ] 同条件比较，单writer-channel不冒充自旋分辨；证据路径/缺项：______。

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

历史边界见[run notes](pw_spin_plus_u_run_notes.md)；无法获得的事实保留unknown，不填写假定成功结果。
