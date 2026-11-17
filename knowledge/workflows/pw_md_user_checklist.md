# Si：七组原生 PW 分子动力学：用户操作检查单

结合[完整教程](pw_md.md)和[状态机](pw_md_state_machine.md)使用；勾选必须对应实际证据。

- [ ] 选择七组之一与演示/生产目标；证据路径/缺项：______。
- [ ] 实际2或64原子Si结构、Si UPF、28.086amu；证据路径/缺项：______。
- [ ] Gamma/20Ha/真实初态与对应ensemble候选；证据路径/缺项：______。
- [ ] dt/步数/温压/恒温器，requested与effective；证据路径/缺项：______。
- [ ] 1/1池、初速、电子设置与三层控制检查；证据路径/缺项：______。
- [ ] 已有授权时以用户已知launcher独立运行；证据路径/缺项：______。
- [ ] 逐步SCF、退出、N+1完整帧、ensemble观测量；证据路径/缺项：______。
- [ ] 统计窗、来源、thermo3旧失败与新输入未验证分开；证据路径/缺项：______。

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

历史边界见[run notes](pw_md_run_notes.md)；无法获得的事实保留unknown，不填写假定成功结果。
