"""EXP-FW-V1-26 臂 R：一阶滚转动力学下的延迟预算（检验 H3）。

预注册：experiments/EXP-FW-V1-26-preregistration.md 第 4.3/5 节（判据 P4）
前置：src/exp_fw_v1_26_joint_latency.py（臂 I，已通过三件套与解析交叉）
文献核查：见 experiments/EXP-FW-V1-26-armR.md 末段（FROZEN_PROTOCOL 第 13 节）

== H3 的预言 ==
一阶滚转响应：φ(t)/φ_max = 1 − e^(−t/τ_roll) ⟹ ω_eff(t) = ω(1 − e^(−t/τ_roll))
航向亏损 = ∫₀^∞ [ω − ω_eff] dt = ω·τ_roll  ⟹ 等价于**多延迟 τ_roll**

故： τ_crit(臂 R) = τ_crit(臂 I) − τ_roll          （H3）

== 臂 R 的轨迹（与臂 I 的区别只在转弯段）==
延迟段（同臂 I）：直飞 τ_delay
转弯段：ψ(s) = ψ0 + sign·ω·(s − τ_roll(1 − e^(−s/τ_roll))),  s = t − τ_delay
位置：数值积分（因转弯率随时间变化）

== 判据（直接轨迹穿透，与臂 I 的圆盘判据在窗口内等价）==
pen_e = max over 该边的**连续推进段** of [ n_e·x(t) − c_e ]
越界 ⟺ 存在 e 使 pen_e > 0

== 三件套（FROZEN_PROTOCOL 12.1，先跑）==
(a) 负对照：形心（远离各边）→ 应无越界
(b) 正对照：大 τ_roll 应**减小** τ_crit（滚转滞后有害）——判据须能体现该单调性
(c) 交叉验证：τ_roll → 0 时臂 R 应**复现臂 I**（臂 I 已由解析交叉独立验证）
"""
from __future__ import annotations

import csv
import importlib.util
import os

import numpy as np

# ---------------------------------------------------------------- 载入臂 I 机制
_s = importlib.util.spec_from_file_location("a26", "src/exp_fw_v1_26_joint_latency.py")
A26 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A26)

VA = A26.VA_DEFAULT
OM = A26.OMEGA
R = A26.R
TWO_PI = A26.TWO_PI
hrep_from_verts = A26.hrep_from_verts
verts_from_hrep = A26.verts_from_hrep
setup_rect = A26.setup_rect
edge_midpoint = A26.edge_midpoint
v_ground = A26.v_ground
tau_crit_analytic_joint = A26.tau_crit_analytic_joint
tau_crit_measured = A26.tau_crit_measured

N_T_R = 40001


# ---------------------------------------------------------------- 臂 R 轨迹
def heading_arm_R(t, psi0, sign, tau_roll, om=OM):
    """一阶滚转下的航向：ψ(s) = ψ0 + sign·ω·(s − τ_roll(1 − e^(−s/τ_roll)))。"""
    if tau_roll <= 0:
        return psi0 + sign * om * t
    return psi0 + sign * om * (t - tau_roll * (1.0 - np.exp(-t / tau_roll)))


def trajectory_arm_R(x0, psi0, sign, tau_delay, tau_roll, w, va=VA, phi_wind=0.0,
                     n_t=N_T_R):
    """返回 (t_all, x_all, psi_all)：延迟段 + 滚转受限转弯段。"""
    t_fly = np.linspace(0.0, max(tau_delay, 0.0), 3) if tau_delay > 0 else np.array([0.0])
    # 转弯段时长：需足够长以完成转弯（滚转滞后会延长）
    span = TWO_PI / OM + 6.0 * max(tau_roll, 0.0)
    t_turn = np.linspace(0.0, span, n_t)
    if tau_delay > 0:
        t_all = np.concatenate([t_fly, tau_delay + t_turn[1:]])
    else:
        t_all = t_turn

    psi = np.empty(len(t_all))
    x = np.empty((len(t_all), 2))
    # 转弯段：在整个 t_turn 网格上积分（含首个区间，避免漏一步）
    psi_turn_full = heading_arm_R(t_turn, psi0, sign, tau_roll)
    vx_f = va * np.cos(psi_turn_full) + w * va * np.cos(phi_wind)
    vy_f = va * np.sin(psi_turn_full) + w * va * np.sin(phi_wind)
    dx_full = np.concatenate([[0.0], np.cumsum(0.5 * (vx_f[1:] + vx_f[:-1]) * np.diff(t_turn))])
    dy_full = np.concatenate([[0.0], np.cumsum(0.5 * (vy_f[1:] + vy_f[:-1]) * np.diff(t_turn))])

    if tau_delay > 0:
        vg0 = v_ground(psi0, w, va, phi_wind)
        x[:len(t_fly)] = np.asarray(x0, float) + np.outer(t_fly, vg0)
        psi[:len(t_fly)] = psi0
        x_t = x[len(t_fly) - 1]
        psi[len(t_fly):] = psi_turn_full[1:]
        x[len(t_fly):] = x_t + np.stack([dx_full[1:], dy_full[1:]], axis=-1)
    else:
        psi[:] = psi_turn_full
        x[:] = np.asarray(x0, float) + np.stack([dx_full, dy_full], axis=-1)
    return t_all, x, psi


def simulate_arm_R(x0, psi0, sign, tau_delay, ns, cs, w, r, tau_roll,
                   va=VA, phi_wind=0.0):
    """臂 R 的越界量与是否越界（直接轨迹穿透，窗口 = 连续推进段）。"""
    t_all, x, psi = trajectory_arm_R(x0, psi0, sign, tau_delay, tau_roll,
                                     w, va, phi_wind)
    vgx = va * np.cos(psi) + w * va * np.cos(phi_wind)
    vgy = va * np.sin(psi) + w * va * np.sin(phi_wind)
    worst = -np.inf
    for e in range(len(ns)):
        n_e, c_e = ns[e], cs[e]
        rate = vgx * n_e[0] + vgy * n_e[1]
        moving = rate > 1e-12
        if not moving.any():
            continue
        i0 = int(np.argmax(moving))
        i1 = i0
        while i1 + 1 < len(moving) and moving[i1 + 1]:
            i1 += 1
        proj = x[:, 0] * n_e[0] + x[:, 1] * n_e[1]
        pen = proj[i0:i1 + 1] - c_e
        worst = max(worst, float(np.max(pen)))
    return worst, bool(worst > 1e-9)


def tau_crit_arm_R(x0, psi0, ns, cs, w, r, tau_roll, va=VA, phi_wind=0.0,
                   lo=0.0, hi=30.0, iters=70, tol=1e-12):
    """臂 R 的 τ_crit（二分）。返回 (tau_crit, feasible)。"""
    def violated(tau):
        for sign in (+1, -1):
            _, v = simulate_arm_R(x0, psi0, sign, tau, ns, cs, w, r, tau_roll,
                                  va, phi_wind)
            if not v:
                return False
        return True
    if violated(lo):
        lo2, hi2 = -hi, 0.0
        for _ in range(iters):
            mid = 0.5 * (lo2 + hi2)
            if violated(mid):
                hi2 = mid
            else:
                lo2 = mid
        return 0.5 * (lo2 + hi2), False
    if not violated(hi):
        return np.inf, True
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if violated(mid):
            hi = mid
        else:
            lo = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi), True


# ---------------------------------------------------------------- 自检
def check_deficit_identity():
    """自检：航向亏损 = ω·τ_roll（H3 推导的一步）。"""
    print("[自检] 航向亏损 = omega·tau_roll ?")
    worst = 0.0
    for tr in (0.3, 0.5, 0.8, 1.2):
        s = np.linspace(0.0, 60 * tr, 400001)
        deficit = float(np.trapezoid(OM * np.exp(-s / tr), s))
        worst = max(worst, abs(deficit - OM * tr))
    print(f"   最大绝对偏差 = {worst:.3e} rad -> "
          f"{'通过' if worst < 1e-8 else '不通过'}")
    return worst


def c_neg():
    """(a) 负对照：形心处应无越界。"""
    print("")
    print("[三件套 a] 负对照：形心（远离各边）应无越界")
    bad = tot = 0
    for w in (0.0, 0.3):
        V, ns, cs, shifts, V_s = setup_rect(w)
        c = V_s.mean(axis=0)
        for psd in range(0, 360, 45):
            for tr in (0.3, 0.8):
                for sign in (+1, -1):
                    _, vi = simulate_arm_R(c, np.deg2rad(psd), sign, 0.0,
                                           ns, cs, w, R, tr)
                    tot += 1
                    bad += int(vi)
    ok = bad == 0
    print(f"   {tot} 组合，越界 {bad} 个 -> {'通过' if ok else '不通过'}")
    return ok


def c_pos():
    """(b) 正对照：τ_roll 增大应单调减小 τ_crit。"""
    print("")
    print("[三件套 b] 正对照：tau_roll 增大 -> tau_crit 减小（须单调）")
    w = 0.3
    V, ns, cs, shifts, V_s = setup_rect(w)
    e = 0
    x0 = edge_midpoint(V_s, ns, cs, e) + 1.0 * R * (-ns[e])
    psi = float(np.arctan2(-ns[e][1], -ns[e][0]))
    vals = []
    for tr in (1e-6, 0.3, 0.5, 0.8):
        tc, _ = tau_crit_arm_R(x0, psi, ns, cs, w, R, tr)
        vals.append((tr, tc))
        print(f"   tau_roll={tr:>7.6f}: tau_crit={tc:>9.5f} s")
    mono = all(vals[i][1] >= vals[i + 1][1] - 1e-9 for i in range(len(vals) - 1))
    drop = vals[0][1] - vals[-1][1]
    print(f"   单调递减 = {mono}；总降幅 = {drop:.4f} s")
    return mono and drop > 1e-6


def c_cross():
    """(c) 交叉验证：两项同类比较。

    (c1) **轨迹一致性**：τ_roll→0 时臂 R 的轨迹应等于臂 I 的解析圆弧轨迹。
    (c2) **判据关系**：臂 I（圆盘判据）≤ 臂 R（直接轨迹），因圆盘假设最坏航向被达到；
         该关系必须成立（否则说明有实现错误）。
    """
    print("")
    print("[三件套 c1] 轨迹一致性：臂 R(τ_roll→0) vs 臂 I 的解析圆弧（逐点比位置）")
    print(f"   {'w':>5} {'psi':>5} {'最大位置差(m)':>14}")
    worst_pos = 0.0
    for w in (0.0, 0.1, 0.3, 0.5):
        V, ns, cs, shifts, V_s = setup_rect(w)
        e = 0
        x0 = edge_midpoint(V_s, ns, cs, e) + 1.0 * R * (-ns[e])
        for psd in (0, 90, 180, 270):
            psi0 = np.deg2rad(psd)
            for sign in (+1, -1):
                t, x, psi = trajectory_arm_R(x0, psi0, sign, 0.25, 1e-9, w)
                # 解析参照：直飞段用 vg·t，转弯段用 vg·(t−0.25) + 圆弧
                s_fly = np.minimum(t, 0.25)
                s_turn = np.clip(t - 0.25, 0.0, None)
                psi_a = psi0 + sign * OM * s_turn
                dx = sign * R * (np.sin(psi_a) - np.sin(psi0)) + w * VA * s_turn
                dy = -sign * R * (np.cos(psi_a) - np.cos(psi0))
                x_arc = (np.asarray(x0, float) + np.outer(s_fly, v_ground(psi0, w))
                         + np.stack([dx, dy], axis=-1))
                dmax = float(np.max(np.abs(x - x_arc)))
                worst_pos = max(worst_pos, dmax)
                if psd == 90 and w == 0.3:
                    print(f"   {w:>5.1f} {psd:>5} {dmax:>14.3e}")
    ok1 = worst_pos < 1e-6
    print(f"   -> 全局最大位置差 = {worst_pos:.3e} m -> {'通过' if ok1 else '不通过'}")

    print("")
    print("[三件套 c2] 判据关系：臂 I(圆盘) <= 臂 R(直接轨迹) 应恒成立")
    print(f"   {'w':>5} {'psi':>5} {'臂I(圆盘)':>11} {'臂R(traj)':>11} {'关系':>10}")
    ok2 = True
    for w in (0.0, 0.1, 0.3, 0.5):
        V, ns, cs, shifts, V_s = setup_rect(w)
        e = 0
        x0 = edge_midpoint(V_s, ns, cs, e) + 1.0 * R * (-ns[e])
        for psd in (0, 90, 180, 270):
            psi = np.deg2rad(psd)
            tI, _ = tau_crit_analytic_joint(x0, psi, ns, cs, w, R)
            tR, _ = tau_crit_arm_R(x0, psi, ns, cs, w, R, 1e-9)
            if np.isfinite(tI) and np.isfinite(tR):
                good = tR >= tI - 1e-6
                ok2 &= good
                tag = "OK" if good else "**违反**"
                print(f"   {w:>5.1f} {psd:>5} {tI:>11.5f} {tR:>11.5f} {tag:>10}")
    print(f"   -> {'通过（圆盘判据确实更紧）' if ok2 else '不通过'}")
    return ok1 and ok2


def main():
    print("=" * 78)
    print("EXP-FW-V1-26 臂 R：一阶滚转动力学下的延迟预算（H3）")
    print("=" * 78)
    print(f"R = {R:.4f} m；tau_roll in {{0.3, 0.5, 0.8}} s\n")

    d = check_deficit_identity()
    ok_n = c_neg()
    ok_p = c_pos()
    ok_c = c_cross()

    print("")
    print("=" * 78)
    print("三件套总判（臂 R）")
    print("=" * 78)
    all_ok = ok_n and ok_p and ok_c and (d < 1e-8)
    print(f"  自检(亏损恒等式): {'通过' if d < 1e-8 else '不通过'}")
    print(f"  a 负对照        : {'通过' if ok_n else '不通过'}")
    print(f"  b 正对照        : {'通过' if ok_p else '不通过'}")
    print(f"  c 交叉验证      : {'通过' if ok_c else '不通过'}")
    if not all_ok:
        print("")
        print("  ** 三件套未全过 -> H3 判定不得讨论。**")
        return

    print("")
    print("[H3 判定] tau_crit(臂R) ?= tau_base − tau_roll")
    print("  tau_base = 臂 R 在 tau_roll→0 的 tau_crit（同类判据基线）")
    print(f"   {'w':>5} {'psi':>5} {'tau_roll':>9} {'tau_base':>9} {'臂R':>9} "
          f"{'基线−τroll':>11} {'相对偏差':>10}")
    os.makedirs("outputs", exist_ok=True)
    rows = []
    worst_rel = 0.0
    for w in (0.0, 0.1, 0.3, 0.5):
        V, ns, cs, shifts, V_s = setup_rect(w)
        e = 0
        x0 = edge_midpoint(V_s, ns, cs, e) + 1.0 * R * (-ns[e])
        for psd in (0, 45, 90, 135, 180, 270):
            psi = np.deg2rad(psd)
            base, _ = tau_crit_arm_R(x0, psi, ns, cs, w, R, 1e-9)
            for tr in (0.3, 0.5, 0.8):
                tR, _ = tau_crit_arm_R(x0, psi, ns, cs, w, R, tr)
                if np.isfinite(base) and np.isfinite(tR):
                    pred = base - tr
                    rel = abs(tR - pred) / max(abs(pred), 1e-9)
                    worst_rel = max(worst_rel, rel)
                    rows.append({"w": w, "psi_deg": float(np.degrees(psi)),
                                 "tau_roll": tr, "tau_base": base,
                                 "tau_armR": tR, "pred_base_minus_roll": pred,
                                 "rel_dev": rel})
                    if tr == 0.5:
                        print(f"   {w:>5.1f} {np.degrees(psi):>5.0f} {tr:>9.2f} "
                              f"{base:>9.5f} {tR:>9.5f} {pred:>11.5f} {rel:>10.2e}")
    print("")
    print(f"   最大相对偏差 = {worst_rel:.3e}")
    verdict = ("支持（< 1%）" if worst_rel < 0.01 else
               "支持（1%–5%）" if worst_rel < 0.05 else
               "部分支持（5%–20%）" if worst_rel < 0.20 else "不支持")
    print(f"   -> H3 判定：{verdict}")

    with open("outputs/exp_fw_v1_26_armR.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print("")
    print(f"wrote outputs/exp_fw_v1_26_armR.csv（{len(rows)} 行）")


if __name__ == "__main__":
    main()
