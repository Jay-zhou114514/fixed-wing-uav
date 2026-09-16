"""EXP-FW-V1-22: 接管响应延迟对缓冲余量的消耗。

预注册见 experiments/EXP-FW-V1-22-preregistration.md。
模型：延迟 tau_L 内保持航向直飞；之后以最大转弯率转向，直到地面速度
在关注方向上的分量 <= 0，随后保持航向。
方向取风向（EXP-FW-V1-21 已确认最坏需求出现在该方向）。
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
R = VA / OMEGA                      # = delta_u
T_PERIOD = 2.0 * np.pi / OMEGA
N_PSI = 361
N_T = 1600
TAU_MAX = 4.0

W_LIST = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
TAU_LIST = np.round(np.arange(0.0, TAU_MAX + 1e-9, 0.1), 2)

PSI0 = np.linspace(0.0, 2 * np.pi, N_PSI, endpoint=False)[:, None]   # (P,1)


def required_along_wind(w, tau_L, phi_w=0.0):
    """沿风向方向的最坏穿透量。"""
    n = np.array([np.cos(phi_w), np.sin(phi_w)])
    W = w * VA * n
    t = np.linspace(0.0, tau_L + T_PERIOD, N_T)[None, :]             # (1,T)
    s = np.maximum(0.0, t - tau_L)                                   # (1,T)
    straight = np.minimum(t, tau_L)                                  # (1,T)

    best = None
    for sign in (+1, -1):
        psi = PSI0 + sign * OMEGA * s                                # (P,T)
        w_hat = np.cos(phi_w)
        dx = (VA * np.cos(PSI0) * straight
              + sign * R * (np.sin(psi) - np.sin(PSI0))
              + W[0] * t)
        dy = (VA * np.sin(PSI0) * straight
              - sign * R * (np.cos(psi) - np.cos(PSI0))
              + W[1] * t)
        proj_d = dx * n[0] + dy * n[1]
        proj_v = (VA * np.cos(psi) + W[0]) * n[0] + (VA * np.sin(psi) + W[1]) * n[1]

        mask = proj_v <= 0.0
        any_hit = mask.any(axis=1)
        idx = np.argmax(mask, axis=1)
        idx = np.where(any_hit, idx, N_T - 1)
        rmax = np.maximum.accumulate(proj_d, axis=1)
        val = rmax[np.arange(N_PSI), idx]
        val = np.where(any_hit, val, 1e9)
        best = val if best is None else np.minimum(best, val)
    return float(np.max(best))


def delta_d(w):
    return 0.0 if w <= 0 else R * np.sqrt(1.0 - w**2) + w * R * np.arccos(-w)


def rough_tau_star(w):
    return R / (VA * (1.0 + w))


def main():
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("outputs/figures", exist_ok=True)

    # H1: tau_L = 0 应复现 EXP-21
    h1 = []
    for w in W_LIST:
        req = required_along_wind(w, 0.0)
        dd = delta_d(w)
        if dd > 0:
            h1.append(abs(req - dd) / dd)
    print(f"H1 (τL=0 时 required == δd): 最大相对偏差 = {max(h1):.5f}")

    rows = []
    for w in W_LIST:
        dd = delta_d(w)
        given = R + dd
        prev = None
        tau_star = None
        for tau in TAU_LIST:
            req = required_along_wind(w, float(tau))
            margin = given - req
            if prev is not None and req < prev - 1e-9 and tau_star is None:
                print(f"    [异常] w={w} τL={tau} 出现非单调")
            prev = req
            if tau_star is None and margin <= 0:
                tau_star = float(tau)
            rows.append({"w": w, "tau_L_s": float(tau), "delta_d_m": dd,
                         "given_m": given, "required_m": req, "margin_m": margin,
                         "tau_star_s": tau_star})
        rough = rough_tau_star(w)
        rows_w = [r for r in rows if r["w"] == w]
        print(f"  w={w:.1f}: δu={R:.2f} δd={dd:>6.2f} given={given:>7.2f} | "
              f"τL*={tau_star if tau_star is not None else '>4s'}  "
              f"粗估 δu/[Va(1+w)]={rough:.2f}s")

    with open("outputs/exp_fw_v1_22_latency.csv", "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)

    print()
    print("### 临界延迟 τL* 与粗估对比 (H4)")
    for w in W_LIST:
        ts = next((r["tau_star_s"] for r in rows if r["w"] == w and r["tau_star_s"] is not None), None)
        rough = rough_tau_star(w)
        if ts is None:
            print(f"  w={w:.1f}: τL* > {TAU_MAX}s（粗估 {rough:.2f}s）")
        else:
            print(f"  w={w:.1f}: τL* = {ts:.1f} s，粗估 {rough:.2f} s，相对偏差 {abs(ts-rough)/rough*100:.1f}%")

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    for w in W_LIST:
        rw = [r for r in rows if r["w"] == w]
        ax[0].plot([r["tau_L_s"] for r in rw], [r["required_m"] for r in rw], label=f"w={w:.1f}")
        ax[1].plot([r["tau_L_s"] for r in rw], [r["margin_m"] for r in rw], label=f"w={w:.1f}")
    ax[0].set_xlabel("reaction latency τL (s)"); ax[0].set_ylabel("required buffer (m)")
    ax[0].set_title("required buffer vs latency (along wind)"); ax[0].grid(alpha=0.3); ax[0].legend(fontsize=8)
    ax[1].axhline(0, color="r", ls="--", lw=1)
    ax[1].set_xlabel("reaction latency τL (s)"); ax[1].set_ylabel("margin = given - required (m)")
    ax[1].set_title("margin consumption by latency"); ax[1].grid(alpha=0.3); ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("outputs/figures/exp_fw_v1_22_latency.png", dpi=160)
    print("wrote outputs/exp_fw_v1_22_latency.csv and figure")


if __name__ == "__main__":
    main()
