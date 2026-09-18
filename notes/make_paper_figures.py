"""生成会议论文的三张主图（投稿前待办第 3 项）。

Fig 1: 拐角几何示意 —— 顶点内角 θ、穿透量 R·cos(θ/2)、死区 d* = R·cot(θ/2)
Fig 2: w=0.3 时允许接管延迟随接近方向的极坐标图（方向依赖 5.1 倍）
Fig 3: 死区 d*/R 随内角 θ 的曲线（与 R·cot(θ/2) 吻合；w=0）

数据来源：
  Fig 2 ← outputs/exp_fw_v1_26_joint_latency.csv（EXP-26 臂 I）
  Fig 3 ← outputs/exp_fw_v1_26_critical_distance.csv（EXP-26 C 区）
"""
from __future__ import annotations

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = "docs/figures"
os.makedirs(OUT, exist_ok=True)

R = 41.252961249
VA = 18.0
OM = np.deg2rad(25.0)

plt.rcParams.update({
    "font.size": 10,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "figure.dpi": 200,
})

# ============================================================ Fig 1
print("[Fig 1] 拐角几何示意")
fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.2))

def draw_corner(ax, theta_deg, title):
    th = np.deg2rad(theta_deg)
    # 顶点在原点；两条边沿 +x 与 θ 方向的**向内**方向展开
    L = 2.6
    a = np.array([1.0, 0.0])
    b = np.array([np.cos(th), np.sin(th)])
    # 围栏区域在角内
    ax.plot([0, L * a[0]], [0, L * a[1]], "k-", lw=2)
    ax.plot([0, L * b[0]], [0, L * b[1]], "k-", lw=2)
    ax.fill_between([0, L, L * b[0], 0], [0, 0, L * b[1], 0],
                    color="0.92", zorder=0)

    # 向内分角线
    bis = (a + b) / np.linalg.norm(a + b)
    d_star = 1.0 / np.tan(th / 2)          # 以 R 为单位
    ax.plot([0, (d_star + 0.55) * bis[0]], [0, (d_star + 0.55) * bis[1]],
            "--", color="tab:blue", lw=1.4, label=r"interior bisector")
    # 死区（d* 以内，零延迟即越界）
    ax.plot([0, d_star * bis[0]], [0, d_star * bis[1]],
            color="tab:red", lw=3.2, solid_capstyle="butt",
            label=r"dead zone $d^*=R\cot(\theta/2)$")
    ax.plot([d_star * bis[0]], [d_star * bis[1]], "o", color="tab:red", ms=5)

    # 转弯圆：半径 1（单位 R），圆心在分角线上距顶点 d* 处
    c = d_star * bis
    ang = np.linspace(0, 2 * np.pi, 400)
    ax.plot(c[0] + np.cos(ang), c[1] + np.sin(ang), "-",
            color="tab:green", lw=1.6, label=r"turning circle ($R$)")
    ax.plot([c[0]], [c[1]], "+", color="tab:green", ms=8)

    ax.set_aspect("equal")
    ax.set_xlim(-0.15, 2.5)
    ax.set_ylim(-0.15, 2.5)
    ax.set_title(title)
    ax.set_xlabel("x / R")
    ax.set_ylabel("y / R")

    # 标注角度
    ax.annotate(r"$\theta$", xy=(0.62, 0.10), fontsize=13, color="k")
    mid = 0.5 * np.deg2rad(theta_deg)
    ax.annotate("", xy=(0.5 * np.cos(mid * 0), 0.5 * 0), xytext=(0, 0))
    return ax

ax = axes[0]
draw_corner(ax, 90.0, r"(a) $\theta = 90^\circ$:  $d^* = R$")
ax.legend(loc="upper right", fontsize=8, framealpha=0.95)

ax = axes[1]
th = np.deg2rad(60.0)
L = 2.6
a = np.array([1.0, 0.0]); b = np.array([np.cos(th), np.sin(th)])
ax.plot([0, L*a[0]], [0, L*a[1]], "k-", lw=2)
ax.plot([0, L*b[0]], [0, L*b[1]], "k-", lw=2)
bis = (a+b)/np.linalg.norm(a+b)
d_star = 1.0/np.tan(th/2)
ax.plot([0, (d_star+0.55)*bis[0]], [0, (d_star+0.55)*bis[1]], "--",
        color="tab:blue", lw=1.4)
ax.plot([0, d_star*bis[0]], [0, d_star*bis[1]], color="tab:red", lw=3.2,
        solid_capstyle="butt")
ax.plot([d_star*bis[0]], [d_star*bis[1]], "o", color="tab:red", ms=5)
c = d_star*bis
ang = np.linspace(0, 2*np.pi, 400)
ax.plot(c[0]+np.cos(ang), c[1]+np.sin(ang), "-", color="tab:green", lw=1.6)
ax.plot([c[0]], [c[1]], "+", color="tab:green", ms=8)
ax.set_aspect("equal"); ax.set_xlim(-0.15, 2.5); ax.set_ylim(-0.15, 2.5)
ax.set_title(r"(b) $\theta = 60^\circ$:  $d^* = 1.732R$")
ax.set_xlabel("x / R"); ax.set_ylabel("y / R")
ax.annotate(r"$\theta$", xy=(0.72, 0.24), fontsize=13)

fig.suptitle("Corner geometry: dead zone and turning circle", y=1.0)
fig.tight_layout()
fig.savefig(f"{OUT}/fig1_corner_geometry.png", bbox_inches="tight")
plt.close(fig)
print(f"  -> {OUT}/fig1_corner_geometry.png")

# ============================================================ Fig 2
print("[Fig 2] 方向依赖的允许延迟（极坐标）")
rows = []
with open("outputs/exp_fw_v1_26_joint_latency.csv", newline="", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["zone"] == "A1R" and abs(float(r["w"]) - 0.3) < 1e-9:
            rows.append((float(r["psi_deg"]), float(r["tau_analytic"])))
rows.sort()
psi = np.deg2rad([r[0] for r in rows])
tau = np.array([r[1] for r in rows])

# 闭合曲线
psi_c = np.append(psi, psi[0] + 2*np.pi)
tau_c = np.append(tau, tau[0])

fig = plt.figure(figsize=(6.6, 6.0))
ax = fig.add_subplot(111, projection="polar")
ax.plot(psi_c, tau_c, "-o", lw=2, ms=5, color="tab:blue")
ax.fill(psi_c, tau_c, alpha=0.15, color="tab:blue")
ax.set_theta_zero_location("E")
ax.set_theta_direction(1)
ax.set_title(r"Admissible handover latency $\tau_{crit}$ vs approach "
             r"direction ($w=0.3$)", pad=18)
ax.set_rlabel_position(135)
for p, t in zip(psi, tau):
    ax.annotate(f"{t:.2f}", xy=(p, t), xytext=(p, t + 0.75),
                fontsize=7.5, ha="center")
# 风向箭头
ax.annotate("", xy=(0.0, 13.4), xytext=(-0.28, 13.4),
            arrowprops=dict(arrowstyle="->", lw=2, color="tab:red"))
ax.text(0.03, 13.6, "wind", color="tab:red", fontsize=9)
ax.text(np.deg2rad(270), 12.6, f"min {tau.min():.2f} s",
        fontsize=8.5, color="tab:red", ha="center")
ax.text(np.deg2rad(120), 12.6, f"max {tau.max():.2f} s",
        fontsize=8.5, color="tab:green", ha="center")
fig.tight_layout()
fig.savefig(f"{OUT}/fig2_directional_latency.png", bbox_inches="tight")
plt.close(fig)
print(f"  -> {OUT}/fig2_directional_latency.png  (max/min = {tau.max()/tau.min():.2f})")

# ============================================================ Fig 3
print("[Fig 3] 死区 d*/R 随内角 θ（w=0）")
recs = []
with open("outputs/exp_fw_v1_26_critical_distance.csv", newline="",
          encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if abs(float(r["w"])) < 1e-12 and abs(float(r["va"]) - 18.0) < 1e-9:
            recs.append((float(r["theta_deg"]), float(r["ratio"])))
recs.sort()
th_deg = np.array([r[0] for r in recs])
ratio = np.array([r[1] for r in recs])

fig, ax = plt.subplots(figsize=(6.4, 4.4))
th_fine = np.linspace(45, 175, 400)
ax.plot(th_fine, 1.0/np.tan(np.deg2rad(th_fine)/2), "-", lw=2,
        color="tab:red", label=r"$d^*/R = \cot(\theta/2)$")
ax.plot(th_deg, ratio, "o", ms=8, mfc="none", mew=2,
        color="tab:blue", label="measured (EXP-26 zone C, $w=0$)")
for x, y in zip(th_deg, ratio):
    ax.annotate(rf"$n={int(360/(180-x))}$", xy=(x, y), xytext=(x - 7, y + 0.06),
                fontsize=8, color="tab:blue")
ax.axhline(1.0, color="0.6", ls=":", lw=1)
ax.axvline(90, color="0.6", ls=":", lw=1)
ax.text(91, 1.62, r"$\theta=90^\circ \Rightarrow d^*=R$", fontsize=8.5, color="0.35")
ax.set_xlabel(r"interior angle $\theta$ (deg)")
ax.set_ylabel(r"$d^*/R$")
ax.set_title(r"Corner dead-zone length: depends on interior angle alone")
ax.legend(fontsize=9)
ax.set_xlim(50, 170)
fig.tight_layout()
fig.savefig(f"{OUT}/fig3_deadzone_vs_theta.png", bbox_inches="tight")
plt.close(fig)
print(f"  -> {OUT}/fig3_deadzone_vs_theta.png  "
      f"(max |measured − cot| = {np.max(np.abs(ratio - 1/np.tan(np.deg2rad(th_deg)/2))):.2e})")
print("\n三张图已生成。")
