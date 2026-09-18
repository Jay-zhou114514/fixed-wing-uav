"""Kim et al. (2022, DASC) 式 7 与 Table IV/V 的数值交叉核对。

目的（独立实现 vs 已发表数值）：
  1. 用 Table IV 的参数代入式 7a-7d，复现 Table V 的 δ_sb 与 δ_sbx；
  2. 由此判定式 7b 在正文印刷的 "3σz" 是否为笔误（应为 3σy）；
  3. 复现正文的两处差值陈述（4.47 / 0.76 / ~8m）。

这属于 FROZEN_PROTOCOL 12.1(c) 的"独立实现交叉验证"：
核对的是第三方论文的自洽性，用于支撑"我们确实读懂了其缓冲构造"。
"""

TOL = 0.02  # 发表值仅保留 2 位小数

# Table IV（Unit: m）
TABLE_IV = {
    "Aerosonde UAS": dict(
        eps_gy=16.90, eps_gz=5.45, sigma=[1.08, 0.66, 0.28], b=2.89, fl=0.72, h=0.30
    ),
    "AAM": dict(
        eps_gy=18.11, eps_gz=4.86, sigma=[1.03, 0.78, 0.23], b=8.70, fl=2.538, h=0.90
    ),
}
# Table V（Unit: m）
TABLE_V = {
    "Aerosonde UAS": dict(dsb=20.33, dsbx=3.60),
    "AAM": dict(dsb=24.80, dsbx=4.36),
}


def eq7(v, lateral_sigma_is_y=True):
    """式 7a-7d。lateral_sigma_is_y=False 时按正文印刷的 3σz 计算（用于笔误判定）。"""
    sx, sy, sz = v["sigma"]
    dsbx = 3.0 * sx + 0.5 * v["fl"]                    # (7a)
    s_lat = sy if lateral_sigma_is_y else sz
    dsby = 3.0 * s_lat + v["eps_gy"] + 0.5 * v["b"]    # (7b)
    dsbz = 3.0 * sz + v["eps_gz"] + 0.5 * v["h"]       # (7c)
    return dict(dsbx=dsbx, dsby=dsby, dsbz=dsbz, dsb=max(dsby, dsbz))  # (7d)


print("=" * 78)
print("A. 式 7a-7d vs Table V（横向 σ 取 σ_y）")
print("=" * 78)
print(f"{'模型':<16}{'量':<8}{'式 7 计算':>12}{'Table V':>10}{'偏差':>10}  {'判定':<6}")
ok_all = True
res = {}
for name, v in TABLE_IV.items():
    r = eq7(v, True)
    res[name] = r
    for key, pub in (("dsbx", TABLE_V[name]["dsbx"]), ("dsb", TABLE_V[name]["dsb"])):
        d = r[key] - pub
        ok = abs(d) <= TOL
        ok_all &= ok
        print(f"{name:<16}{key:<8}{r[key]:>12.4f}{pub:>10.2f}{d:>10.4f}  {'✓' if ok else '✗':<6}")
print(f"\n小结论：{'式 7 完全复现 Table V（σ_y 口径）' if ok_all else '存在不一致'}")

print()
print("=" * 78)
print("B. 笔误判定：若式 7b 严格按正文印刷的 3σz 计算")
print("=" * 78)
for name, v in TABLE_IV.items():
    r_typo = eq7(v, False)
    pub = TABLE_V[name]["dsb"]
    print(f"{name:<16} 3σz 口径 → δ_sb = {r_typo['dsb']:.4f} m；"
          f"发表值 = {pub:.2f} m；差 {r_typo['dsb'] - pub:+.4f} m")
    print(f"{'':<16} → {'与发表值不符，确认为笔误' if abs(r_typo['dsb'] - pub) > 10 * TOL else '相符'}")
    # 垂向分支本身
    print(f"{'':<16} （对照：垂向分支 δ_sbz = {r_typo['dsbz']:.4f} m，横向分支按 σ_z 时 = {r_typo['dsby']:.4f} m）")

print()
print("=" * 78)
print("C. 正文差值陈述复现")
print("=" * 78)
d_cross = res["AAM"]["dsb"] - res["Aerosonde UAS"]["dsb"]
d_long = res["AAM"]["dsbx"] - res["Aerosonde UAS"]["dsbx"]
print(f"横向缓冲差  AAM - Aerosonde = {d_cross:.4f} m   （正文称 4.47 m）")
print(f"纵向缓冲差  AAM - Aerosonde = {d_long:.4f} m   （正文称 0.76 m）")
print(f"围栏宽度差 2×Δδ_sb          = {2 * d_cross:.2f} m   （正文称 'approximately 8 m'）")
print(f"  → 按表中数值应为 {2 * d_cross:.2f} m（≈{round(2 * d_cross)} m），"
      f"正文 '8 m' 属其自身四舍五入不一致（不影响任何结论）")

print()
print("=" * 78)
print("D. 结构性判读（供文献分析引用）")
print("=" * 78)
for name, v in TABLE_IV.items():
    r = eq7(v, True)
    sx, sy, sz = v["sigma"]
    print(f"{name}:")
    print(f"  导航项 3σ = [{3*sx:.2f}, {3*sy:.2f}, {3*sz:.2f}] m  → 量级 < 3.3 m")
    print(f"  制导项   = [ε_gy={v['eps_gy']:.2f}, ε_gz={v['eps_gz']:.2f}] m  → 量级 4.9–18.1 m")
    print(f"  机身项   = [f_l/2={v['fl']/2:.2f}, b/2={v['b']/2:.2f}, h/2={v['h']/2:.2f}] m")
    print(f"  横向/垂向分支 = [{r['dsby']:.2f}, {r['dsbz']:.2f}] → 取 max = {r['dsb']:.2f}")
    dom = "制导误差" if r["dsby"] - (3 * sy) > 3 * sy else "导航"
    print(f"  → 横向分支中制导误差占 {100*v['eps_gy']/r['dsby']:.1f}%（主导项）")
print()
print("注意：截面横/垂向分支不含任何与来流方向（风向）有关的项。")
print("      水平面内缓冲被 'max[δsby,δsbz]' 取为单一值 ⟹ 各向同性。")
