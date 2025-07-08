# 🎤 CocoSpeak: The Modern TTS GUI App

---

> **A beautiful, powerful, and user-friendly Text-to-Speech (TTS) desktop app for everyone!**

---

## ✨ FEATURE SPOTLIGHT

| 🚀 Feature                | 💡 Description                                      |
|--------------------------|-----------------------------------------------------|
| 🗣️ Multi-Speaker Support | Auto-detects and lets you pick any voice!           |
| ⚡ CUDA Auto-Detect       | Uses your GPU if available, for blazing speed       |
| 🔄 Import Wizard         | Easy import of models, configs, and speaker mapping |
| 🎛️ Phonemizer Switch    | Instantly swap between `gruut` and `espeak`         |
| 🧹 Clean Model List      | Only real models, no clutter                        |
| 💾 Save as WAV           | Export your speech to high-quality audio            |
| 🖥️ Modern UI            | Responsive, beautiful, and easy to use              |

---

## 🚀 QUICK START

### 1️⃣ Use the Pre-built EXE
1. Download the `cocospeak` folder from releases
2. Double-click `cocospeak.exe`
3. Start speaking!

### 2️⃣ Build from Source
```sh
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
build.bat  # or build.ps1
```
Find your EXE in `dist/cocospeak/cocospeak.exe`

---

## 🖱️ HOW TO USE

1. **Run the App**
   - Double-click the EXE or run `python cocospeak.py`
   - Make sure the `models/` folder is next to the EXE/script

2. **Add Models**
   - **Download Online:** Use the "Download Model" button for Coqui TTS Hub models
   - **Import Custom:** Use "Import Model" to add your own model, config, and (optionally) speaker mapping
   - **Manual:** Place model/checkpoint and config in a new folder under `models/`

3. **Select a Model**
   - Only real model files are shown (no more `speakers.pth` or `config.json` clutter!)
   - Multi-speaker models show a speaker dropdown—just pick your voice!

4. **Type Text & Speak**
   - Enter your text, click **Speak**, or **Save as WAV**

5. **Switch Phonemizer**
   - Use the dropdown to toggle between `gruut` and `espeak` (auto-updates config)

6. **Refresh Models**
   - Click **Refresh** if you add/remove models while the app is open

---

## 🆕 WHAT'S NEW?

- **Multi-Speaker Models:** Auto-detects and supports speaker selection for any compatible model
- **Import Improvements:** Warns if you forget a mapping file for multi-speaker models; always copies as `speakers.pth`
- **Model List Cleanup:** Only real models appear in the dropdown
- **No More Annoying Popups:** Success is shown in the status bar, not as a popup
- **Automatic CUDA Detection:** Uses your GPU if available, falls back to CPU if not

---

## 🛠️ TROUBLESHOOTING & TIPS

- **Model Not Showing?**
  - Make sure both the model and config are in the same folder
  - Click **Refresh** after adding new models
- **Multi-Speaker Model, No Names?**
  - Import the correct `speakers.pth` file, or use numeric IDs
- **Audio Issues?**
  - Check your system audio and dependencies
- **Phonemizer Errors?**
  - Try switching phonemizer in the GUI, or check your config
- **CUDA Not Detected?**
  - Make sure you have a compatible GPU and PyTorch installed with CUDA support

---

## 📁 PROJECT STRUCTURE

```text
CocoSpeak/
├── cocospeak.py          # Main application
├── cocospeak.spec        # PyInstaller config
├── requirements.txt      # Python dependencies
├── build.bat / build.ps1 # Windows build scripts
├── models/               # TTS models (not in git)
│   ├── custom/           # Custom imported models
│   └── [model folders]   # Downloaded/imported models
└── dist/cocospeak/       # Built executable (after build)
```

---

## 🤝 CONTRIBUTING

Pull requests and suggestions are welcome! If you find a bug or want a new feature, open an issue or PR.

---

## 📄 LICENSE

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙋‍♂️ NEED HELP?

Open an issue on this GitHub repo for support or questions.

---

## 🧠 MODEL COMPATIBILITY

- **Supported:** VITS, Tacotron, FastPitch, GlowTTS, Capacitron, and similar TTS models
- **Not Supported:** Vocoder-only models (e.g., HiFiGAN, MelGAN) are hidden and cannot be selected

---

## 🪟 WINDOWS BUILD NOTE: HIDING SUBPROCESS WINDOWS

CocoSpeak uses a PyInstaller runtime hook to hide unwanted command prompt windows:
- **File:** `hook-hide_subprocess_windows.py`
- **How to use:**
  1. Ensure the file is present in your project root
  2. Add to `runtime_hooks` in `cocospeak.spec`:
     ```python
     runtime_hooks=['hook-hide_subprocess_windows.py'],
     ```
  3. Build with PyInstaller as usual

--- 