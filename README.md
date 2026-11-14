# 🎨 Palettes Generator

Extract professional **Light & Dark** UI color palettes from any image using Google Gemini — straight to PNG previews.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 👀 Preview

| Light Theme | Dark Theme |
|:---:|:---:|
| ![Light](images/l_theme.png) | ![Dark](images/d_theme.png) |

---

## ✨ What It Does

Pick an image → get 5 WCAG-compliant color tokens (PRIMARY, SECONDARY, ACCENT, NEUTRALS, SEMANTIC) for both themes → saved as ready-to-use PNGs.

---

## 📦 Install

__
git clone https://github.com/USERNAME/palettes-generator.git
cd palettes-generator
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
__

Then open __.env__ and add your key:
__
GEMINI_API_KEY=your_actual_key_here
__

Get a free key from [Google AI Studio](https://aistudio.google.com/app/apikey).

---

## 🚀 Run

__
python main.py
__

---

## 🗂 Files

| File | Role |
|---|---|
| __main.py__ | GUI (CustomTkinter) — screens, flow, threading |
| __logic.py__ | API calls, image → WEBP, palette PNG rendering |
| __StaticPrompt.md__ | Strict system prompt forcing valid JSON output |
| __requirements.txt__ | Dependencies |
| __.env.example__ | Template for your API key |

---

## 🖼 Build EXE

__
pyinstaller --onedir --windowed --noconfirm --collect-all customtkinter --collect-all google.genai --name "Palettes Generator" main.py
__

Copy __StaticPrompt.md__, __.env__, and __Alexandria-Bold.ttf__ into __dist/Palettes Generator/__.

---

## 📄 License

MIT © 2025 — free to use, modify, and distribute; keep the copyright notice, no warranty.
