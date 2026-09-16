# 工程路线图

与 `docs/plans/RESEARCH_PLAN_vX.Y.md` 的分工：
研究计划管**科学问题与证据**，路线图管**工程任务与代码结构**。

## 代码结构（目标）

```text
src/
  config.py                 参数唯一来源，禁止在脚本里写魔数
  fixedwing_core.py         运动学、地面曲率、可达几何
  scenarios.py              场景生成器（固定种子，train/val/test 分离）
  planner_lattice.py        航向格 A*（常半径运动基元）
  planner_dubins.py         解析 Dubins（6 族最短）
  tracker.py                纯追踪 / L1 制导
  metrics.py                成功率、间隙、偏差、代价
  experiment_runner.py      批量跑场景、写 CSV 与日志
  exp_fw_v1_0X_*.py         每个实验一个入口
tests/                      单元测试：几何、规划、度量、场景生成
outputs/                    CSV、图、日志、报告（可重新生成）
docs/figures/               进入 README 的少量展示图
```

## 工程任务顺序

1. 核心几何与单元测试（含解析式与数值互验）
2. 场景生成器（可复现、可指定种子）
3. 两个基线规划器 + 跟踪器
4. 度量管道与端到端跑通（EXP-FW-V1-01）
5. 批量实验与统计（EXP-FW-V1-03 起）

## 与 Motor 的工程差异

| 项目 | Motor | 本项目 |
| --- | --- | --- |
| 输入 | 公开数据集（外部，只读） | 程序化生成场景（自建，参数化） |
| 随机性 | 数据是固定的 | 种子与参数组合是实验变量，必须记录 |
| 可视化 | 波形与特征空间 | 航迹图、相图、极坐标足迹 |
| 复现成本 | 下载数据 + 跑脚本 | 跑脚本即可，但场景生成器本身必须被测试 |
