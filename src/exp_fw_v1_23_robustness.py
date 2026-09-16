"""EXP-FW-V1-23: 缓冲构造适用边界的参数稳健性。

预注册见 experiments/EXP-FW-V1-23-preregistration.md。
核心预测：omega * tau_L* ~= 1/(1+w)，与 Va 和 omega 各自无关。
"""
from __future__ import annotations

import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

VA_LIST = [15.0, 18.0, 25.0]
OMEGA_DEG_LIST = [15.0, 25.0, 40.0]
W_LIST = [0.1, 0.2, 0.3, 0.4, 0.5]
TAU_GRID = np.round(np.arange(0.0, 5.0 + 1e-9, 0.1), 2)

N_PSI = 181
N_T = 1500
PSI0 = np.linspace(0.0, 2 * np.pi, N_PSI, endpoint=False)[:, None]


def required_along_wind(va, omega, w, tau_L):
    """沿风向的最坏穿透量（延迟 tau_L 内直飞，之后满舵转向，v.n<=0 后保持）。"""
    R = va / omega
    T_PERIOD = 2.0 * np.pi / omega
    n = np.array([1.0, 0.0])          # 风向 = +x
    W = np.array([w * va, 0.0])
    t = np.linspace(0.0, tau_L + T_PERIOD, N_T)[None, :]
    s = np.maximum(0.0, t - tau_L)
    straight = np.minimum(t, tau_L)

    best = None
    for sign in (+1, -1):
        psi = PSI0 + sign * omega * s
        dx = (va * np.cos(PSI0) * straight
              + sign * R * (np.sin(psi) - np.sin(PSI0)) + W[0] * t)
        dy = (va * np.sin(PSI0) * straight
              - sign * R * (np.cos(psi) - np.cos(PSI0)) + W[1] * t)
        proj_d = dx * n[0] + dy * n[1]
        proj_v = (va * np.cos(psi) + W[0]) * n[0] + (va * np.sin(psi) + W[1]) * n[1]

        mask = proj_v <= 0.0
        any_hit = mask.any(axis=1)
        idx = np.where(any_hit, np.argmax(mask, axis=1), N_T - 1)
        rmax = np.maximum.accumulate(proj_d, axis=1)
        val = np.where(any_hit, rmax[np.arange(N_PSI), idx], 1e9)
        best = val if best is None else np.minimum(best, val)
    return float(np.max(best))


def delta_d(va, omega, w):
    R = va / omega
    return 0.0 if w <= 0 else R * np.sqrt(1 - w**2) + w * R * np.arccos(-w)


def main():
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("outputs/figures", exist_ok=True)
    rows = []

    for va in VA_LIST:
        for om_deg in OMEGA_DEG_LIST:
            om = np.deg2rad(om_deg)
            R = va / om
            for w in W_LIST:
                dd = delta_d(va, om, w)
                given = R + dd

                # H1：tau_L = 0 时 required == delta_d
                req0 = required_along_wind(va, om, w, 0.0)
                h1_err = abs(req0 - dd) / dd

                # 找 tau_L*
                tau_star = None
                prev = None
                for tau in TAU_GRID:
                    req = required_along_wind(va, om, w, float(tau))
                    margin = given - req
                    if prev is not None and tau_star is None and margin <= 0:
                        # 线性插值细化
                        t0, m0 = prev
                        frac = m0 / (m0 - margin) if (m0 - margin) != 0 else 0.0
                        tau_star = float(t0 + frac * (tau - t0))
                        break
                    prev = (float(tau), margin)

                rows.append({
                    "Va_m_s": va, "omega_deg_s": om_deg, "w": w,
                    "R_m": R, "delta_d_m": dd, "given_m": given,
                    "required_tau0_m": req0, "h1_rel_err": h1_err,
                    "margin_at_tau0_m": given - req0,
                    "tau_star_s": tau_star,
                    "omega_tau_star_rad": (om * tau_star) if tau_star else None,
                    "pred_1_over_1pw": 1.0 / (1.0 + w),
                })
                ts = f"{tau_star:.3f}" if tau_star else ">5"
                print(f"  Va={va:>4.0f} ω={om_deg:>4.0f}° w={w:.1f} | R={R:>6.2f} δd={dd:>6.2f} "
                      f"H1err={h1_err:.2e} | τL*={ts:>6}  ω·τL*="
                      f"{(om*tau_star):.3f}" if tau_star else
                      f"  Va={va:>4.0f} ω={om_deg:>4.0f}° w={w:.1f} | R={R:>6.2f} δd={dd:>6.2f} "
                      f"H1err={h1_err:.2e} | τL*>{5}s")

    with open("outputs/exp_fw_v1_23_robustness.csv", "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)

    print()
    print("### H1（τL=0 时 required == δd）最大相对偏差:", f"{max(r['h1_rel_err'] for r in rows):.3e}")
    print("### H2（余量 == δu）最大相对偏差:",
          f"{max(abs(r['margin_at_tau0_m'] - r['R_m'])/r['R_m'] for r in rows):.3e}")

    print()
    print("### H4 / H5：无量纲临界延迟 ω·τL*  与预测 1/(1+w)")
    print(f"{'w':>5} {'预测':>8} {'实测均值':>10} {'标准差':>9} {'变异系数':>9} {'最大相对偏差':>13}")
    ok_h4 = True
    worst_h5 = 0.0
    for w in W_LIST:
        vals = [r["omega_tau_star_rad"] for r in rows if r["w"] == w and r["omega_tau_star_rad"]]
        if not vals:
            print(f"{w:>5.1f}  无有效 τL*")
            ok_h4 = False
            continue
        m, s = float(np.mean(vals)), float(np.std(vals))
        pred = 1.0 / (1.0 + w)
        cv = s / m
        dev = max(abs(v - pred) / pred for v in vals)
        worst_h5 = max(worst_h5, dev)
        if cv >= 0.10:
            ok_h4 = False
        print(f"{w:>5.1f} {pred:>8.4f} {m:>10.4f} {s:>9.4f} {cv:>9.3f} {dev:>13.3f}")
    print()
    print(f"H4（ω·τL* 与 Va、ω 无关，CV<10%）: {'通过' if ok_h4 else '不通过'}")
    print(f"H5（与 1/(1+w) 偏差 <20%）: 最大相对偏差 {worst_h5:.3f} -> {'通过' if worst_h5 < 0.20 else '不通过'}")

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    for va in VA_LIST:
        for om_deg in OMEGA_DEG_LIST:
            sub = [r for r in rows if r["Va_m_s"] == va and r["omega_deg_s"] == om_deg and r["omega_tau_star_rad"]]
            if sub:
                ax[0].plot([r["w"] for r in sub], [r["omega_tau_star_rad"] for r in sub],
                           "o-", ms=3, alpha=0.7, label=f"Va={va:.0f}, ω={om_deg:.0f}°/s")
    ww = np.linspace(0.1, 0.5, 50)
    ax[0].plot(ww, 1 / (1 + ww), "k--", lw=2, label="prediction 1/(1+w)")
    ax[0].set_xlabel("wind ratio w"); ax[0].set_ylabel("ω · τL*  (rad)")
    ax[0].set_title("dimensionless critical latency (H4/H5)")
    ax[0].grid(alpha=0.3); ax[0].legend(fontsize=7)
    ax[1].plot([r["w"] for r in rows if r["tau_star_s"]],
               [r["tau_star_s"] for r in rows if r["tau_star_s"]], "o", ms=3, alpha=0.0)
    for va in VA_LIST:
        for om_deg in OMEGA_DEG_LIST:
            sub = [r for r in rows if r["Va_m_s"] == va and r["omega_deg_s"] == om_deg and r["tau_star_s"]]
            if sub:
                ax[1].plot([r["w"] for r in sub], [r["tau_star_s"] for r in sub], "o-", ms=3, alpha=0.7)
    ax[1].set_xlabel("wind ratio w"); ax[1].set_ylabel("τL* (s)")
    ax[1].set_title("critical latency in seconds (parameter dependent)")
    ax[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("outputs/figures/exp_fw_v1_23_robustness.png", dpi=160)
    print("wrote outputs/exp_fw_v1_23_robustness.csv and figure")


if __name__ == "__main__":
    main()
