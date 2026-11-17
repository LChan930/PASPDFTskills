# 已有输出：日志、能带、能级、DOS 与 MD：用户操作检查单

结合[完整教程](output_analysis.md)和[状态机](output_analysis_state_machine.md)使用；勾选必须对应实际证据。

- [ ] 按内容识别用户已有日志/谱/DOS/MD；证据路径/缺项：______。
- [ ] 只读文件哈希、配对来源与缺失项；证据路径/缺项：______。
- [ ] 选分析对象、输出目录与表号；证据路径/缺项：______。
- [ ] 单位/参考/占据/自旋/权重与语言；证据路径/缺项：______。
- [ ] 核对解析格式与命令选项，无输入晋级要求；证据路径/缺项：______。
- [ ] 执行已授权本地分析，写用户新产物；证据路径/缺项：______。
- [ ] 场图已显式选 `--mode slice`（单平面体密度）或 `--mode project`（整胞层积分面密度），记录省略轴、切片位置/积分范围；未由单层材料推断模式。证据路径/缺项：______。
- [ ] 若要求逐物理层积分，已定义层边界并说明当前脚本未实现有限层窗口；全胞积分未冒充逐层结果。证据路径/缺项：______。
- [ ] 核对JSON、图/计数/单位与原始证据一致；场图的量、色标单位、`representation` 与 `integration_scope` 匹配，切片未标成面密度。证据路径/缺项：______。
- [ ] 交付报告图、来源、unknown和限制；证据路径/缺项：______。

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

历史边界见[run notes](output_analysis_run_notes.md)；无法获得的事实保留unknown，不填写假定成功结果。
