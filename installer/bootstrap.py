"""
WhisperLeaf Installer
Bootstraps a complete WhisperLeaf installation on Windows.
Packaged with PyInstaller — bundles the app zip and owl logo.
"""

import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import sys
import os
import shutil
import zipfile
import pathlib
import urllib.request
import time
import ctypes
import webbrowser
import datetime
import socket

# ── Log file (always written to the user's Desktop) ───────────────────────────
LOG_PATH = pathlib.Path(os.environ.get("USERPROFILE", "C:/Users/Public")) / "Desktop" / "whisperleaf-install.log"

def _log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass  # never let logging crash the installer

def log(msg):
    _log(msg)

def log_section(title):
    _log("")
    _log(f"{'─' * 50}")
    _log(f"  {title}")
    _log(f"{'─' * 50}")

# ── Install location ───────────────────────────────────────────────────────────
INSTALL_DIR = pathlib.Path(os.environ.get("LOCALAPPDATA", "C:/Users/Public")) / "WhisperLeaf"
APP_DIR = INSTALL_DIR / "app"
VENV_DIR = APP_DIR / ".venv"

PYTHON_MIN = (3, 10)
PYTHON_URL = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
OLLAMA_URL = "https://ollama.com/download/OllamaSetup.exe"
MODEL = "phi3:mini"
APP_PORT = 8000

# ── Steps ─────────────────────────────────────────────────────────────────────
STEPS = [
    ("python",  "Check Python"),
    ("app",     "Install WhisperLeaf files"),
    ("venv",    "Set up virtual environment"),
    ("deps",    "Install dependencies"),
    ("ollama",  "Check Ollama"),
    ("model",   "Download AI model (phi3:mini  ~2.2 GB)"),
    ("launch",  "Launch WhisperLeaf"),
]

# ── Palette ────────────────────────────────────────────────────────────────────
BG      = "#0f1419"
CARD    = "#161b22"
BORDER  = "#21262d"
FG      = "#e6edf3"
MUTED   = "#8b949e"
GREEN   = "#4ade80"
BLUE    = "#58a6ff"
RED     = "#f85149"
YELLOW  = "#d29922"

# ── Helpers ───────────────────────────────────────────────────────────────────

def resource(filename):
    """Return path to a bundled resource (works both frozen and dev)."""
    if hasattr(sys, "_MEIPASS"):
        return pathlib.Path(sys._MEIPASS) / filename
    # Dev: files sit next to this script or in the project root
    here = pathlib.Path(__file__).parent
    candidates = [here / filename, here.parent / "whisperleaf-site" / "downloads" / filename]
    for c in candidates:
        if c.exists():
            return c
    return here / filename  # will fail with a clear error later


def run(cmd, **kwargs):
    log(f"RUN: {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.stdout.strip():
        log(f"  stdout: {result.stdout.strip()[:400]}")
    if result.stderr.strip():
        log(f"  stderr: {result.stderr.strip()[:400]}")
    log(f"  exit: {result.returncode}")
    return result


def find_python():
    """Return a python executable that satisfies PYTHON_MIN, or None."""
    for exe in ("python", "python3", "py"):
        try:
            r = run([exe, "-c",
                     "import sys; v=sys.version_info; print(f'{v.major}.{v.minor}')"])
            if r.returncode == 0:
                major, minor = (int(x) for x in r.stdout.strip().split("."))
                if (major, minor) >= PYTHON_MIN:
                    return exe
        except FileNotFoundError:
            pass
    return None


def find_ollama():
    try:
        r = run(["ollama", "--version"])
        if r.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    local_exe = pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
    return local_exe.exists()


def make_reporthook(progress_fn, start_pct, end_pct, label):
    last = [0]
    def hook(block, block_size, total):
        if total <= 0:
            return
        pct = min(block * block_size / total, 1.0)
        value = start_pct + pct * (end_pct - start_pct)
        if abs(value - last[0]) >= 0.5:
            last[0] = value
            mb_done = block * block_size / 1_048_576
            mb_total = total / 1_048_576
            progress_fn(f"{label} — {mb_done:.0f} / {mb_total:.0f} MB", value)
    return hook


def is_installed():
    """True if a previous install completed successfully.

    Requires the venv python, the app source, AND at least one installed
    package (fastapi) so a partial/interrupted install is not mistaken for
    a complete one and sent straight to launch.
    """
    venv_python = VENV_DIR / "Scripts" / "python.exe"
    fastapi_marker = VENV_DIR / "Lib" / "site-packages" / "fastapi"
    return (
        venv_python.exists()
        and (APP_DIR / "src" / "main.py").exists()
        and fastapi_marker.exists()
    )


def is_running():
    """True if something is already listening on the app port."""
    try:
        with socket.create_connection(("127.0.0.1", APP_PORT), timeout=1):
            return True
    except OSError:
        return False


def create_shortcuts(app_dir):
    """Create a Desktop shortcut and Start Menu entry for WhisperLeaf."""
    bat = app_dir / "Start WhisperLeaf.bat"
    if not bat.exists():
        log(f"Skipping shortcuts — {bat} not found")
        return

    desktop = pathlib.Path(os.environ.get("USERPROFILE", "C:/Users/Public")) / "Desktop"
    start_menu = (
        pathlib.Path(os.environ.get("APPDATA", ""))
        / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    )

    lnk_desktop    = desktop    / "WhisperLeaf.lnk"
    lnk_start_menu = start_menu / "WhisperLeaf.lnk"

    # Use the bundled favicon.ico if available; fall back to no custom icon.
    icon_path = resource("favicon.ico")
    icon_line = f'$sc.IconLocation = "{icon_path}"' if icon_path.exists() else ""

    def shortcut_block(var, lnk):
        lines = [
            f'${var} = $ws.CreateShortcut("{lnk}")',
            f'${var}.TargetPath = "{bat}"',
            f'${var}.WorkingDirectory = "{app_dir}"',
            f'${var}.WindowStyle = 1',
            f'${var}.Description = "WhisperLeaf - Private Local AI"',
        ]
        if icon_line:
            lines.append(icon_line.replace("$sc.", f"${var}."))
        lines.append(f'${var}.Save()')
        return "\n".join(lines)

    ps_script = (
        "$ws = New-Object -ComObject WScript.Shell\n"
        + shortcut_block("sc1", lnk_desktop) + "\n"
        + shortcut_block("sc2", lnk_start_menu) + "\n"
    )

    tmp_ps = pathlib.Path(os.environ.get("TEMP", str(app_dir))) / "wl_shortcuts.ps1"
    try:
        tmp_ps.write_text(ps_script, encoding="utf-8-sig")
        r = run([
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(tmp_ps),
        ])
        if r.returncode == 0:
            log(f"Shortcuts created: {lnk_desktop}, {lnk_start_menu}")
        else:
            log(f"Warning: shortcut creation exited {r.returncode}")
    except Exception as exc:
        log(f"Warning: could not create shortcuts: {exc}")
    finally:
        try:
            tmp_ps.unlink(missing_ok=True)
        except Exception:
            pass


# ── Installation logic ────────────────────────────────────────────────────────

def install(update_step, update_status, update_progress, done_cb, error_cb):
    # Start fresh log for this run
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            f.write(f"WhisperLeaf Installer — {datetime.datetime.now()}\n")
            f.write(f"Python: {sys.version}\n")
            f.write(f"Frozen: {hasattr(sys, '_MEIPASS')}\n")
            f.write(f"MEIPASS: {getattr(sys, '_MEIPASS', 'n/a')}\n")
            f.write(f"INSTALL_DIR: {INSTALL_DIR}\n")
            f.write(f"APP_DIR: {APP_DIR}\n")
            f.write(f"VENV_DIR: {VENV_DIR}\n\n")
    except Exception as e:
        pass  # can't write log — proceed anyway

    try:
        # ── Already running? Just open the browser ─────────────────────────────
        if is_running():
            log("App already running on port 8000 — opening browser")
            for key, _ in STEPS:
                update_step(key, "done")
            update_progress(100)
            update_status("WhisperLeaf is already running — opening in your browser…")
            webbrowser.open(f"http://127.0.0.1:{APP_PORT}/chat")
            done_cb()
            return

        # ── Already installed? Skip straight to launch ─────────────────────────
        if is_installed():
            log("Existing install found — skipping to launch")
            for key, _ in STEPS[:-1]:   # mark everything except "launch" as done
                update_step(key, "done")
            update_progress(99)
            update_status("WhisperLeaf is already installed — launching…")

            venv_python = VENV_DIR / "Scripts" / "python.exe"
            update_step("launch", "running")
            bat = APP_DIR / "Start WhisperLeaf.bat"
            if bat.exists():
                subprocess.Popen(
                    ["cmd", "/c", str(bat)],
                    cwd=str(APP_DIR),
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            else:
                subprocess.Popen(
                    [str(venv_python), "-m", "uvicorn", "src.main:app",
                     "--host", "127.0.0.1", "--port", str(APP_PORT)],
                    cwd=str(APP_DIR),
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            create_shortcuts(APP_DIR)
            time.sleep(4)
            webbrowser.open(f"http://127.0.0.1:{APP_PORT}/chat")
            update_step("launch", "done")
            update_progress(100)
            done_cb()
            return

        # ── 1. Python ──────────────────────────────────────────────────────────
        log_section("STEP 1: Check Python")
        update_step("python", "running")
        update_status("Checking for Python…")
        py = find_python()
        if py:
            log(f"Python found: {py}")
            update_status(f"Python found ({py})")
            update_step("python", "done")
            update_progress(8)
        else:
            log("Python not found — will download installer")
            update_status("Python not found — downloading installer…")
            tmp = pathlib.Path(os.environ.get("TEMP", INSTALL_DIR)) / "python_installer.exe"
            urllib.request.urlretrieve(
                PYTHON_URL, tmp,
                reporthook=make_reporthook(
                    lambda msg, v: (update_status(msg), update_progress(v)),
                    2, 60, "Downloading Python"
                )
            )
            update_status("Installing Python (this takes a moment)…")
            update_progress(62)
            r = run([str(tmp), "/quiet", "InstallAllUsers=0",
                     "PrependPath=1", "Include_test=0", "Include_pip=1"])
            tmp.unlink(missing_ok=True)
            if r.returncode != 0:
                raise RuntimeError("Python installer failed. Please install Python 3.10+ manually from python.org.")
            py = find_python()
            if not py:
                py = "python"   # PATH update may need a restart; best effort
            update_status("Python installed.")
            update_step("python", "done")
            update_progress(70)

        # ── 2. Extract app files ───────────────────────────────────────────────
        log_section("STEP 2: Extract app files")
        update_step("app", "running")
        update_status("Installing WhisperLeaf…")
        zip_path = resource("whisperleaf-beta.zip")
        log(f"zip_path: {zip_path}  exists={zip_path.exists()}")
        if not zip_path.exists():
            raise RuntimeError(f"App bundle not found: {zip_path}")
        if APP_DIR.exists():
            try:
                shutil.rmtree(APP_DIR)
            except PermissionError as e:
                log(f"rmtree blocked ({e}) — installing on top of existing directory")
                # A locked .venv means deps are likely already installed;
                # is_installed() should have caught this, but proceed safely.
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            members = zf.namelist()
            total = len(members)
            for i, name in enumerate(members):
                # Strip the top-level whisperleaf-beta/ prefix
                parts = name.split("/", 1)
                dest_name = parts[1] if len(parts) == 2 else name
                if not dest_name:
                    continue
                dest = APP_DIR / dest_name
                if name.endswith("/"):
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(name) as src, open(dest, "wb") as out:
                        shutil.copyfileobj(src, out)
                pct = 70 + (i / total) * 6
                update_progress(pct)
        log(f"Extracted to: {APP_DIR}")
        update_status("WhisperLeaf files installed.")
        create_shortcuts(APP_DIR)
        update_step("app", "done")
        update_progress(76)

        # ── 3. Virtual environment ─────────────────────────────────────────────
        log_section("STEP 3: Virtual environment")
        update_step("venv", "running")
        if VENV_DIR.exists():
            log("venv already exists — reusing")
            update_status("Virtual environment already exists, reusing.")
        else:
            update_status("Creating virtual environment…")
            r = run([py, "-m", "venv", str(VENV_DIR)])
            if r.returncode != 0:
                raise RuntimeError(f"venv creation failed:\n{r.stderr}")
        update_step("venv", "done")
        update_progress(80)

        # Always use venv python to invoke pip — pip.exe may not exist right
        # after venv creation on all Windows configurations.
        venv_python = VENV_DIR / "Scripts" / "python.exe"
        log(f"venv_python: {venv_python}  exists={venv_python.exists()}")

        # ── 4. Dependencies ────────────────────────────────────────────────────
        log_section("STEP 4: Install dependencies")
        update_step("deps", "running")

        # Prefer the requirements.txt extracted from the zip; fall back to the
        # copy bundled directly inside the installer exe.
        req_file = APP_DIR / "requirements.txt"
        log(f"req_file (primary): {req_file}  exists={req_file.exists()}")
        if not req_file.exists():
            bundled_req = resource("requirements.txt")
            log(f"req_file (bundled fallback): {bundled_req}  exists={bundled_req.exists()}")
            if bundled_req.exists():
                req_file = bundled_req
            else:
                raise RuntimeError(
                    f"requirements.txt not found at {req_file} "
                    f"or in the bundled installer resources."
                )
        log(f"Using req_file: {req_file}")

        update_status("Upgrading pip…")
        r = run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "-q"])
        if r.returncode != 0:
            raise RuntimeError(f"pip upgrade failed:\n{r.stderr or r.stdout}")
        update_progress(82)
        update_status("Installing dependencies — this may take several minutes…")
        log(f"RUN pip install -r {req_file}")

        # Merge stderr into stdout to avoid pipe buffer deadlock.
        # (Reading stdout line-by-line while stderr has a separate pipe causes
        # a deadlock once pip's stderr output fills the OS pipe buffer.)
        proc = subprocess.Popen(
            [str(venv_python), "-m", "pip", "install",
             "-r", str(req_file), "--progress-bar", "off"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            encoding="utf-8", errors="replace"
        )
        pkg_count = 0
        last_lines = []   # keep a rolling tail for error reporting
        for line in proc.stdout:
            line = line.strip()
            log(f"  pip: {line}")   # log every line from pip
            if not line:
                continue
            last_lines.append(line)
            if len(last_lines) > 20:
                last_lines.pop(0)
            if line.startswith("Collecting") or line.startswith("Installing"):
                pkg_count += 1
                label = line[:55] + "…" if len(line) > 55 else line
                update_status(label)
                pct = min(82 + (pkg_count / 60) * 11, 93)
                update_progress(pct)
        proc.wait()
        log(f"pip exit code: {proc.returncode}")
        if proc.returncode != 0:
            tail = "\n".join(last_lines[-10:])
            raise RuntimeError(f"Dependency installation failed:\n{tail}")
        update_status("Dependencies installed.")
        update_step("deps", "done")
        update_progress(93)

        # ── 5. Ollama ──────────────────────────────────────────────────────────
        update_step("ollama", "running")
        update_status("Checking for Ollama…")
        if find_ollama():
            update_status("Ollama found.")
            update_step("ollama", "done")
            update_progress(95)
        else:
            update_status("Ollama not found — downloading installer…")
            tmp_ollama = pathlib.Path(os.environ.get("TEMP", INSTALL_DIR)) / "OllamaSetup.exe"
            urllib.request.urlretrieve(
                OLLAMA_URL, tmp_ollama,
                reporthook=make_reporthook(
                    lambda msg, v: (update_status(msg), update_progress(v)),
                    93, 95, "Downloading Ollama"
                )
            )
            update_status("Installing Ollama silently…")
            r = run([str(tmp_ollama), "/S"])
            tmp_ollama.unlink(missing_ok=True)
            if r.returncode not in (0, 3010):   # 3010 = success, reboot pending
                raise RuntimeError("Ollama installer failed. Please install Ollama manually from ollama.com.")
            update_status("Ollama installed.")
            update_step("ollama", "done")
            update_progress(95)

        # ── 6. Pull model ──────────────────────────────────────────────────────
        update_step("model", "running")
        update_status(f"Checking if {MODEL} is already downloaded…")

        # Check if model already exists
        r = run(["ollama", "list"])
        if r.returncode == 0 and MODEL.split(":")[0] in r.stdout:
            update_status(f"{MODEL} already downloaded.")
            update_step("model", "done")
            update_progress(99)
        else:
            update_status(f"Downloading {MODEL} (~2.2 GB) — please wait…")
            proc = subprocess.Popen(
                ["ollama", "pull", MODEL],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                encoding="utf-8", errors="replace"
            )
            for line in proc.stdout:
                # Strip ANSI escape codes roughly
                clean = ""
                skip = False
                for ch in line:
                    if ch == "\x1b":
                        skip = True
                    elif skip and ch == "m":
                        skip = False
                    elif not skip:
                        clean += ch
                clean = clean.strip()
                if not clean:
                    continue
                # Parse percentage if present
                pct_val = None
                if "%" in clean:
                    try:
                        pct_str = clean.split("%")[0].split()[-1]
                        pct_val = float(pct_str)
                        progress = 95 + (pct_val / 100) * 4
                        update_progress(progress)
                    except (ValueError, IndexError):
                        pass
                label = clean[:65] + "…" if len(clean) > 65 else clean
                update_status(label)
            proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(f"Model download failed (exit {proc.returncode}). Check your internet connection.")
            update_step("model", "done")
            update_progress(99)

        # ── 7. Launch ──────────────────────────────────────────────────────────
        update_step("launch", "running")
        update_status("Launching WhisperLeaf…")

        bat = APP_DIR / "Start WhisperLeaf.bat"
        if bat.exists():
            subprocess.Popen(
                ["cmd", "/c", str(bat)],
                cwd=str(APP_DIR),
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        else:
            # Fallback: launch uvicorn directly
            subprocess.Popen(
                [str(venv_python), "-m", "uvicorn", "src.main:app",
                 "--host", "127.0.0.1", "--port", str(APP_PORT)],
                cwd=str(APP_DIR),
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )

        # Give the server a moment to start, then open browser
        time.sleep(4)
        webbrowser.open(f"http://127.0.0.1:{APP_PORT}/chat")
        update_step("launch", "done")
        update_progress(100)
        done_cb()

    except Exception as exc:
        import traceback
        log_section("INSTALL FAILED")
        log(traceback.format_exc())
        log(f"Error shown to user: {exc}")
        error_cb(str(exc))


# ── GUI ───────────────────────────────────────────────────────────────────────

class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WhisperLeaf Setup")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._step_labels = {}
        self._step_icons  = {}
        self._build_ui()
        self._center()
        self.after(200, self._start_install)

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=CARD, pady=22)
        header.pack(fill="x")

        try:
            from PIL import Image, ImageTk
            img = Image.open(resource("owl.png")).convert("RGBA").resize((48, 48))
            self._owl = ImageTk.PhotoImage(img)
            tk.Label(header, image=self._owl, bg=CARD).pack()
        except Exception:
            pass

        tk.Label(header, text="WhisperLeaf", font=("Segoe UI", 18, "bold"),
                 bg=CARD, fg=FG).pack()
        tk.Label(header, text="Setting up your private AI workspace",
                 font=("Segoe UI", 10), bg=CARD, fg=MUTED).pack(pady=(2, 0))

        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x")

        # ── Steps ────────────────────────────────────────────────────────────
        steps_frame = tk.Frame(self, bg=BG, padx=32, pady=20)
        steps_frame.pack(fill="x")

        for key, label in STEPS:
            row = tk.Frame(steps_frame, bg=BG)
            row.pack(fill="x", pady=3)

            icon = tk.Label(row, text="○", font=("Segoe UI", 11),
                            bg=BG, fg=MUTED, width=2, anchor="w")
            icon.pack(side="left")

            lbl = tk.Label(row, text=label, font=("Segoe UI", 10),
                           bg=BG, fg=MUTED, anchor="w")
            lbl.pack(side="left", padx=(6, 0))

            self._step_icons[key]  = icon
            self._step_labels[key] = lbl

        sep2 = tk.Frame(self, bg=BORDER, height=1)
        sep2.pack(fill="x")

        # ── Progress bar ──────────────────────────────────────────────────────
        prog_frame = tk.Frame(self, bg=BG, padx=32, pady=16)
        prog_frame.pack(fill="x")

        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("WL.Horizontal.TProgressbar",
                        troughcolor=CARD, background=GREEN,
                        bordercolor=BORDER, lightcolor=GREEN, darkcolor=GREEN,
                        thickness=10)

        self._progress_var = tk.DoubleVar(value=0)
        self._bar = ttk.Progressbar(prog_frame, variable=self._progress_var,
                                    maximum=100, length=420,
                                    style="WL.Horizontal.TProgressbar")
        self._bar.pack(fill="x")

        self._status_var = tk.StringVar(value="Starting…")
        tk.Label(prog_frame, textvariable=self._status_var,
                 font=("Segoe UI", 9), bg=BG, fg=MUTED,
                 wraplength=420, justify="left", anchor="w").pack(
                     fill="x", pady=(8, 0))

        # ── Footer ─────────────────────────────────────────────────────────────
        footer = tk.Frame(self, bg=BG, pady=14)
        footer.pack(fill="x")
        tk.Label(footer, text="Everything runs locally. Nothing leaves your machine.",
                 font=("Segoe UI", 9, "italic"), bg=BG, fg=MUTED).pack()

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    # ── Threadsafe updaters ───────────────────────────────────────────────────

    def _update_step(self, key, state):
        def _do():
            icon  = self._step_icons.get(key)
            label = self._step_labels.get(key)
            if not icon or not label:
                return
            if state == "running":
                icon.config(text="▶", fg=BLUE)
                label.config(fg=FG)
            elif state == "done":
                icon.config(text="✓", fg=GREEN)
                label.config(fg=FG)
            elif state == "error":
                icon.config(text="✗", fg=RED)
                label.config(fg=RED)
        self.after(0, _do)

    def _update_status(self, msg):
        self.after(0, lambda: self._status_var.set(msg))

    def _update_progress(self, value):
        self.after(0, lambda: self._progress_var.set(value))

    def _on_done(self):
        def _do():
            self._status_var.set("WhisperLeaf is running! Opening in your browser…")
            self.after(3000, self.destroy)
        self.after(0, _do)

    def _on_error(self, msg):
        def _do():
            self._status_var.set(f"Error: {msg}")
            # Mark the currently-running step as errored
            for key, icon in self._step_icons.items():
                if icon.cget("text") == "▶":
                    self._update_step(key, "error")
            # Show log file location and retry hint
            tk.Label(self, text=f"Log saved to: {LOG_PATH}",
                     font=("Segoe UI", 8), bg=BG, fg=MUTED,
                     wraplength=440).pack(pady=(4, 0))
            tk.Label(self, text="Close this window and try again, or send the log file for support.",
                     font=("Segoe UI", 9), bg=BG, fg=RED,
                     wraplength=440).pack(pady=(2, 10))
        self.after(0, _do)

    # ── Start ─────────────────────────────────────────────────────────────────

    def _start_install(self):
        t = threading.Thread(
            target=install,
            args=(self._update_step, self._update_status,
                  self._update_progress, self._on_done, self._on_error),
            daemon=True,
        )
        t.start()


if __name__ == "__main__":
    # On Windows, suppress the console window when frozen
    if sys.platform == "win32" and hasattr(ctypes, "windll"):
        try:
            ctypes.windll.kernel32.SetConsoleTitleW("WhisperLeaf Setup")
        except Exception:
            pass

    app = InstallerApp()
    app.mainloop()
