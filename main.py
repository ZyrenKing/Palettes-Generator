import customtkinter as ctk
from tkinter import filedialog, messagebox
import os, sys, json, ast, shutil, threading
from dotenv import load_dotenv

from logic import (
    validate_api_key,
    open_static_prompt_file,
    convert_image_to_webp_bytes,
    image_to_base64,
    get_color_palette_from_image,
    generate_palettes_images,
)

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROMPT_FILE = os.path.join(BASE_DIR, "StaticPrompt.md")
ENV_FILE    = os.path.join(BASE_DIR, ".env")
FONT_FILE   = os.path.join(BASE_DIR, "Alexandria-Bold.ttf")
FONT_FAMILY = "Alexandria"

LABELS = ("PRIMARY", "SECONDARY", "ACCENT", "NEUTRALS", "SEMANTIC")
DEFAULTS = {
    "PRIMARY": "#3b82f6", "SECONDARY": "#64748b", "ACCENT": "#f59e0b",
    "NEUTRALS": "#94a3b8", "SEMANTIC": "#10b981",
}

BG, CARD, BORDER = "#0f172a", "#1e293b", "#334155"
TEXT, MUTED      = "#f8fafc", "#94a3b8"
SUCCESS, ERROR   = "#22c55e", "#ef4444"


def _load_font():
    if os.path.exists(FONT_FILE) and sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.gdi32.AddFontResourceExW(FONT_FILE, 0x10, 0)
        except Exception:
            pass


_load_font()


def F(size, bold=False):
    return ctk.CTkFont(family=FONT_FAMILY, size=size,
                       weight="bold" if bold else "normal")


def is_file():
    return os.path.exists(PROMPT_FILE)


def save_api_key(key):
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, encoding="utf-8") as f:
            lines = f.readlines()
    new, found = [], False
    for line in lines:
        if line.strip().startswith("GEMINI_API_KEY"):
            new.append(f"GEMINI_API_KEY={key}\n")
            found = True
        else:
            new.append(line)
    if not found:
        new.append(f"GEMINI_API_KEY={key}\n")
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(new)
    os.environ["GEMINI_API_KEY"] = key


def parse_palette_json(text):
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("\n")[1:]
        if parts and parts[-1].strip().startswith("```"):
            parts = parts[:-1]
        text = "\n".join(parts).strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return ast.literal_eval(text)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Palettes Generator")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color=BG)
        self.startup()

    def startup(self):
        self._clear()
        self.geometry("900x400")
        self.resizable(False, False)

        box = ctk.CTkFrame(self, fg_color=BG)
        box.pack(fill="both", expand=True)
        ctk.CTkLabel(box, text="Checking...", font=F(20, True),
                     text_color=TEXT).pack(expand=True)

        threading.Thread(target=self._startup_check, daemon=True).start()

    def _startup_check(self):
        if not is_file():
            self.after(0, self.show_prompt_setup)
            return

        load_dotenv(ENV_FILE, override=True)
        key = os.getenv("GEMINI_API_KEY")
        if not key or not key.strip():
            self.after(0, lambda: self.show_api_setup(
                "API key not found. Please enter a valid key."))
            return

        ok, msg = validate_api_key(key)
        if ok:
            self.after(0, self.show_main)
        else:
            short = msg if len(msg) < 200 else msg[:200] + "..."
            self.after(0, lambda s=short: self.show_api_setup(
                f"Saved API key is invalid:\n{s}"))

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def show_prompt_setup(self):
        self._clear()
        self.geometry("900x400")
        self.resizable(False, False)
        self.setup_screen(
            title="Select StaticPrompt.md file",
            placeholder="File path...",
            browse=lambda: filedialog.askopenfilename(
                title="Select StaticPrompt.md",
                filetypes=[("Markdown", "*.md"), ("All files", "*.*")]),
            submit=self.save_prompt,
        )

    def show_api_setup(self, warning=None):
        self._clear()
        self.geometry("900x400")
        self.resizable(False, False)
        self.setup_screen(
            title="Add Gemini API Key",
            placeholder="Enter API key...",
            submit=self.save_api,
            secret=True,
            warning=warning,
        )

    def show_main(self):
        self._clear()
        self.geometry("900x750")
        self.resizable(False, False)
        self.main_screen()

    def setup_screen(self, title, placeholder, browse=None,
                     submit=None, secret=False, warning=None):
        box = ctk.CTkFrame(self, fg_color=BG)
        box.pack(fill="both", expand=True, padx=50, pady=50)

        ctk.CTkLabel(box, text=title, font=F(26, True),
                     text_color=TEXT).pack(pady=(40, 20))

        if warning:
            ctk.CTkLabel(box, text=warning, font=F(12),
                         text_color=ERROR, justify="center").pack(
                pady=(0, 15))

        row = ctk.CTkFrame(box, fg_color=BG)
        row.pack(fill="x")

        self.setup_entry = ctk.CTkEntry(
            row, placeholder_text=placeholder, font=F(13),
            height=42, fg_color=CARD, border_color=BORDER,
            text_color=TEXT, placeholder_text_color=MUTED,
            show="•" if secret else "",
        )
        self.setup_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        if browse:
            def do_browse():
                p = browse()
                if p:
                    self.setup_entry.delete(0, "end")
                    self.setup_entry.insert(0, p)
                    self.setup_next.configure(state="normal")

            ctk.CTkButton(row, text="...", width=50, height=42,
                          font=F(20, True),
                          command=do_browse).pack(side="left")

        self.setup_next = ctk.CTkButton(
            box, text="Next", state="disabled", height=46,
            font=F(14, True), command=submit)
        self.setup_next.pack(fill="x", pady=(25, 0))

        self.setup_entry.bind("<KeyRelease>", lambda e: self.setup_next.configure(
            state="normal" if self.setup_entry.get().strip() else "disabled"))

    def save_prompt(self):
        try:
            shutil.copy(self.setup_entry.get().strip(), PROMPT_FILE)
            self.startup()
        except Exception as e:
            messagebox.showerror("Error", f"Could not copy: {e}")

    def save_api(self):
        key = self.setup_entry.get().strip()
        if not key:
            return
        self.setup_next.configure(state="disabled", text="Verifying...")
        self.setup_entry.configure(state="disabled")
        threading.Thread(target=self._verify_api, args=(key,), daemon=True).start()

    def _verify_api(self, key):
        ok, msg = validate_api_key(key)

        def finish():
            if ok:
                save_api_key(key)
                self.show_main()
            else:
                self.setup_next.configure(state="normal", text="Next")
                self.setup_entry.configure(state="normal")
                short = msg if len(msg) < 200 else msg[:200] + "..."
                messagebox.showerror("API Error", short)

        self.after(0, finish)

    def main_screen(self):
        load_dotenv(ENV_FILE, override=True)

        body = ctk.CTkFrame(self, fg_color=BG)
        body.pack(fill="both", expand=True)

        ctk.CTkLabel(body, text="Palette", font=F(36, True),
                     text_color=TEXT).pack(fill="x", padx=30, pady=(20, 25))

        ctk.CTkLabel(body, text="Select Image", font=F(15, True),
                     text_color=MUTED, anchor="w").pack(
            fill="x", padx=30, pady=(0, 6))

        img_row = ctk.CTkFrame(body, fg_color=BG)
        img_row.pack(fill="x", padx=30, pady=(0, 15))

        self.image_entry = ctk.CTkEntry(
            img_row, placeholder_text="Image path...", font=F(13),
            height=42, fg_color=CARD, border_color=BORDER,
            text_color=TEXT, placeholder_text_color=MUTED,
        )
        self.image_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            img_row, text="Browse", width=100, height=42, font=F(14, True),
            command=lambda: self._browse(self.image_entry,
                lambda: filedialog.askopenfilename(
                    title="Select Image",
                    filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp"),
                               ("All files", "*.*")])),
        ).pack(side="left")

        ctk.CTkLabel(body, text="Select Output Folder", font=F(15, True),
                     text_color=MUTED, anchor="w").pack(
            fill="x", padx=30, pady=(0, 6))

        dir_row = ctk.CTkFrame(body, fg_color=BG)
        dir_row.pack(fill="x", padx=30, pady=(0, 20))

        self.dir_entry = ctk.CTkEntry(
            dir_row, placeholder_text="Output folder path...", font=F(13),
            height=42, fg_color=CARD, border_color=BORDER,
            text_color=TEXT, placeholder_text_color=MUTED,
        )
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            dir_row, text="Browse", width=100, height=42, font=F(14, True),
            command=lambda: self._browse(self.dir_entry,
                lambda: filedialog.askdirectory(title="Select Output Folder")),
        ).pack(side="left")

        self.generate_btn = ctk.CTkButton(
            body, text="Generate Palette", height=46,
            font=F(14, True), command=self.run_generate,
        )
        self.generate_btn.pack(fill="x", padx=30, pady=(10, 10))

        self.status = ctk.CTkLabel(body, text="", font=F(12),
                                   text_color=MUTED, anchor="w")
        self.status.pack(fill="x", padx=30, pady=(0, 15))

        self.results = ctk.CTkFrame(body, fg_color=BG)
        self.results.pack(fill="x", padx=30)

    def _browse(self, entry, fn):
        p = fn()
        if p:
            entry.delete(0, "end")
            entry.insert(0, p)

    def run_generate(self):
        img = self.image_entry.get().strip()
        out = self.dir_entry.get().strip()

        if not img:
            messagebox.showwarning("Warning", "Please select an image first.")
            return
        if not os.path.exists(img):
            messagebox.showerror("Error", "Image path does not exist.")
            return
        if not out:
            messagebox.showwarning("Warning", "Please select an output folder.")
            return

        self.generate_btn.configure(state="disabled", text="Processing...")
        self.status.configure(text="Analyzing image...", text_color=MUTED)

        threading.Thread(target=self.worker, args=(img, out), daemon=True).start()

    def worker(self, img, out):
        try:
            load_dotenv(ENV_FILE, override=True)
            key = os.getenv("GEMINI_API_KEY")
            if not key:
                raise ValueError("API key not found")

            prompt = open_static_prompt_file(PROMPT_FILE)
            b64    = image_to_base64(convert_image_to_webp_bytes(img))

            self.after(0, lambda: self.status.configure(
                text="Connecting to Gemini..."))

            palette = get_color_palette_from_image(b64, key, prompt)
            themes  = parse_palette_json(palette)

            self.after(0, lambda: self.status.configure(
                text="Generating images..."))

            generate_palettes_images(themes, ImageConfig={"save_dir": out})

            self.after(0, lambda: self.show_results(themes))
        except Exception as e:
            err = str(e)
            self.after(0, lambda: self.show_error(err))

    def show_error(self, msg):
        self.generate_btn.configure(state="normal", text="Generate Palette")
        short = msg if len(msg) < 200 else msg[:200] + "..."
        self.status.configure(text=f"Error: {short}", text_color=ERROR)
        messagebox.showerror("Error", short)

    def show_results(self, themes):
        self.status.configure(text="Generated successfully ✓", text_color=SUCCESS)
        self.generate_btn.configure(state="normal", text="Generate Palette")

        for w in self.results.winfo_children():
            w.destroy()

        for theme_name, colors in themes.items():
            ctk.CTkLabel(self.results, text=str(theme_name),
                         font=F(16, True), text_color=TEXT,
                         anchor="w").pack(fill="x", pady=(8, 6))

            row = ctk.CTkFrame(self.results, fg_color=BG)
            row.pack(fill="x", pady=(0, 15))
            for i in range(len(LABELS)):
                row.grid_columnconfigure(i, weight=1, uniform="col")

            for i, name in enumerate(LABELS):
                color = colors.get(name, DEFAULTS[name])
                if not (isinstance(color, str) and color.startswith("#")):
                    color = DEFAULTS[name]

                cell = ctk.CTkFrame(row, fg_color=BG)
                cell.grid(row=0, column=i, padx=4, sticky="nsew")

                box = ctk.CTkFrame(cell, fg_color=color, height=55,
                                   corner_radius=8, border_width=1,
                                   border_color=BORDER)
                box.pack(fill="x")
                box.pack_propagate(False)

                ctk.CTkLabel(cell, text=color, font=F(10),
                             text_color=MUTED).pack(pady=(4, 0))


if __name__ == "__main__":
    App().mainloop()