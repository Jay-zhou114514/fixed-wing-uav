# fixed-wing-uav

固定翼无人机在风扰下的航迹可执行性研究（大创项目二）。

**工作名称**：固定翼无人机风扰下航迹可执行性的失效边界与最小修复
**一句话**：固定翼的最小转弯半径在有风时不是常数，顺风与逆风可以差三倍以上；
用常数半径做避障规划，等价于在空气坐标系里做安全校验，而真正的安全边界在地面坐标系里。

## 目录

| 位置 | 作用 |
| --- | --- |
| `docs/plans/RESEARCH_PLAN_v1.0.md` | 研究计划主文件（唯一真相源） |
| `docs/plans/CHANGELOG.md` | 计划版本变更记录 |
| `experiments/README.md` | 实验注册表，编号 EXP-FW-V1-0X，永不复用 |
| `experiments/EXP-FW-V1-0X-*.md` | 单次实验的预注册、结果、三层次报告 |
| `src/` | 仿真、规划、评价、作图的代码 |
| `outputs/` | CSV、图、日志、报告（可复现产物） |

## 复现

```powershell
python -m pip install -r requirements.txt
python src/exp_fw_v1_02_turn_geometry.py
```

## 与项目一的关系

项目一 `motor-health-monitor` 提供方法规范：预注册、训练集独立选参、
证据等级 A–D、三层次报告（观察/解释/局限）、失败保留、版本化计划。
本项目沿用同一套规范，但研究对象从振动信号换成固定翼运动几何。

## 状态

见 `PROJECT_STATUS.md`。当前：v1.0 计划完成，EXP-FW-V1-02 已产生首批可验证结果。
