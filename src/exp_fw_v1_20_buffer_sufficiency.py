"""EXP-FW-V1-20: JAIS 2020 缓冲构造的充分性检验（支持函数法）。

背景：Stevens & Atkins (2020), "Generating Airspace Geofence Boundary Layers in Wind",
JAIS 17(2), doi:10.2514/1.I010792。该文给出
    δu = Va/omega                （均匀缓冲 = 转弯半径）
    δd = R*sqrt(1-w^2) + w*R*arccos(-w)   （方向缓冲，沿风向）
本实验检验：真实可达集（有最小转弯半径的固定翼，常值风，最大转弯率）
是否被构造 δu ⊕ 单向 δd 所包含。

方法：对凸集 C，S ⊆ C 当且仅当对一切方向 n 有 h_S(n) <= h_C(n)（支持函数比较）。
      h_S(n) 用数值最坏情况求得：对初始航向取最坏、对转弯方向取最优。

自检：w = 0 时需求应恒等于 R。
"""
from __future__ import annotations

import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

VA = 18.0
OMEGA = np.deg2rad(25.0)
R = VA / OMEGA
T_PERIOD = 2.0 * np.pi / OMEGA
N_ANGLES = 361
N_PSI = 289
N_T = 4000


def _t():
    return np.linspace(0.0, T_PERIOD, N_T)


T = _t()


def displacement(psi0, sign, w, phi_w):
    """地面系位移（相对出发点）。sign=+1 左转，-1 右转。

    注意：积分 int cos(a + b t) dt = sin(a+bt)/b，b = sign*OMEGA，
    因此位移里必须带 sign 因子。
    """
    W = w * VA * np.array([np.cos(phi_w), np.sin(phi_w)])
    psi = psi0 + sign * OMEGA * T
    dx = sign * R * (np.sin(psi) - np.sin(psi0)) + W[0] * T
    dy = -sign * R * (np.cos(psi) - np.cos(psi0)) + W[1] * T
    return np.stack([dx, dy], axis=-1)


def required_support(w, phi_w):
    """最坏初始航向下、控制器可选最优转弯方向时，各方向所需缓冲。"""
    angs = np.linspace(0.0, 2 * np.pi, N_ANGLES, endpoint=False)
    N = np.stack([np.cos(angs), np.sin(angs)], axis=-1)
    req = -1e9 * np.ones(N_ANGLES)
    for psi0 in np.linspace(0.0, 2 * np.pi, N_PSI, endpoint=False):
        a = (displacement(psi0, +1, w, phi_w) @ N.T).max(axis=0)
        b = (displacement(psi0, -1, w, phi_w) @ N.T).max(axis=0)
        req = np.maximum(req, np.minimum(a, b))
    return angs, req


def paper_support(w, phi_w, angs):
    """论文构造 δu 全向 + δd 沿风向的支持函数。w=0 时无方向缓冲。"""
    if w <= 0:
        d_d = 0.0
    else:
        d_d = R * np.sqrt(1.0 - w**2) + w * R * np.arccos(-w)
    sup = R + d_d * np.maximum(0.0, np.cos(angs - phi_w))
    return sup, d_d


def main():
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("outputs/figures", exist_ok=True)

    # 自检
    _, req0 = required_support(0.0, 0.0)
    assert abs(req0.max() - R) < 0.01 * R, "w=0 自检失败"
    print(f"自检通过: w=0 时最大需求 {req0.max():.3f} m, R = {R:.3f} m")

    rows = []
    for w in np.round(np.arange(0.0, 0.501, 0.01), 2):
        angs, req = required_support(float(w), 0.0)
        sup, d_d = paper_support(float(w), 0.0, angs)
        gap = req - sup
        j = int(np.argmax(gap))
        rows.append({
            "w": float(w),
            "Vw_m_s": float(w) * VA,
            "delta_d_m": d_d,
            "max_required_m": float(req.max()),
            "max_required_over_R": float(req.max() / R),
            "max_gap_m": float(max(0.0, gap[j])),
            "gap_direction_deg": float(np.degrees(angs[j])),
            "worst_dir_required_m": float(req[j]),
            "worst_dir_paper_m": float(sup[j]),
        })

    with open("outputs/exp_fw_v1_20_buffer_sufficiency.csv", "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)

    pos = [r for r in rows if r["max_gap_m"] > 0.5]
    w_star = pos[0]["w"] if pos else None
    print(f"首个出现缺口(>0.5 m)的 w* = {w_star}")
    for r in rows:
        print(f"  w={r['w']:.2f} Vw={r['Vw_m_s']:>4.1f} m/s  δd={r['delta_d_m']:>6.2f}  "
              f"需求={r['max_required_m']:>7.2f} ({r['max_required_over_R']:.3f}R)  "
              f"缺口={r['max_gap_m']:>6.2f} m @ {r['gap_direction_deg']:.0f}°")

    ws = [r["w"] for r in rows]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    ax[0].plot(ws, [r["max_gap_m"] for r in rows], "o-", ms=3)
    ax[0].set_xlabel("wind ratio  w = Vw / Va")
    ax[0].set_ylabel("max gap (m)")
    ax[0].set_title("JAIS-2020 buffer vs required: worst-case deficit")
    ax[0].grid(alpha=0.3)
    if w_star is not None:
        ax[0].axvline(w_star, color="r", ls="--", lw=1, label=f"w* = {w_star:.2f}")
        ax[0].legend()
    ax[1].plot(ws, [r["max_required_over_R"] for r in rows], label="required / R")
    ax[1].plot(ws, [1 + r["delta_d_m"] / R for r in rows], "--", label="paper: 1 + δd/R")
    ax[1].set_xlabel("wind ratio w")
    ax[1].set_ylabel("normalized buffer")
    ax[1].set_title("required vs published buffer (along wind axis)")
    ax[1].grid(alpha=0.3)
    ax[1].legend()
    fig.tight_layout()
    fig.savefig("outputs/figures/exp_fw_v1_20_buffer_sufficiency.png", dpi=160)
    print("wrote outputs/exp_fw_v1_20_buffer_sufficiency.csv and figure")


if __name__ == "__main__":
    main()
