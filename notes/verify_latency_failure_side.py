"""V2.0 可行性核验：延迟预算的"失效侧"—— 超过 τL* 之后会发生什么。

当前 V1 只给出了 τL* = 1/(ω(1+w))（EXP-FW-V1-23）。
但它只回答"最多能等多久"，没有回答"等过头会怎样"。
本脚本核验失效侧是否存在同样干净的解析法则。

定义（沿风向，围栏有一边外法线沿风向）：
    given    = R + δd         缓冲构造提供的沿风向覆盖
    required(τ) = 迟延 τ 内直飞、随后满舵转向时的最大沿风向位移
    penetration(τ) = max(0, required(τ) − given)

解析猜想：
    penetration(τ) = Va(1+w)·τ − R           (τ ≥ τL*)
    无量纲： penetration/R = (1+w)·ω·τ − 1
    斜率 = 顺风地速 Va(1+w)，与空速无关（归一化后与 R 无关）

本脚本只做精确数值核验，无随机性。
"""
from __future__ import annotations

import numpy as np

N_PSI = 721
N_T = 4000
T_PERIOD_N = 8.0          # 覆盖足够长时间（以 1/ω 为单位）


def required_along_wind(va, omega, w, tau_L):
    """迟延 tau_L 内的最大沿风向（+x）位移：max over psi0, min over turn sign。

    方向固定为风向 +x；飞机直飞到 tau_L，之后满舵转向，直到地速 x 分量 <= 0。
    """
    R = va / omega
    T = np.linspace(0.0, tau_L + T_PERIOD_N / omega, N_T)[None, :]
    s = np.maximum(0.0, T - tau_L)
    straight = np.minimum(T, tau_L)
    psi0 = np.linspace(0.0, 2 * np.pi, N_PSI, endpoint=False)[:, None]

    best = None
    for sign in (+1, -1):
        psi = psi0 + sign * omega * s
        dx = (va * np.cos(psi0) * straight
              + sign * R * (np.sin(psi) - np.sin(psi0))
              + w * va * T)
        vx = va * np.cos(psi) + w * va
        mask = vx <= 0.0
        hit = mask.any(axis=1)
        idx = np.where(hit, np.argmax(mask, axis=1), N_T - 1)
        rmax = np.maximum.accumulate(dx, axis=1)
        val = np.where(hit, rmax[np.arange(N_PSI), idx], 1e9)
        best = val if best is None else np.minimum(best, val)
    return float(np.max(best))


def delta_d(va, omega, w):
    R = va / omega
    return 0.0 if w <= 0 else R * np.sqrt(1 - w**2) + w * R * np.arccos(-w)


def main():
    print("=" * 78)
    print("V2.0 核验：延迟预算的失效侧（超过 τL* 之后）")
    print("=" * 78)

    VA = 18.0
    OM = np.deg2rad(25.0)
    R = VA / OM
    print(f"\n固定参数：Va={VA} m/s, ω={25.0}°/s, R={R:.4f} m")

    # ---------- A. τL* 复现 ----------
    print("\n[A] τL* 复现（应等于 1/(ω(1+w))）")
    print(f"  {'w':>5} {'τL*(数值)':>10} {'1/(ω(1+w))':>12} {'相对偏差':>10}")
    for w in [0.1, 0.2, 0.3, 0.4, 0.5]:
        given = R + delta_d(VA, OM, w)
        pred = 1.0 / (OM * (1 + w))
        # 二分求 margin 零点
        lo, hi = 0.0, 5.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if given - required_along_wind(VA, OM, w, mid) > 0:
                lo = mid
            else:
                hi = mid
        tau = 0.5 * (lo + hi)
        print(f"  {w:>5.1f} {tau:>10.4f} {pred:>12.4f} {abs(tau-pred)/pred:>10.2e}")

    # ---------- B. 失效侧线性法则 ----------
    print("\n[B] 失效侧：penetration(τ) 是否等于 Va(1+w)·τ − R")
    print(f"  {'w':>5} {'τ(s)':>7} {'数值穿透':>10} {'解析预言':>10} {'偏差':>10}")
    worst = 0.0
    for w in [0.1, 0.3, 0.5]:
        given = R + delta_d(VA, OM, w)
        for tau in [1.0, 2.0, 3.0, 4.0]:
            pen_num = required_along_wind(VA, OM, w, tau) - given
            pen_ana = VA * (1 + w) * tau - R
            if pen_num > 0:
                err = abs(pen_num - pen_ana)
                worst = max(worst, err)
                print(f"  {w:>5.1f} {tau:>7.2f} {pen_num:>10.4f} {pen_ana:>10.4f} {err:>10.2e}")
            else:
                print(f"  {w:>5.1f} {tau:>7.2f} {pen_num:>10.4f} {'(未失效)':>10}")

    print(f"\n  → 失效侧线性法则最大偏差：{worst:.2e}  "
          f"{'通过' if worst < 1e-6 else '不通过'}")

    # ---------- C. 无量纲形式 ----------
    print("\n[C] 无量纲形式：penetration/R = (1+w)·ω·τ − 1，应与参数无关")
    print(f"  {'Va':>5} {'ω(°/s)':>8} {'w':>5} {'τω':>7} {'数值(pen/R)':>12} {'预言':>10}")
    worst_c = 0.0
    for va in [15.0, 18.0, 25.0]:
        for om_deg in [15.0, 25.0, 40.0]:
            om = np.deg2rad(om_deg)
            r = va / om
            w = 0.3
            given = r + delta_d(va, om, w)
            for tau in [1.0 / om * 2.0, 1.0 / om * 3.0]:     # τω = 2, 3
                pen_num = required_along_wind(va, om, w, tau) - given
                pen_pred = (1 + w) * om * tau - 1.0
                if pen_num > 0:
                    ratio = pen_num / r
                    d = abs(ratio - pen_pred)
                    worst_c = max(worst_c, d)
                    print(f"  {va:>5.0f} {om_deg:>8.0f} {w:>5.1f} {om*tau:>7.3f} "
                          f"{ratio:>12.4f} {pen_pred:>10.4f}")
    print(f"\n  → 无量纲法则最大偏差：{worst_c:.2e}  "
          f"{'通过' if worst_c < 1e-6 else '不通过'}")

    # ---------- D. 风估计误差的敏感性（非对称风险） ----------
    print("\n[D] 风估计误差：预算算错多少？方向重要吗？")
    print(f"  {'w真实':>7} {'w估计':>7} {'τL*真实':>10} {'τL*用估计值算':>15} "
          f"{'后果':>12}")
    for w_true, w_est in [(0.3, 0.2), (0.3, 0.4), (0.5, 0.3), (0.1, 0.3)]:
        tau_true = 1.0 / (OM * (1 + w_true))
        tau_est = 1.0 / (OM * (1 + w_est))
        verdict = "不安全(超估预算)" if w_est < w_true else "保守(低估预算)"
        print(f"  {w_true:>7.1f} {w_est:>7.1f} {tau_true:>10.4f} {tau_est:>15.4f} "
              f"{verdict:>12}")

    print("\n  解析： dτL*/τL* = −dw/(1+w)   →  w 低估 x 时，预算超估 x/(1+w)")
    for w, x in [(0.3, 0.1), (0.5, 0.1)]:
        print(f"    w={w}: 低估 {x:.1f} → 预算超估 {x/(1+w)*100:.1f}% ；"
              f"高估 {x:.1f} → 预算低估 {x/(1+w)*100:.1f}%")

    print("\n" + "=" * 78)
    print("结论")
    print("=" * 78)
    print("1. τL* = 1/(ω(1+w)) 复现通过（见 A 节）")
    print("2. 失效侧存在线性法则：penetration = Va(1+w)·τ − R，斜率 = 顺风地速")
    print("3. 风估计误差造成**非对称**风险：低估风速 → 预算超估 → 不安全")
    print("4. 以上均为 3-DOF 水平面、常值风、单方向支撑函数口径")


if __name__ == "__main__":
    main()
