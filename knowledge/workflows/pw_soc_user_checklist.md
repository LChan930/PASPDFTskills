# Bi2Se3：SR 与 FR 赝势比较：用户操作检查单

结合[完整教程](pw_soc.md)和[状态机](pw_soc_state_machine.md)使用；勾选必须对应实际证据。

- [ ] 确定SR或FR/SOC及当前阶段；证据路径/缺项：______。
- [ ] Bi/Se精确SR/FR UPF和相对论元数据；证据路径/缺项：______。
- [ ] ISPIN4/五零磁矩/RWIGS块候选；证据路径/缺项：______。
- [ ] SR30Ha/FR40Ha差异与比较目的；证据路径/缺项：______。
- [ ] UPF、XC/表示兼容、独立参考配对；证据路径/缺项：______。
- [ ] 已有授权时两分支分别SCF→bands；证据路径/缺项：______。
- [ ] 实际SOC激活、谱状态与TB；无结果维持input-only；证据路径/缺项：______。
- [ ] 报告数值对照差异，不声称已得SOC光谱；证据路径/缺项：______。

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

历史边界见[run notes](pw_soc_run_notes.md)；无法获得的事实保留unknown，不填写假定成功结果。
