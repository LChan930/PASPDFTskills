# 应用日志与调度输出

`logs`

PASP 没有指定的应用日志后缀。根据内容识别启动、电子迭代、SCF/能带结果和 MD 结束；调度 stdout/stderr 可能只保存脚本消息。多份日志需按实际输入和初态匹配；重复 MPI 错误与唯一失败步分开计数。

详细规则见 [对应参考](../topics/output-analysis.md)。
