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


def fill_rect(grid, x0, x1, y0, y1, on=True):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            set_px(grid, x, y, on)


def overlay(base, other):
    """other の 'X' を base に重ねる（other の '.' は透過＝base をそのまま残す）"""
    g = [row[:] for row in base]
    for y in range(H):
        for x in range(W):
            if other[y][x] == "X":
                g[y][x] = "X"
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

def robot(dx=0, lean=0, crouch=0, compact=False, banzai=False, hop=False):
    """dx: 全体の横シフト（エレベーターへの移動用）
       lean: 上半身（頭・首・胴・腕）だけを足に対して左右にずらす（ゆらゆら用）
       crouch: 上半身を1px落として脚を1px縮める（EDMのドゥンドゥン用）
       compact: 腕とアンテナを省いた細身シルエット（エレベーターに入る用）
       banzai: 腕を頭の横まで振り上げる（最高潮用）
       hop: 足先を1px浮かせる＝跳ねた瞬間（最高潮用）
    """
    g = blank()

    # 脚（常に基準位置、crouch分だけ短縮）
    leg_top = 13 + crouch
    leg_bot = 16 if hop else 17
    if leg_top <= leg_bot:
        fill_rect(g, 4 + dx, 5 + dx, leg_top, leg_bot, True)
        fill_rect(g, 8 + dx, 9 + dx, leg_top, leg_bot, True)

    ux = dx + lean  # 上半身のx
    uy = crouch      # 上半身のyオフセット

    if not compact:
        # アンテナ
        set_px(g, 7 + ux, 0 + uy, True)
        set_px(g, 7 + ux, 1 + uy, True)
    # 頭
    fill_rect(g, 4 + ux, 9 + ux, 2 + uy, 5 + uy, True)
    # 目穴（透過）
    set_px(g, 5 + ux, 3 + uy, False)
    set_px(g, 8 + ux, 3 + uy, False)
    # 首
    fill_rect(g, 6 + ux, 7 + ux, 6 + uy, 6 + uy, True)
    # 胴
    fill_rect(g, 2 + ux, 11 + ux, 7 + uy, 12 + uy, True)
    if banzai:
        # 振り上げた腕（肩から頭の横へ）
        fill_rect(g, 0 + ux, 1 + ux, 1 + uy, 7 + uy, True)
        fill_rect(g, 12 + ux, 13 + ux, 1 + uy, 7 + uy, True)
    elif not compact:
        # 腕
        fill_rect(g, 0 + ux, 1 + ux, 7 + uy, 11 + uy, True)
        fill_rect(g, 12 + ux, 13 + ux, 7 + uy, 11 + uy, True)

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
# 精子（エレベーター再登場演出）: 丸い頭 + くねる尻尾
# ---------------------------------------------------------------------------

def sperm(hx, hy, wiggle=0):
    g = blank()
    fill_rect(g, hx, hx + 2, hy, hy + 1, True)  # 頭（3x2）
    # 尻尾（頭から右へ、wiggle で上下にくねる）
    tx = hx + 3
    for i in range(7):
        ty = hy + (1 if (i + wiggle) % 2 == 0 else 0)
        set_px(g, tx + i, ty, True)
    return g


# ---------------------------------------------------------------------------
# 各状態のフレーム定義
# ---------------------------------------------------------------------------

IDLE = [robot()]                                              # 0: 微動だにしない

SWAY = [robot(lean=0), robot(lean=1), robot(lean=0), robot(lean=-1)]   # 1: ゆらゆら

BOUNCE = [robot(crouch=0), robot(crouch=1)]                    # 2/3: EDMドゥンドゥン（③は再生間隔だけ速める）

# 4: 最高潮（80%超え、退勤まで粘っている間）— 万歳したまま、沈んで溜め→跳ねる、を左右交互に
#    腕は上げっぱなし（跳ねるたびに上げ下げしない）
CLIMAX = [robot(banzai=True, crouch=1), robot(banzai=True, hop=True),
          robot(banzai=True, crouch=1), robot(banzai=True, hop=True, lean=1)]

BLANK = [blank()]                                              # 4: 職務放棄・完全に消えた状態

# --- 職務放棄シーケンス（0/1/2/3 → 4 へ入るときに1回だけ再生） ---
_box_closed_full_with_robot = overlay(robot(), box("closed"))
VANISH = [
    robot(),                                                    # 通常姿勢
    overlay(robot(), box("closed", grow=6)),                    # 箱が上からせり出してくる
    overlay(robot(), box("closed", grow=12)),
    _box_closed_full_with_robot,                                # 箱、着地・閉
    overlay(robot(), box("open")),                              # 扉が開く
    overlay(robot(dx=8, compact=True), box("open")),             # ロボットが箱へ歩み寄る
    overlay(robot(dx=15, compact=True), box("open")),            # 箱の中に完全に入る
    box("closed"),                                              # 扉が閉まる（ロボット見えなくなる）
    box("closed", wipe_top=9),                                  # 箱が上へスライドして消えていく
    blank(),                                                    # 元の場所は空白になって、無くなる
]

# --- 復帰シーケンス（4 → 0/1/2/3 へ戻るときに1回だけ再生・エレベーター×精子） ---
_box_closed_full_empty = box("closed")
REAPPEAR = [
    blank(),
    box("closed", grow=6),                                      # 箱が降ってくる
    box("closed", grow=12),
    _box_closed_full_empty,                                     # 着地・閉（中身はまだ見えない）
    overlay(sperm(19, 8, wiggle=0), box("open")),                # 扉が開く…中には精子
    overlay(sperm(12, 8, wiggle=1), box("open")),                # 泳いで出てくる（くねり1）
    overlay(sperm(5, 8, wiggle=0), box("open")),                 # くねり2、ロボットの定位置まで到達
    overlay(robot(), box("open")),                               # 変態完了＝ロボットの姿に
    _box_closed_full_with_robot,                                 # 扉が閉まる（ロボットは外＝定位置）
    overlay(robot(), box("closed", wipe_top=9)),                 # 箱が上へスライドして去っていく
    robot(),                                                     # 箱は消え、ロボットだけが残る
]


ALL_SEQS = {
    "idle": IDLE,
    "sway": SWAY,
    "bounce": BOUNCE,
    "climax": CLIMAX,
    "blank": BLANK,
    "vanish": VANISH,
    "reappear": REAPPEAR,
}


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


def render_sheet(path, frames, scale=10, gap=2, cols=None):
    n = len(frames)
    cols = cols or n
    rows_n = (n + cols - 1) // cols
    sw = cols * (W + gap) * scale
    sh = rows_n * (H + 2) * scale
    px = [[(240, 240, 245) for _ in range(sw)] for _ in range(sh)]
    for i, fr in enumerate(frames):
        rr, cc = divmod(i, cols)
        ox = cc * (W + gap) * scale
        oy = rr * (H + 2) * scale
        for r in range(H):
            for c in range(W):
                col = (20, 20, 25) if fr[r][c] == "X" else (255, 255, 255)
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
        out = sys.argv[2] if len(sys.argv) > 2 else "sheet.png"
        seq = sys.argv[3] if len(sys.argv) > 3 else None
        frames = ALL_SEQS[seq] if seq else (IDLE + SWAY + BOUNCE + VANISH + REAPPEAR)
        render_sheet(out, frames, cols=6)
        print(f"done: {out} ({len(frames)} frames)")
    elif cmd == "dump":
        print(dump_c_array("kIdle", IDLE))
        print(dump_c_array("kSway", SWAY))
        print(dump_c_array("kBounce", BOUNCE))
        print(dump_c_array("kClimax", CLIMAX))
        print(dump_c_array("kBlank", BLANK))
        print(dump_c_array("kVanish", VANISH))
        print(dump_c_array("kReappear", REAPPEAR))
