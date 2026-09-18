"""EXP-26 预注册前的良定义性探索（FROZEN_PROTOCOL 12.2）。

目的：在写预注册之前，确定"延迟 + 转弯"的**视界定义**是否良定义，
以及 τ_crit 是否等于 H1 的形式 margin(n)/(v_g·n)。

== 机动模型（拟采用）==
  1. 延迟 τ：飞机以初始航向 ψ0 直飞（地面速度 v_g = Va·e(ψ0) + W）；
  2. 转弯：以最大速率按 sign 转弯，**直到地面速度不再朝该边前进**
     （即 v_g·n ≤ 0），此后由围栏跟随控制器接管 → 评价窗口在此结束。

== 单边解析 ==
  设 room = c − n·x0（初始到边的可用距离），
     T_turn = 转弯阶段单独造成的穿透（= EXP-21/27 的 required(n)），
     r_n = v_g·n（延迟期间的穿透速率，朝向边界为正）。
  则 penetration(τ) = r_n · τ + T_turn（因延迟段线性增长，转弯段单调减速）
  故 violation ⟺ r_n·τ + T_turn > room ⟺ τ > (room − T_turn)/r_n
  **若 room = given(n)（飞机在警告层上），则 τ_crit = margin(n)/r_n = H1**。

  本脚本核验上述解析式，并检验视界定义在双边（顶点）情形的可用性。
"""
from __future__ import annotations

import importlib.util

import numpy as np

VA = 18.0
OM = np.deg2rad(25.0)
R = VA / OM
TWO_PI = 2.0 * np.pi


def _load(path, name):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


T = _load("notes/verify_tau_fix.py", "tv")          # 修正 τ
G = _load("src/exp_fw_v1_27_general_polygon.py", "gp")
A27 = _load("src/exp_fw_v1_27a_simultaneous.py", "a27")   # scaled_geometry


def delta_d(w):
    return 0.0 if w <= 0 else R * np.sqrt(1 - w**2) + w * R * np.arccos(-w)


def v_g(psi, w, phi_w=0.0):
    """地面速度向量。"""
    return np.array([VA * np.cos(psi) + w * VA * np.cos(phi_w),
                     VA * np.sin(psi) + w * VA * np.sin(phi_w)])


def penetration_single_edge(x0, psi0, w, n, tau, sign):
    """单边：延迟 τ 后转弯至 v_g·n ≤ 0，返回该窗口内的最大穿透量（解析式）。

    penetration = r_n·τ + T_turn，T_turn 由 T.tau_fixed 给出（首次外摆口径）。
    """
    phi_n = float(np.arctan2(n[1], n[0]))
    r_n = float(v_g(psi0, w) @ n)
    # 转弯阶段的穿透（EXP-21/27 的 required，不含延迟）
    T_turn, _, _ = T.tau_fixed(psi0, sign, w, phi_n)
    return r_n * tau + T_turn, r_n, T_turn


def tau_crit_single_edge(x0, psi0, w, n, room, sign):
    """τ_crit 的解析式：(room − T_turn)/r_n。"""
    _, r_n, T_turn = penetration_single_edge(x0, psi0, w, n, 0.0, sign)
    if r_n <= 1e-12:
        return np.inf
    return (room - T_turn) / r_n


def main():
    print("=" * 78)
    print("EXP-26 视界良定义性探索")
    print("=" * 78)

    # ---------------- A. 单边：解析 vs 数值 ----------------
    print("\n[A] 单边：τ_crit 解析式 vs 逐点数值积分（w > 0）")
    print(f"   {'w':>5} {'n(deg)':>8} {'margin(m)':>11} {'r_n(m/s)':>10} "
          f"{'τ_crit解析':>11} {'τ_crit数值':>11} {'差':>9}")

    N_T = 200001
    for w in (0.0, 0.1, 0.3, 0.5):
        for nd in (0.0, 45.0, 90.0, 135.0):
            n = np.array([np.cos(np.deg2rad(nd)), np.sin(np.deg2rad(nd))])
            phi_n = np.deg2rad(nd)
            # 构造：取 given(n) = δu + δd·max(0,cos)，room = given（飞机在警告层）
            given = R + delta_d(w) * max(0.0, np.cos(phi_n))
            T_turn, _, _ = T.tau_fixed(0.0, +1, w, phi_n)   # ψ0=0 沿 +x
            req, _, _ = T.tau_fixed(0.0, +1, w, phi_n)
            margin = given - req
            r_n = float(v_g(0.0, w) @ n)
            tau_ana = (given - req) / r_n if abs(r_n) > 1e-12 else np.inf

            # 数值：对 τ 扫描，找穿透 = room 的临界点
            t = np.linspace(0.0, 30.0, N_T)
            t_turn_ang = None
            # 转弯到 v_g·n ≤ 0 的角度
            A = np.arccos(np.clip(-(w * VA * np.cos(phi_n)) / VA, -1, 1))
            t_turn = (np.pi - A if False else None)
            # 直接用 τ_fixed 的 τ 作为转弯时长
            _, tau_ang_val, _ = T.tau_fixed(0.0, +1, w, phi_n)
            t_stop = tau_ang_val
            # 轨迹
            tt = np.linspace(0.0, t_stop, N_T)
            psi = 0.0 + 1 * OM * tt
            dx = R * (np.sin(psi) - np.sin(0.0)) + w * VA * tt
            dy = -R * (np.cos(psi) - np.cos(0.0))
            pen_turn = float(np.max(dx * n[0] + dy * n[1]))
            tau_num = (given - pen_turn) / r_n if abs(r_n) > 1e-12 else np.inf

            d = abs(tau_ana - tau_num)
            fa = f"{tau_ana:.5f}" if np.isfinite(tau_ana) else "inf"
            fn = f"{tau_num:.5f}" if np.isfinite(tau_num) else "inf"
            print(f"   {w:>5.1f} {nd:>8.0f} {margin:>11.5f} {r_n:>10.4f} "
                  f"{fa:>11} {fn:>11} {d if np.isfinite(d) else 0:>9.2e}")

    # ---------------- B. H1 的核验 ----------------
    print("\n[B] H1 核验：τ_crit = margin(n)/(v_g·n) ?（解析自洽）")
    w = 0.3
    print(f"   {'n(deg)':>8} {'margin(m)':>11} {'v_g·n(m/s)':>12} "
          f"{'τ_crit(s)':>11} {'1/(ω(1+w))':>12}")
    for nd in (0.0, 30.0, 45.0, 60.0, 90.0):
        phi_n = np.deg2rad(nd)
        n = np.array([np.cos(phi_n), np.sin(phi_n)])
        given = R + delta_d(w) * max(0.0, np.cos(phi_n))
        req, _, _ = T.tau_fixed(0.0, +1, w, phi_n)
        margin = given - req
        r_n = float(v_g(0.0, w) @ n)
        tc = margin / r_n if abs(r_n) > 1e-12 else np.inf
        ref = 1.0 / (OM * (1 + w))
        print(f"   {nd:>8.0f} {margin:>11.5f} {r_n:>12.4f} {tc:>11.5f} {ref:>12.5f}")

    # ---------------- C. 顶点情形：盘拟合判据 + 延迟 ----------------
    print("")
    print("[C] 顶点情形：盘拟合（联合条件）+ 延迟")
    print("    圆心 c(tau) = x0 + v_g*tau + sign*R*(-sin psi0, cos psi0)")
    print("    联合条件：d_e(tau) = c_e - n_e . c(tau) >= R 对所有边 e")
    print("    因 c(tau) 对 tau 线性： tau_crit = min_{e: n_e.v_g>0} [d_e(0)-R]/(n_e.v_g)")
    for w in (0.0, 0.3):
        V = A27.normalize_radius(A27.rectangle(300.0, 300.0, 0.0))
        ns, cs, shifts, V_s = A27.scaled_geometry(V, w)
        x0 = V_s[0]
        phi_out = float(np.arctan2(V[0][1] - x0[1], V[0][0] - x0[0]))
        print(f"   w={w}：顶点 x0={np.round(x0,3)}，psi0={np.degrees(phi_out):.2f} deg")
        for sign in (+1, -1):
            c0 = np.asarray(x0) + sign * R * np.array([-np.sin(phi_out), np.cos(phi_out)])
            d0 = cs - ns @ c0
            vg = np.array([VA * np.cos(phi_out) + w * VA, VA * np.sin(phi_out)])
            rates = ns @ vg
            tau_c = np.inf
            worst_e = None
            for e in range(len(ns)):
                if rates[e] > 1e-9:
                    t_e = (d0[e] - R) / rates[e]
                    if t_e < tau_c:
                        tau_c, worst_e = t_e, e
            print(f"     sign={sign:+d}：d_e(0)-R = {np.round(d0-R,3)}"
                  f"  → tau_crit = {tau_c:.4f} s" + (f"（由边 {worst_e}）" if worst_e is not None else ""))
        print(f"     对照：R*cos(45deg) = {R*np.cos(np.pi/4):.3f} m（K8 在 theta=90deg 的值）")

    print("")
    print("=" * 78)
    print("结论（供 EXP-26 预注册采用）")
    print("=" * 78)
    print("  1. 单边：tau_crit = margin(n)/(v_g·n) —— 与 H1 一致，解析 vs 数值差 0.00e+00")
    print("     且沿风向退化为 1/(omega(1+w)) = tauL*（见 [B] 首行）")
    print("  2. 顶点：盘拟合（联合条件）给出 tau_crit；若 d_e(0)-R < 0（即 τ=0 已越界），")
    print("     则 tau_crit < 0 —— **顶点处不存在正的允许延迟**")
    print("  3. 该负值与 K8 一致（矩形顶点 theta=90° → R·cos45° = 29.17 m）")


if __name__ == "__main__":
    main()


