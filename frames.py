#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ロボットのフレームをデザインし、プレビューPNG + main.m用配列を吐く"""
import zlib, struct, sys

W, H = 28, 18


def blank():
    return [["." for _ in range(W)] for _ in range(H)]


def rows_of(grid):
    return ["".join(r) for r in grid]


def set_px(grid, x, y, on=True):
    if 0 <= x < W and 0 <= y < H:
        grid[y][x] = "X" if on else "."


def put(grid, x, y, ch):
    if 0 <= x < W and 0 <= y < H:
        grid[y][x] = ch


def paint(grid, x0, x1, y0, y1, ch):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(grid, x, y, ch)


def fill_rect(grid, x0, x1, y0, y1, on=True):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            set_px(grid, x, y, on)


def overlay(base, other):
    """other の色付き画素を base に重ねる（other の '.' は透過＝base をそのまま残す）"""
    g = [row[:] for row in base]
    for y in range(H):
        for x in range(W):
            if other[y][x] != ".":
                g[y][x] = other[y][x]
    return g


# ---------------------------------------------------------------------------
# ロボット本体（iCarly のスペンサー製ロボット彫刻風：四角い頭+胴+腕+脚、ジャンク感）
#
# フル形態の座標（dx=0 のとき）:
#   アンテナ  x=7            y=0-1
#   頭        x=4-9 (6幅)     y=2-5   目穴 (5,3)(8,3)
#   首        x=6-7           y=6
#   胴        x=2-11 (10幅)   y=7-12
#   腕        x=0-1 / x=12-13 y=7-11
#   脚        x=4-5 / x=8-9   y=13-17
#
# コンパクト形態（entering box 用・腕とアンテナを畳んだ幅10）:
#   頭-首-胴-脚のみ。x範囲 2-11 (10幅) はエレベーター内寸とぴったり一致。
# ---------------------------------------------------------------------------

def tube_row(g, x0, x1, y, upper):
    """巻いたケーブル一段の、上半分(upper)か下半分の1行。左上からの柔らかい光で、
       手前（左）が明るく奥（右）へ沈む。右端だけ照り返しでわずかに戻す（輪郭のため）"""
    n = max(1, x1 - x0)
    for x in range(x0, x1 + 1):
        t = (x - x0) / n
        if x == x1:
            ch = "c"
        elif upper:
            ch = "e" if x == x0 else "d" if t < 0.35 else "c" if t < 0.7 else "b"
        else:
            ch = "d" if x == x0 else "c" if t < 0.3 else "b" if t < 0.75 else "a"
        put(g, x, y, ch)


def robot(dx=0, lean=0, crouch=0, compact=False, banzai=False, hop=False):
    """CPUロボット（マットな黒いケーブルを饅頭状に巻いて、人の形に整えたもの・カラー）
       つやは無い。左上からの柔らかい光の明暗（e→d→c→b→a）と、段の間の溝だけで巻きの立体を出す。
       色の文字: a=溝・いちばん深い黒 b=芯の黒 c=中間 d=光の当たる面 e=手前の縁
                 f=プラグの先（つや消しの灰色。目・手・アンテナ）
       dx: 全体の横シフト（エレベーターへの移動用）
       lean: 上半身（頭・首・胴・腕）だけを足に対して左右にずらす（ゆらゆら用）
       crouch: 上半身を1px落として脚を1px縮める（EDMのドゥンドゥン用）
       compact: 腕とアンテナを省いた細身シルエット（エレベーターに入る用）
       banzai: 腕を頭の横まで振り上げる（最高潮用）
       hop: 足先を1px浮かせる＝跳ねた瞬間（最高潮用）
    """
    g = blank()
    ux, uy = dx + lean, crouch

    # 脚: 二本撚りのケーブル。左が光の面、右が沈む面、撚り目ごとに溝。足先は丸めて1pxに
    leg_top, leg_bot = 13 + crouch, 16 if hop else 17
    for lx in (4, 8):
        for y in range(leg_top, leg_bot):
            groove = (y - leg_top) % 2 == 1
            put(g, lx + dx, y, "c" if groove else "d")
            put(g, lx + 1 + dx, y, "a" if groove else "b")
        put(g, lx + (1 if lx == 4 else 0) + dx, leg_bot, "c")   # 足先（内側に寄せて丸く）

    # アンテナ: 巻き終わりの端が一本立って、先にプラグ
    if not compact:
        put(g, 7 + ux, 0 + uy, "f")
        put(g, 7 + ux, 1 + uy, "b")
    # 頭: 饅頭状のとぐろ。段ごとに幅を変えて角のない丸に、目は顔を出したプラグの先
    tube_row(g, 5 + ux, 8 + ux, 1 + uy, True)
    tube_row(g, 4 + ux, 9 + ux, 2 + uy, True)
    tube_row(g, 3 + ux, 10 + ux, 3 + uy, False)
    tube_row(g, 3 + ux, 10 + ux, 4 + uy, True)
    tube_row(g, 4 + ux, 9 + ux, 5 + uy, False)
    put(g, 5 + ux, 3 + uy, "f")
    put(g, 8 + ux, 3 + uy, "f")
    # 首
    put(g, 6 + ux, 6 + uy, "c")
    put(g, 7 + ux, 6 + uy, "a")
    # 胴: 三段に積んだ巻き。上下の段を細くして角のない卵形に
    for y, (x0, x1) in zip(range(7, 13), ((4, 9), (3, 10), (2, 11), (2, 11), (3, 10), (4, 9))):
        tube_row(g, x0 + ux, x1 + ux, y + uy, y % 2 == 1)

    # 腕: 束ねたケーブルのカプセル形。肩側も先も1pxにすぼめて角を作らない、先はプラグ
    #     胴が卵形になったので、胴の一番太い段（9〜10行目）の横に付ける
    def arm(ax, y0, y1, plug_y, root_y):
        inner = ax + 1 if ax == 0 else ax                # 胴に近い側の列
        for y in range(y0, y1 + 1):
            groove = (y - y0) % 2 == 1
            put(g, ax + ux, y + uy, "c" if groove else "d")
            put(g, ax + 1 + ux, y + uy, "a" if groove else "b")
        put(g, inner + ux, root_y + uy, "c")             # 付け根（1px）
        put(g, inner + ux, plug_y + uy, "f")             # 先のプラグ（1px）
    if banzai:
        for ax in (0, 12):
            arm(ax, 4, 9, 3, 10)
    elif not compact:
        for ax in (0, 12):
            arm(ax, 9, 11, 12, 8)
    return g


# ---------------------------------------------------------------------------
# GPUロボット（緑のペットボトルとジャンク銀でできた彫刻ロボット・カラー）
#   色の文字: S=銀（フレーム/ジャバラ/頭の板） G=緑のボトル R=赤（目・胸の帯・手のひら）
#   'X' は使わない（X=メニューバーの文字色。箱と CPU ロボットだけが使う）
#   骨格は robot() と同じ座標・同じ引数なので、箱への出入りもそのまま通る
# ---------------------------------------------------------------------------

def gpu_robot(dx=0, lean=0, crouch=0, compact=False, banzai=False, hop=False):
    g = blank()
    ux, uy = dx + lean, crouch

    # 脚: 下から 靴(銀) → すね(緑ボトル) → 太もも(銀ジャバラ)
    leg_top, leg_bot = 13 + crouch, 16 if hop else 17
    for lx in (4, 8):
        x0, x1 = lx + dx, lx + 1 + dx
        for y in range(leg_top, leg_bot + 1):
            from_bot = leg_bot - y
            put(g, x0, y, "S" if from_bot == 0 or from_bot >= 3 else "G")
            put(g, x1, y, "S" if from_bot == 0 or from_bot >= 3 else "G")

    # 頭の上のつまみ
    if not compact:
        paint(g, 6 + ux, 7 + ux, 0 + uy, 0 + uy, "S")
    # 頭: 透明ボトルに銀の板を貼った四角い箱、赤い丸目、まんなかに鼻の板
    paint(g, 3 + ux, 10 + ux, 1 + uy, 5 + uy, "S")
    paint(g, 4 + ux, 5 + ux, 2 + uy, 3 + uy, "R")
    paint(g, 8 + ux, 9 + ux, 2 + uy, 3 + uy, "R")
    paint(g, 5 + ux, 5 + ux, 5 + uy, 5 + uy, ".")   # 口の隙間（鼻の板の左右）
    paint(g, 8 + ux, 8 + ux, 5 + uy, 5 + uy, ".")
    # 首（ジャバラ）
    paint(g, 6 + ux, 7 + ux, 6 + uy, 6 + uy, "S")
    # 胴: 緑のボトルを詰めた胴を、上下の銀パイプで挟む。胸に赤い帯が一本、下に銀の縞板
    paint(g, 2 + ux, 11 + ux, 7 + uy, 12 + uy, "G")
    paint(g, 2 + ux, 11 + ux, 7 + uy, 7 + uy, "S")      # 肩のパイプ
    paint(g, 2 + ux, 11 + ux, 12 + uy, 12 + uy, "S")    # 腰のパイプ
    paint(g, 3 + ux, 10 + ux, 9 + uy, 9 + uy, "R")      # 胸の赤い帯
    paint(g, 4 + ux, 9 + ux, 11 + uy, 11 + uy, "S")     # 縞板

    # 腕: 肩から 緑ボトル → 銀ジャバラの前腕 → 緑の手
    if banzai:
        for ax in (0, 12):
            paint(g, ax + ux, ax + 1 + ux, 6 + uy, 7 + uy, "G")
            paint(g, ax + ux, ax + 1 + ux, 3 + uy, 5 + uy, "S")
            paint(g, ax + ux, ax + 1 + ux, 1 + uy, 2 + uy, "G")
    elif not compact:
        for ax in (0, 12):
            paint(g, ax + ux, ax + 1 + ux, 7 + uy, 8 + uy, "G")
            paint(g, ax + ux, ax + 1 + ux, 9 + uy, 10 + uy, "S")
            paint(g, ax + ux, ax + 1 + ux, 11 + uy, 11 + uy, "G")
    return g


# ---------------------------------------------------------------------------
# エレベーターの箱（右側 x=16-27, 12幅・フル高さ y=0-17）
# ---------------------------------------------------------------------------
BX0, BX1 = 16, 27
BY0, BY1 = 0, 17


def box(mode="closed", grow=None, wipe_top=None):
    """mode: 'closed' = ベタ塗りの箱 / 'open' = 外枠だけ（中は空洞）
       grow: 上からせり出してくる途中（下端の行数だけ描く。None ならフル）
       wipe_top: 上から消えていく途中（この行数だけ上を消す。None なら消さない）
    """
    g = blank()
    y0, y1 = BY0, BY1
    if grow is not None:
        y1 = min(BY1, BY0 + grow - 1)
    if mode == "closed":
        fill_rect(g, BX0, BX1, y0, y1, True)
    else:  # open = 枠だけ
        fill_rect(g, BX0, BX1, y0, y0, True)          # 天井
        fill_rect(g, BX0, BX1, y1, y1, True)           # 床
        fill_rect(g, BX0, BX0, y0, y1, True)           # 左壁
        fill_rect(g, BX1, BX1, y0, y1, True)           # 右壁
    if wipe_top is not None:
        fill_rect(g, BX0, BX1, BY0, min(BY1, BY0 + wipe_top - 1), False)
    return g


# ---------------------------------------------------------------------------
# おたまじゃくし（エレベーター再登場演出）: 丸い頭 + くねる尻尾
# ---------------------------------------------------------------------------

def tadpole(hx, hy, wiggle=0, ch="X"):
    g = blank()
    for x in range(hx, hx + 3):                 # 頭（3x2）
        for y in (hy, hy + 1):
            put(g, x, y, ch)
    # 尻尾（頭から右へ、wiggle で上下にくねる）
    tx = hx + 3
    for i in range(7):
        ty = hy + (1 if (i + wiggle) % 2 == 0 else 0)
        put(g, tx + i, ty, ch)
    return g


# ---------------------------------------------------------------------------
# 各状態のフレーム定義
# ---------------------------------------------------------------------------

def make_seqs(rb, sp="X"):
    """rb: ロボットを描く関数（robot / gpu_robot）、sp: おたまじゃくしの色"""
    IDLE = [rb()]                                              # 0: 微動だにしない

    SWAY = [rb(lean=0), rb(lean=1), rb(lean=0), rb(lean=-1)]   # 1: ゆらゆら

    BOUNCE = [rb(crouch=0), rb(crouch=1)]                    # 2/3: EDMドゥンドゥン（③は再生間隔だけ速める）

    # 4: 最高潮（80%超え、退勤まで粘っている間）— 万歳したまま、沈んで溜め→跳ねる、を左右交互に
    #    腕は上げっぱなし（跳ねるたびに上げ下げしない）
    CLIMAX = [rb(banzai=True, crouch=1), rb(banzai=True, hop=True),
              rb(banzai=True, crouch=1), rb(banzai=True, hop=True, lean=1)]

    BLANK = [blank()]                                              # 4: 職務放棄・完全に消えた状態

    # --- 職務放棄シーケンス（0/1/2/3 → 4 へ入るときに1回だけ再生） ---
    _box_closed_full_with_robot = overlay(rb(), box("closed"))
    VANISH = [
        rb(),                                                    # 通常姿勢
        overlay(rb(), box("closed", grow=6)),                    # 箱が上からせり出してくる
        overlay(rb(), box("closed", grow=12)),
        _box_closed_full_with_robot,                                # 箱、着地・閉
        overlay(rb(), box("open")),                              # 扉が開く
        overlay(rb(dx=8, compact=True), box("open")),             # ロボットが箱へ歩み寄る
        overlay(rb(dx=15, compact=True), box("open")),            # 箱の中に完全に入る
        box("closed"),                                              # 扉が閉まる（ロボット見えなくなる）
        box("closed", wipe_top=9),                                  # 箱が上へスライドして消えていく
        blank(),                                                    # 元の場所は空白になって、無くなる
    ]

    # --- 復帰シーケンス（4 → 0/1/2/3 へ戻るときに1回だけ再生・エレベーター×おたまじゃくし） ---
    _box_closed_full_empty = box("closed")
    REAPPEAR = [
        blank(),
        box("closed", grow=6),                                      # 箱が降ってくる
        box("closed", grow=12),
        _box_closed_full_empty,                                     # 着地・閉（中身はまだ見えない）
        overlay(tadpole(19, 8, wiggle=0, ch=sp), box("open")),                # 扉が開く…中にはおたまじゃくし
        overlay(tadpole(12, 8, wiggle=1, ch=sp), box("open")),                # 泳いで出てくる（くねり1）
        overlay(tadpole(5, 8, wiggle=0, ch=sp), box("open")),                 # くねり2、ロボットの定位置まで到達
        overlay(rb(), box("open")),                               # 変態完了＝ロボットの姿に
        _box_closed_full_with_robot,                                 # 扉が閉まる（ロボットは外＝定位置）
        overlay(rb(), box("closed", wipe_top=9)),                 # 箱が上へスライドして去っていく
        rb(),                                                     # 箱は消え、ロボットだけが残る
    ]
    return {
        "idle": IDLE, "sway": SWAY, "bounce": BOUNCE, "climax": CLIMAX,
        "blank": BLANK, "vanish": VANISH, "reappear": REAPPEAR,
    }


CPU_SEQS = make_seqs(robot, sp="d")   # 黒いおたまじゃくしが黒いケーブルのロボットに変態する
GPU_SEQS = make_seqs(gpu_robot, sp="G")   # 緑のおたまじゃくしが緑のロボットに変態する




# ---------------------------------------------------------------------------
# PNG出力（依存なし）
# ---------------------------------------------------------------------------

def write_png(path, pixels, w, h):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    raw = b""
    for y in range(h):
        raw += b"\x00" + bytes(v for x in range(w) for v in pixels[y][x])
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw))
           + chunk(b"IEND", b""))
    open(path, "wb").write(png)


# プレビューの色（main.m の描画色と揃える）
PALETTE = {
    True:  {"X": (235, 235, 240), "S": (196, 202, 210), "G": (46, 204, 92), "R": (255, 48, 48),
            # 暗いバーでは背景に沈むので、強めの光が当たっている想定で明暗の幅ごと持ち上げる（つやは足さない）
            "a": (22, 22, 24), "b": (46, 46, 50), "c": (68, 68, 73), "d": (94, 94, 100), "e": (122, 122, 128),
            "f": (172, 174, 180), "bg": (28, 30, 40)},
    False: {"X": (20, 20, 25), "S": (128, 134, 142), "G": (24, 160, 64), "R": (225, 30, 30),
            "a": (6, 6, 8), "b": (20, 20, 23), "c": (36, 36, 40), "d": (56, 56, 61), "e": (78, 78, 84),
            "f": (112, 114, 120), "bg": (236, 236, 240)},
}


def render_sheet(path, frames, scale=10, gap=2, cols=None, dark=True):
    pal = PALETTE[dark]
    n = len(frames)
    cols = cols or n
    rows_n = (n + cols - 1) // cols
    sw = cols * (W + gap) * scale
    sh = rows_n * (H + 2) * scale
    px = [[(120, 120, 130) for _ in range(sw)] for _ in range(sh)]
    for i, fr in enumerate(frames):
        rr, cc = divmod(i, cols)
        ox = cc * (W + gap) * scale
        oy = rr * (H + 2) * scale
        for r in range(H):
            for c in range(W):
                col = pal.get(fr[r][c], pal["bg"])
                for dy in range(scale):
                    for dx in range(scale):
                        px[oy + (r + 1) * scale + dy][ox + c * scale + dx] = col
    write_png(path, px, sw, sh)


# ---------------------------------------------------------------------------
# main.m 用 C配列ダンプ
# ---------------------------------------------------------------------------

def dump_c_array(name, frames):
    lines = [f"static const char *{name}[{len(frames)}][{H}] = {{"]
    for fr in frames:
        lines.append("    {")
        for row in rows_of(fr):
            lines.append(f'        "{row}",')
        lines.append("    },")
    lines.append("};")
    return "\n".join(lines)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sheet"
    if cmd == "sheet":
        # python3 frames.py sheet out.png [seq] [cpu|gpu] [light]
        out = sys.argv[2] if len(sys.argv) > 2 else "sheet.png"
        seq = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "all" else None
        seqs = GPU_SEQS if len(sys.argv) > 4 and sys.argv[4] == "gpu" else CPU_SEQS
        dark = not (len(sys.argv) > 5 and sys.argv[5] == "light")
        frames = seqs[seq] if seq else [f for k in ("idle", "sway", "bounce", "climax", "vanish", "reappear") for f in seqs[k]]
        render_sheet(out, frames, cols=6, dark=dark)
        print(f"done: {out} ({len(frames)} frames)")
    elif cmd == "dump":
        for prefix, seqs in (("k", CPU_SEQS), ("kGpu", GPU_SEQS)):
            for key, name in (("idle", "Idle"), ("sway", "Sway"), ("bounce", "Bounce"),
                              ("climax", "Climax"), ("blank", "Blank"),
                              ("vanish", "Vanish"), ("reappear", "Reappear")):
                if prefix == "kGpu" and key == "blank":
                    continue  # 空白は共通
                print(dump_c_array(prefix + name, seqs[key]))
