# 原生 PW/PWRS 真实输入模板

从[工作流目录](../workflows/pw_scf_bands.md)或本技能入口选择路线。所有末级模板都含实际FDF、实际include闭包、逐项说明与精确依赖manifest；共24组。输入未替换为占位结构。

**所有模板为input-derived、未做本次PASP运行，且需要用户合法提供UPF。** 密度/重启参考、+U占据、历史日志/轨迹不附。具体文件名/哈希/头元数据见各manifest。没有UPF或必要上游产物时不能声称开箱可跑。

教程：[BaTiO3 SCF/bands](../workflows/pw_scf_bands.md)、[NiO AFM/+U](../workflows/pw_spin_plus_u.md)、[Bi2Se3 SOC](../workflows/pw_soc.md)、[BaTiO3固定胞优化](../workflows/pw_relax.md)、[Graphene PWRS磁通](../workflows/pwrs_magnetic.md)、[Si七组MD](../workflows/pw_md.md)、[已有输出分析](../workflows/output_analysis.md)。

每个候选复制到用户新目录运行。PASP启动方式使用用户已验证命令，独立包不复制依赖外部共享路径的run.sh，不发明PASP参数。
