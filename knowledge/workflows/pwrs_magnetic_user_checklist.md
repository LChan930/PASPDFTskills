# Graphene：零磁通与有限磁通：用户操作检查单

结合[完整教程](pwrs_magnetic.md)和[状态机](pwrs_magnetic_state_machine.md)使用；勾选必须对应实际证据。

- [ ] 确定Bfield路径n0=0或1与SCF/band；证据路径/缺项：______。
- [ ] 同C UPF、同几何，闭包完整；证据路径/缺项：______。
- [ ] 20×20×1 SCF，保留本例选择器调用；证据路径/缺项：______。
- [ ] 场与默认表示、ALGO4/nb_pool1兼容性；证据路径/缺项：______。
- [ ] 实际k池/ranks与各分支独立配对；证据路径/缺项：______。
- [ ] 已有授权时先各SCF，通过才bands；证据路径/缺项：______。
- [ ] 核对新审计中两分支TB及四日志；退出与谱收敛分开；证据路径/缺项：______。
- [ ] 只比较通过同阶段验证的零/有限磁通结果；证据路径/缺项：______。

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

历史边界见[run notes](pwrs_magnetic_run_notes.md)；无法获得的事实保留unknown，不填写假定成功结果。
