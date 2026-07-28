#!/usr/bin/env python3
"""Photo Voice — private viewer that attaches your voice to photographs.

Shows each unsorted photo large; hold your story on it:

    SPACE      start / stop recording (auto-transcribes on stop)
    ← / →      previous / next photo
    A          move photo (+ its RAW twin + voice files) to archived/
    Q / Esc    quit

Everything stays inside photos-inbox/ (gitignored, private):
    voice/<photo-stem>.wav   — the recording
    voice/<photo-stem>.txt   — the transcript
    captions.md              — running log: filename + transcript

Run with the VoiceTyper venv (has sounddevice + mlx-whisper):
    /Users/john/Dropbox/_______Cursor/speech/venv/bin/python3 \
        photography/photo_voice.py
or double-click photos-inbox/"Photo Voice.command".
"""

import queue
import threading
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
import tkinter as tk

HERE = Path(__file__).parent
INBOX = (HERE.parent / "photos-inbox").resolve()
VOICE = INBOX / "voice"
VOICE.mkdir(exist_ok=True)
CAPTIONS = INBOX / "captions.md"
SHOW = (".jpg", ".jpeg", ".png")
RAW = (".cr2", ".raf", ".arw", ".dng", ".nef")
SAMPLE_RATE = 16_000
MLX_REPO = "mlx-community/whisper-small-mlx"  # same model VoiceTyper uses

PAPER, INK, DIM, ACCENT = "#f7f6f3", "#1c1b18", "#8a867c", "#7C2530"


def unsorted_photos():
    return sorted(p for p in INBOX.iterdir()
                  if p.is_file() and p.suffix.lower() in SHOW)


class App:
    def __init__(self):
        self.photos = unsorted_photos()
        self.i = 0
        self.recording = False
        self.frames = queue.Queue()
        self.stream = None
        self.busy = False

        self.root = tk.Tk()
        self.root.title("Photo Voice — private")
        self.root.configure(bg=PAPER)
        self.root.geometry("1200x860")

        self.name_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.name_var, bg=PAPER, fg=DIM,
                 font=("Helvetica", 12)).pack(pady=(12, 4))
        self.canvas = tk.Canvas(self.root, bg=PAPER, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=16)
        self.status_var = tk.StringVar()
        self.status = tk.Label(self.root, textvariable=self.status_var, bg=PAPER,
                               fg=INK, font=("Helvetica", 13), wraplength=1100,
                               justify="left")
        self.status.pack(fill="x", padx=18, pady=(4, 2))
        tk.Label(self.root, text="SPACE record/stop · ← → navigate · A archive · Q quit",
                 bg=PAPER, fg=DIM, font=("Helvetica", 11)).pack(pady=(0, 10))

        self.root.bind("<space>", self.toggle_record)
        self.root.bind("<Left>", lambda e: self.nav(-1))
        self.root.bind("<Right>", lambda e: self.nav(1))
        self.root.bind("a", self.archive_current)
        self.root.bind("q", lambda e: self.root.destroy())
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.canvas.bind("<Configure>", lambda e: self.show())

        self._img_ref = None
        self.set_status("Loading transcription model in the background…")
        threading.Thread(target=self._warmup, daemon=True).start()
        self.show()

    # ---------- model ----------
    def _warmup(self):
        try:
            import mlx_whisper
            silent = VOICE / "_warmup.wav"
            self._write_wav(silent, np.zeros(SAMPLE_RATE // 2, dtype=np.int16))
            mlx_whisper.transcribe(str(silent), path_or_hf_repo=MLX_REPO,
                                   language="en")
            silent.unlink(missing_ok=True)
            self.set_status("Ready. SPACE to start talking about this photo.")
        except Exception as e:
            self.set_status(f"Model warmup problem (will retry on first use): {e}")

    # ---------- ui ----------
    def set_status(self, text, color=INK):
        self.status_var.set(text)
        self.status.configure(fg=color)

    def show(self):
        self.canvas.delete("all")
        if not self.photos:
            self.name_var.set("")
            self.set_status("Inbox clear — no unsorted photos. ✨")
            return
        self.i %= len(self.photos)
        p = self.photos[self.i]
        self.name_var.set(f"{p.name}   ·   {self.i + 1} / {len(self.photos)}"
                          + ("   ·   has voice note" if (VOICE / (p.stem + '.txt')).exists() else ""))
        try:
            img = tk.PhotoImage(file=str(p))
        except Exception:
            # tk PhotoImage handles PNG/GIF natively; JPEGs need a detour
            img = self._load_jpeg(p)
        if img is None:
            self.set_status(f"Can't display {p.name}", ACCENT)
            return
        cw = max(self.canvas.winfo_width(), 400)
        ch = max(self.canvas.winfo_height(), 300)
        scale = max(1, int(max(img.width() / cw, img.height() / ch)) + 1) \
            if (img.width() > cw or img.height() > ch) else 1
        if scale > 1:
            img = img.subsample(scale, scale)
        self._img_ref = img
        self.canvas.create_image(cw // 2, ch // 2, image=img)

    def _load_jpeg(self, p):
        # Convert via sips to a temp PNG tk can read (no PIL dependency).
        import subprocess
        import tempfile
        tmp = Path(tempfile.gettempdir()) / (p.stem + "_pv.png")
        try:
            subprocess.run(["sips", "-s", "format", "png",
                            "--resampleHeightWidthMax", "1600",
                            str(p), "--out", str(tmp)],
                           capture_output=True, check=True)
            return tk.PhotoImage(file=str(tmp))
        except Exception:
            return None

    def nav(self, d):
        if self.recording:
            return
        self.i = (self.i + d) % max(1, len(self.photos))
        self.show()

    # ---------- recording ----------
    def toggle_record(self, _e=None):
        if self.busy or not self.photos:
            return
        if not self.recording:
            self.frames = queue.Queue()
            try:
                self.stream = sd.InputStream(
                    samplerate=SAMPLE_RATE, channels=1, dtype="int16",
                    callback=lambda data, *_: self.frames.put(data.copy()))
                self.stream.start()
            except Exception as e:
                self.set_status(f"Mic problem: {e}", ACCENT)
                return
            self.recording = True
            self.set_status("● Recording — SPACE to stop.", ACCENT)
        else:
            self.recording = False
            self.stream.stop(); self.stream.close()
            chunks = []
            while not self.frames.empty():
                chunks.append(self.frames.get())
            if not chunks:
                self.set_status("Heard nothing — try again.")
                return
            audio = np.concatenate(chunks).flatten()
            p = self.photos[self.i]
            wav_path = VOICE / (p.stem + ".wav")
            self._write_wav(wav_path, audio)
            self.busy = True
            self.set_status("Transcribing…", DIM)
            threading.Thread(target=self._transcribe,
                             args=(p, wav_path), daemon=True).start()

    @staticmethod
    def _write_wav(path, int16_audio):
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(int16_audio.tobytes())

    def _transcribe(self, photo, wav_path):
        try:
            import mlx_whisper
            result = mlx_whisper.transcribe(str(wav_path),
                                            path_or_hf_repo=MLX_REPO,
                                            language="en")
            text = result["text"].strip()
            (VOICE / (photo.stem + ".txt")).write_text(text + "\n",
                                                       encoding="utf-8")
            with open(CAPTIONS, "a", encoding="utf-8") as f:
                f.write(f"- **{photo.name}** — {text}\n")
            self.root.after(0, lambda: (
                self.set_status(f"“{text}”"),
                self.show()))
        except Exception as e:
            self.root.after(0, lambda: self.set_status(
                f"Transcription failed (audio saved at {wav_path.name}): {e}",
                ACCENT))
        finally:
            self.busy = False

    # ---------- filing ----------
    def archive_current(self, _e=None):
        if self.recording or not self.photos:
            return
        p = self.photos.pop(self.i)
        dest = INBOX / "archived"
        dest.mkdir(exist_ok=True)
        moved = [p.name]
        p.rename(dest / p.name)
        # RAW twin + voice files travel with the photo
        for twin in INBOX.iterdir():
            if twin.is_file() and twin.stem.lower() == p.stem.lower() \
                    and twin.suffix.lower() in RAW:
                twin.rename(dest / twin.name)
                moved.append(twin.name)
        self.set_status(f"→ archived: {', '.join(moved)}")
        self.show()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
