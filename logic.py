from typing import List, Optional, Tuple
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import io
from PIL import Image, ImageDraw, ImageFont
import base64
import colorsys


def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """
    Validates the API key by sending a simple question to Gemini.
    Returns (True, response) on success, or (False, error message) on failure.
    """
    if not api_key or not api_key.strip():
        return False, "Key is empty"

    try:
        client = genai.Client(api_key=api_key)
        interaction = client.interactions.create(
            model="gemini-3.5-flash-lite",
            input="1 + 1 = ?",
        )
        text = interaction.output_text
        if not text or not text.strip():
            return False, "No response received from Gemini"
        return True, text
    except Exception as e:
        return False, str(e)


def open_static_prompt_file(file_path: str) -> str:
    """Open and read the contents of a static prompt file."""
    with open(file_path, "r") as f:
        return f.read()


def convert_image_to_webp_bytes(input_path, quality=80):
    """
    Convert an image to WEBP format and return the image as bytes.
    """
    with Image.open(input_path) as img:
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "transparency" in img.info or img.mode == "P" else "RGB")

        clean_img = Image.new(img.mode, img.size)
        clean_img.paste(img)

        output_buffer = io.BytesIO()

        clean_img.save(
            output_buffer,
            format="WEBP",
            quality=quality,
            method=2
        )

        image_bytes = output_buffer.getvalue()
    return image_bytes


def image_to_base64(Bytes: str) -> str:
    """Convert an image to a base64 string."""
    return base64.b64encode(Bytes).decode("utf-8")


def get_color_palette_from_image(image_base64: str, api_key: str, static_prompt: str) -> List[str]:
    """Get a color palette from an image using the Gemini API."""
    client = genai.Client(api_key=api_key)

    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        system_instruction=static_prompt,
        input=[
        {"type": "text", "text": "Give me a ColorPalette with 5 colors for LightTheme and 5 colors for DarkTheme from this is image Return the output in JSON format."},
        {
            "type": "image",
            "data": image_base64,
            "mime_type": "image/webp",
        },
    ],
    generation_config={
        "temperature": 0.0,
    },
    response_format={
        "type": "text",
        "mime_type": "application/json",
    },
)
    return interaction.output_text


def generate_palettes_images(themes_dict, ImageConfig=None):
    """
    Generates a PNG image for each theme and returns a dict {theme_name: png_bytes}.
    themes_dict : {"ThemeName": {"PRIMARY": "#hex", "ACCENT": "#hex", ...}, ...}
    ImageConfig : Simple visual settings only (all values optional).
    """
    cfg = {
        "font_name": "Alexandria-Bold.ttf",
        "font_title_size": 34,
        "font_label_size": 17,
        "font_footer_size": 15,
        "app_name": "Palettes V1",
        "template_name": "Template 001 - Palettes Generator",
        "save_dir": None,
    }
    if ImageConfig:
        cfg.update(ImageConfig)

    WIDTH, HEIGHT = 1000, 600
    CARD_BOX = (40, 40, 960, 560)
    LABELS = ("PRIMARY", "SECONDARY", "ACCENT", "NEUTRALS", "SEMANTIC")
    DEFAULTS = {
        "PRIMARY":   "#3b82f6",
        "SECONDARY": "#64748b",
        "ACCENT":    "#f59e0b",
        "NEUTRALS":  "#94a3b8",
        "SEMANTIC":  "#10b981",
    }
    BOX_SIZE, GAP = 50, 10
    PRIMARY_INDEX = 3
    ROW_HEIGHT, Y_START = 70, 160
    DIVIDER_X = 485
    GRID_START_X = 925 - (7 * BOX_SIZE + 6 * GAP)

    try:
        font_title = ImageFont.truetype(cfg["font_name"], cfg["font_title_size"])
        font_label = ImageFont.truetype(cfg["font_name"], cfg["font_label_size"])
        font_footer = ImageFont.truetype(cfg["font_name"], cfg["font_footer_size"])
    except OSError:
        fallback = ImageFont.load_default()
        font_title = font_label = font_footer = fallback

    def hex_to_rgb(h):
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    def rgb_to_hex(r, g, b):
        return "#{:02x}{:02x}{:02x}".format(
            max(0, min(255, int(r))),
            max(0, min(255, int(g))),
            max(0, min(255, int(b))),
        )

    def shades(base_hex):
        try:
            r, g, b = hex_to_rgb(base_hex)
        except (ValueError, IndexError):
            base_hex = "#969696"
            r = g = b = 150
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        out = []
        for i in (3, 2, 1):
            nl = min(1.0, l + (1.0 - l) * (i / 4.0))
            nr, ng, nb = colorsys.hls_to_rgb(h, nl, s)
            out.append(rgb_to_hex(nr * 255, ng * 255, nb * 255))
        out.append(base_hex)
        for i in (1, 2, 3):
            nl = max(0.0, l * (1.0 - i / 4.0))
            nr, ng, nb = colorsys.hls_to_rgb(h, nl, s)
            out.append(rgb_to_hex(nr * 255, ng * 255, nb * 255))
        return out

    save_dir = cfg["save_dir"]
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)

    results = {}
    for theme_name, theme_data in themes_dict.items():
        img = Image.new("RGB", (WIDTH, HEIGHT), "#ffffff")
        draw = ImageDraw.Draw(img)

        draw.rounded_rectangle(CARD_BOX, radius=20, fill="#ffffff",
                               outline="#0f172a", width=3)
        draw.text((75, 68), str(theme_name), fill="#0f172a", font=font_title)
        draw.text((820, 76), cfg["app_name"], fill="#475569", font=font_label)
        draw.line([(75, 130), (925, 130)], fill="#e2e8f0", width=2)
        draw.line([(DIVIDER_X, 150), (DIVIDER_X, 500)], fill="#cbd5e1", width=2)

        for i, label in enumerate(LABELS):
            y_pos = Y_START + i * ROW_HEIGHT
            draw.text((75, y_pos + 12), label, fill="#1e293b", font=font_label)
            base_color = theme_data.get(label, DEFAULTS[label])
            for col, color_hex in enumerate(shades(base_color)):
                bx = GRID_START_X + col * (BOX_SIZE + GAP)
                by = y_pos + 4
                is_primary = (col == PRIMARY_INDEX)
                draw.rounded_rectangle(
                    [bx, by, bx + BOX_SIZE, by + BOX_SIZE],
                    radius=8,
                    fill=color_hex,
                    outline="#0f0f0f" if is_primary else "#cbd5e1",
                    width=3 if is_primary else 1,
                )

        draw.line([(75, 515), (925, 515)], fill="#e2e8f0", width=2)
        draw.text((75, 528), cfg["template_name"], fill="#64748b", font=font_footer)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png = buf.getvalue()
        results[theme_name] = png

        if save_dir:
            path = os.path.join(save_dir, f"{theme_name.lower()}_palette.png")
            with open(path, "wb") as f:
                f.write(png)

    return results