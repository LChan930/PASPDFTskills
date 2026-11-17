# 原生 DFT 主输入

`lattice_model.fdf`

选择 Model DFT、设置 DFT.* 和必要块，并通过 %include 引入真实结构及拆分输入。逐项追踪 include，重复键和未引用的同目录结构都需核查；不要按文件名决定结构。

详细规则见 [对应参考](../topics/input-generation.md)。
