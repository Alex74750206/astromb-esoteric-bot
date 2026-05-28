"""Генерация астрологических изображений для бота."""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont

ASSETS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets"))
os.makedirs(ASSETS, exist_ok=True)

WELCOME_PATH = os.path.join(ASSETS, "welcome_banner.jpg")
PROFILE_PATH = os.path.join(ASSETS, "profile_photo.jpg")

# Palette
_BG_TOP    = (6,  3,  28)
_BG_MID    = (14, 7,  55)
_BG_BOT    = (10, 20, 62)
_GOLD      = (212, 175, 55)
_GOLD_LT   = (255, 218, 90)
_GOLD_DIM  = (120, 95,  22)
_SILVER    = (195, 210, 240)
_LAVENDER  = (160, 140, 230)

_FONT_REG  = r"C:\Windows\Fonts\arial.ttf"
_FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
_FONT_SYM  = r"C:\Windows\Fonts\seguisym.ttf"

ZODIAC_SIGNS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]


def _f(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _gradient_bg(w, h):
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    stops = [(0.0, _BG_TOP), (0.45, _BG_MID), (1.0, _BG_BOT)]
    for y in range(h):
        t = y / max(h - 1, 1)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                f = (t - t0) / (t1 - t0)
                r = int(c0[0] + f * (c1[0] - c0[0]))
                g = int(c0[1] + f * (c1[1] - c0[1]))
                b = int(c0[2] + f * (c1[2] - c0[2]))
                draw.line([(0, y), (w, y)], fill=(r, g, b))
                break
    return img, draw


def _stars(draw, w, h, n=380, seed=7):
    random.seed(seed)
    for _ in range(n):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        sz = random.choices([0, 0, 0, 1, 1, 2], weights=[5, 5, 5, 3, 3, 1])[0]
        br = random.randint(130, 255)
        c = (min(255, br - 8), min(255, br - 3), br)
        if sz == 0:
            draw.point((x, y), fill=c)
        else:
            draw.ellipse([x, y, x + sz, y + sz], fill=c)

    # Bright cross-sparkles
    random.seed(13)
    for _ in range(10):
        x = random.randint(30, w - 30)
        y = random.randint(30, h - 30)
        c = (255, 248, 210)
        draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=c)
        draw.line([(x - 8, y), (x + 8, y)], fill=(*c[:3],), width=1)
        draw.line([(x, y - 8), (x, y + 8)], fill=(*c[:3],), width=1)


def _zodiac_wheel(draw, cx, cy, R):
    inner_R = R - 34
    sign_R  = R - 17

    f_sign = _f(_FONT_SYM, 17)
    f_moon = _f(_FONT_SYM, 34)

    # Soft glow rings behind wheel
    for gr in range(R + 30, R - 10, -4):
        fade = max(0, 60 - (gr - (R - 10)) * 2)
        if fade > 0:
            draw.ellipse(
                [cx - gr, cy - gr, cx + gr, cy + gr],
                outline=(70, 30, 140),
                width=1,
            )

    # Main rings
    draw.ellipse([cx - R, cy - R, cx + R, cy + R], outline=_GOLD, width=2)
    draw.ellipse(
        [cx - inner_R, cy - inner_R, cx + inner_R, cy + inner_R],
        outline=_GOLD_DIM,
        width=1,
    )

    for i in range(12):
        a     = math.radians(i * 30 - 90)
        a_mid = math.radians(i * 30 - 90 + 15)

        # Segment tick
        x1 = cx + inner_R * math.cos(a)
        y1 = cy + inner_R * math.sin(a)
        x2 = cx + R * math.cos(a)
        y2 = cy + R * math.sin(a)
        draw.line([(x1, y1), (x2, y2)], fill=_GOLD, width=2)

        # Small diamond dot on outer ring
        dm = 3
        dx = cx + (R + 6) * math.cos(a)
        dy = cy + (R + 6) * math.sin(a)
        draw.polygon(
            [(dx, dy - dm), (dx + dm, dy), (dx, dy + dm), (dx - dm, dy)],
            fill=_GOLD_LT,
        )

        # Zodiac glyph in slot
        sx = cx + sign_R * math.cos(a_mid)
        sy = cy + sign_R * math.sin(a_mid)
        try:
            bbox = draw.textbbox((0, 0), ZODIAC_SIGNS[i], font=f_sign)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text((sx - tw / 2, sy - th / 2), ZODIAC_SIGNS[i], font=f_sign, fill=_GOLD_LT)
        except Exception:
            pass

    # Center fill
    cr = 42
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(10, 5, 40), outline=_GOLD, width=2)

    # Crescent moon in center
    try:
        bbox = draw.textbbox((0, 0), "☽", font=f_moon)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((cx - tw / 2, cy - th / 2), "☽", font=f_moon, fill=_GOLD_LT)
    except Exception:
        # geometric fallback
        draw.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=_GOLD_LT)
        draw.ellipse([cx - 6,  cy - 16, cx + 24, cy + 16], fill=(10, 5, 40))


def _text_centered(draw, y, text, font, fill, w):
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) / 2, y), text, font=font, fill=fill)
    except Exception:
        draw.text((10, y), text, font=font, fill=fill)


# ─────────────────────────────────────────────────────────────────────────────

def create_welcome_banner() -> str:
    W, H = 1200, 600
    img, draw = _gradient_bg(W, H)
    _stars(draw, W, H, n=420, seed=5)

    # Left — zodiac wheel
    _zodiac_wheel(draw, 300, 300, 225)

    # Small accent wheel — bottom-right corner, faded
    _zodiac_wheel(draw, 1110, 510, 88)

    # Vertical golden separator
    for yy in range(55, 545):
        alpha = 0.35 + 0.65 * math.sin(math.pi * (yy - 55) / 490)
        c = tuple(int(v * alpha) for v in _GOLD_DIM)
        draw.point((575, yy), fill=c)

    # ─ Text block ─
    f_small  = _f(_FONT_REG,  19)
    f_mid    = _f(_FONT_REG,  24)
    f_sub    = _f(_FONT_BOLD, 36)
    f_title  = _f(_FONT_BOLD, 64)

    tx = 600   # left edge of text area

    def rtext(y, text, font, fill):
        draw.text((tx, y), text, font=font, fill=fill)

    rtext(58,  "Ваш персональный", f_sub,   _SILVER)
    rtext(102, "АСТРОЛОГ",         f_title, _GOLD_LT)

    # Decorative gold line
    draw.line([(tx, 180), (tx + 530, 180)], fill=_GOLD_DIM, width=1)

    services = [
        ("•", "Нумерология — число судьбы"),
        ("•", "Матрица судьбы — 9 ключей жизни"),
        ("•", "Натальная карта по планетам"),
        ("•", "Ба Цзы  •  Гороскоп 2026"),
    ]
    for k, (bullet, line) in enumerate(services):
        rtext(198 + k * 36, bullet, f_mid, _GOLD_LT)
        draw.text((tx + 22, 198 + k * 36), line, font=f_mid, fill=_SILVER)

    draw.line([(tx, 346), (tx + 530, 346)], fill=_GOLD_DIM, width=1)

    rtext(362, "Начните бесплатно",       f_sub,   _GOLD_LT)
    rtext(406, "прямо сейчас — это займёт 30 секунд",  f_mid,   _SILVER)
    rtext(444, "Число Судьбы  •  Разбор мгновенно",    f_small, _LAVENDER)
    rtext(474, "Оплата через Telegram Stars",           f_small, _LAVENDER)

    # Outer decorative frame
    draw.rectangle([(6, 6), (W - 6, H - 6)], outline=_GOLD_DIM, width=1)
    draw.rectangle([(2, 2), (W - 2, H - 2)], outline=(40, 30, 80), width=2)

    img.save(WELCOME_PATH, "JPEG", quality=96)
    return WELCOME_PATH


def create_profile_photo() -> str:
    S = 800
    img, draw = _gradient_bg(S, S)
    _stars(draw, S, S, n=280, seed=11)

    cx = cy = S // 2
    _zodiac_wheel(draw, cx, cy, 300)

    # Bot name below wheel
    f_name = _f(_FONT_BOLD, 34)
    f_tag  = _f(_FONT_REG,  21)
    _text_centered(draw, cy + 320, "Астролог  |  Нумеролог", f_name, _GOLD_LT, S)
    _text_centered(draw, cy + 362, "Разбор по дате рождения", f_tag,  _LAVENDER, S)

    draw.rectangle([(4, 4), (S - 4, S - 4)], outline=_GOLD_DIM, width=1)

    img.save(PROFILE_PATH, "JPEG", quality=96)
    return PROFILE_PATH


if __name__ == "__main__":
    p1 = create_welcome_banner()
    p2 = create_profile_photo()
    print(f"Banner : {p1}")
    print(f"Profile: {p2}")
