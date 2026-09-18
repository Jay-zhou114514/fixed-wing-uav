"""P1 附：JAIS δd 在 w=0 处的连续性核查（关键：区分"公式性质"与"我们的守卫"）。

JAIS 2020 第 II 节把 δd 定义为**转弯轨迹最大前向位移**：
    x(t) = R sin(ωt) + Vw t,   y(t) = −R cos(ωt)
    ẋ(t) = 0 ⟹ cos(ωt*) = −w ⟹ t* = arccos(−w)/ω
    δd = x(t*) = R√(1−w²) + (Vw/ω)·arccos(−w)

因此 δd 在 w=0 处**是连续的**，值为 R（四分之一转处 x = R）。

而我们的七个实现都写 `delta_d(w<=0) = 0`（物理直觉：无风则无方向偏移）。
于是**构造层**（δu + δd·max(0, n·d_wind)）在 w=0 处不连续。

本脚本量化该不连续，并判定其影响范围：
  - 若 δd(w→0+)/R → 1（而非 0），则 w=0 与任意小 w>0 之间的缓冲相差近 R。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parent.parent / "src" / "exp_fw_v1_26_joint_latency.py"
spec = importlib.util.spec_from_file_location("j26", SRC)
J = importlib.util.module_from_spec(spec)
sys.modules["j26"] = J
spec.loader.exec_module(J)

R, VA, OMEGA = J.R, J.VA_DEFAULT, J.OMEGA


def dd_jais(w):
    """JAIS 原文公式，不加任何守卫。"""
    return R * np.sqrt(1.0 - w * w) + w * R * np.arccos(-w)


print("=" * 96)
print("JAIS δd 在 w=0 处的连续性核查")
print("=" * 96)
print(f"R = {R:.6f} m")
print()
print(f"{'w':>12}{'δd (JAIS 原文)':>18}{'δd/R':>10}{'δd (我们的代码)':>18}{'缓冲 δu+δd':>14}")
print("-" * 96)
for w in (0.0, 1e-9, 1e-6, 1e-4, 1e-3, 1e-2, 0.1, 0.3, 0.5):
    dj = dd_jais(w)
    dc = J.delta_d(w)
    buf = R + dj
    print(f"{w:>12.0e}{dj:>18.6f}{dj/R:>10.6f}{dc:>18.6f}{buf:>14.6f}")
print()
print("  判读：")
print(f"   - JAIS 公式在 w→0+ 的极限 = R = {R:.4f} m（**不是 0**）")
print(f"   - 我们的代码在 w=0 取 0（守卫），在 w=1e-6 取 {J.delta_d(1e-6):.4f} m")
print(f"   - 故构造层缓冲在 w=0 处：{R:.4f} m；在 w→0+ 处：{R + dd_jais(1e-9):.4f} m")
print(f"     跳变因子 ≈ {2.0:.3f}（几乎翻倍）")
print()
print("=" * 96)
print("与 EXP-26 观察值的关系")
print("=" * 96)
_V0, *_ = J.setup_rect(0.0)
L_HALF = float(np.abs(_V0[:, 0]).max())
RHO0 = L_HALF - R
print(f"  位置 = 缩放层迎风边中点外 1R；rho0 = {RHO0:.6f} m")
t0 = RHO0 / VA
t0p = (RHO0 - R / 2.0) / VA
print(f"  tau(w=0)   = rho0/Va            = {t0:.6f} s   <- EXP-26 记录 6.0414")
print(f"  tau(w→0+)  = (rho0 - R/2)/Va    = {t0p:.6f} s   <- EXP-26 记录 5.2331 (w=0.1)")
print(f"  跳变       = R/(2Va)            = {R/(2*VA):.6f} s")
print()
print("  => EXP-26 表格中 '6.0414 (w=0) -> 5.2331 (w=0.1)' 的下降，")
print("     正是该分支跳变；w>0 段（0.1 -> 0.5: 5.233 -> 6.148 -> 7.698）为单调上升。")
print()
print("=" * 96)
print("影响范围判定：是否有已登记结论被污染？")
print("=" * 96)
checks = [
    ("EXP-26 臂 I 方向依赖 5.1 倍（w=0.3 单点）", "不受影响：单 w，无跨分支比较"),
    ("K1 τL* = 1/(ω(1+w))", "不受影响：独立于本构造的缓冲分支"),
    ("K2/K3 裕度方向结构", "不受影响：逐 w 独立计算"),
    ("K5 δd 精确最坏穿透量（w>0）", "不受影响：w>0 域内"),
    ("K8/K9 拐角律", "不受影响：纯几何，与 δd 分支无关"),
    ("H2 空速无关", "不受影响"),
    ("H3 滚转等效延迟", "不受影响：w=0.3/0.5 单点比较"),
    ("v1.4 的 P1 '非单调性' 提法", "**需更正**：非物理现象，为 w=0 分支跳变"),
]
for a, b in checks:
    print(f"  - {a}")
    print(f"      {b}")
