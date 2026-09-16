"""EXP-FW-V1-21: 缓冲充分性的修正判据检验。

修正点：机动时长不再固定为一整圈，而是"转弯至地面速度在关注方向上的分量 <= 0 为止"，
到达后保持航向。预注册见 experiments/EXP-FW-V1-21-preregistration.md。
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
N_ANGLES = 181
N_PSI = 181
N_T = 2000

T = np.linspace(0.0, T_PERIOD, N_T)
ANGS = np.linspace(0.0, 2 * np.pi, N_ANGLES, endpoint=False)
N = np.stack([np.cos(ANGS), np.sin(ANGS)], axis=-1)   # (A,2)
AR = np.arange(N_ANGLES)


def _state(psi0, sign, w, phi_w):
    W = w * VA * np.array([np.cos(phi_w), np.sin(phi_w)])
    psi = psi0 + sign * OMEGA * T
    dx = sign * R * (np.sin(psi) - np.sin(psi0)) + W[0] * T
    dy = -sign * R * (np.cos(psi) - np.cos(psi0)) + W[1] * T
    d = np.stack([dx, dy], axis=-1)
    v = np.stack([VA * np.cos(psi) + W[0], VA * np.sin(psi) + W[1]], axis=-1)
    return d, v


def _one_direction_set(d, v):
    """返回 (required, feasible)：达到 v.n<=0 前的最大位移。"""
    proj_d = d @ N.T                      # (T,A)
    proj_v = v @ N.T                      # (T,A)
    mask = proj_v <= 0.0                  # (T,A)
    any_hit = mask.any(axis=0)
    idx = np.argmax(mask, axis=0)         # 首个 True；若无 True 则为 0
    idx = np.where(any_hit, idx, N_T - 1)
    rmax = np.maximum.accumulate(proj_d, axis=0)
    return rmax[idx, AR], any_hit


def required_support(w, phi_w):
    req = -1e9 * np.ones(N_ANGLES)
    infeas = np.zeros(N_ANGLES, dtype=bool)
    for psi0 in np.linspace(0.0, 2 * np.pi, N_PSI, endpoint=False):
        vals = []
        fea = []
        for sign in (+1, -1):
            d, v = _state(psi0, sign, w, phi_w)
            val, ok = _one_direction_set(d, v)
            vals.append(val)
            fea.append(ok)
        vals = np.stack(vals)                                    # (2,A)
        # 对不可行方向设为大值，使 min 优先选可行方向
        vals = np.where(np.stack(fea), vals, 1e9)
        best = vals.min(axis=0)
        best = np.where(best > 1e8, np.nan, best)
        req = np.maximum(req, np.where(np.isnan(best), req, best))
        infeas |= np.isnan(best)
    return req, infeas


def delta_d(w):
    return 0.0 if w <= 0 else R * np.sqrt(1.0 - w**2) + w * R * np.arccos(-w)


def given_support(w, phi_w):
    d_d = delta_d(w)
    return R + d_d * np.maximum(0.0, np.cos(ANGS - phi_w)), d_d


def main():
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("outputs/figures", exist_ok=True)

    req0, _ = required_support(0.0, 0.0)
    h1 = abs(req0.max() - R) / R
    print(f"H1 自检 (w=0): required max={req0.max():.4f} m, R={R:.4f} m, 偏差={h1:.2e}")
    assert h1 < 0.01, "H1 失败"

    rows = []
    for w in np.round(np.arange(0.0, 0.501, 0.05), 2):
        req, infeas = required_support(float(w), 0.0)
        giv, d_d = given_support(float(w), 0.0)
        gap = req - giv
        j = int(np.argmax(gap))
        i0 = int(np.argmin(np.abs(ANGS)))
        h2 = abs(req[i0] - d_d) / d_d if d_d > 0 else 0.0
        rows.append({
            "w": float(w), "Vw_m_s": float(w) * VA, "delta_d_m": d_d,
            "required_along_wind_m": float(req[i0]),
            "required_over_delta_d": float(req[i0] / d_d) if d_d > 0 else float("nan"),
            "max_required_m": float(np.nanmax(req)),
            "max_gap_m": float(max(0.0, gap[j])),
            "gap_dir_deg": float(np.degrees(ANGS[j])),
            "n_infeasible_dirs": int(infeas.sum()),
        })
        print(f"  w={w:.2f} Vw={w*VA:>4.1f}  δd={d_d:>7.2f}  "
              f"沿风向需求={req[i0]:>7.2f} (={req[i0]/d_d if d_d>0 else float('nan'):.4f}·δd)  "
              f"最大缺口={max(0.0,gap[j]):>6.2f} m @ {np.degrees(ANGS[j]):.0f}°  "
              f"不可行方向数={int(infeas.sum())}")

    with open("outputs/exp_fw_v1_21_corrected.csv", "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)

    h2_all = max(abs(r["required_over_delta_d"] - 1.0) for r in rows if r["delta_d_m"] > 0)
    h3_max_gap = max(r["max_gap_m"] for r in rows)
    print()
    print(f"H2 (沿风向需求 == δd): 最大相对偏差 = {h2_all:.4f}")
    print(f"H3 (required <= given): 最大缺口 = {h3_max_gap:.3f} m")

    ws = [r["w"] for r in rows]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    ax[0].plot(ws, [r["required_along_wind_m"] for r in rows], "o-", ms=3, label="required along wind")
    ax[0].plot(ws, [r["delta_d_m"] for r in rows], "s--", ms=3, label="paper δd")
    ax[0].set_xlabel("wind ratio w"); ax[0].set_ylabel("m")
    ax[0].set_title("corrected criterion: required vs paper δd")
    ax[0].grid(alpha=0.3); ax[0].legend()
    ax[1].plot(ws, [r["max_gap_m"] for r in rows], "o-", ms=3)
    ax[1].set_xlabel("wind ratio w"); ax[1].set_ylabel("max gap (m)")
    ax[1].set_title("deficit under corrected criterion")
    ax[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("outputs/figures/exp_fw_v1_21_corrected.png", dpi=160)
    print("wrote outputs/exp_fw_v1_21_corrected.csv and figure")


if __name__ == "__main__":
    main()
