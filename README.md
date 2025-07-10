# 🎤 CocoSpeak: The Modern TTS GUI App (PyQt6)

---

> **A beautiful, powerful, and user-friendly Text-to-Speech (TTS) desktop app built with PyQt6!**

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
| 🖥️ Modern PyQt6 UI     | Responsive, beautiful, and easy to use              |
| ⬇️ Real-time Downloads  | Progress bars for online model downloads            |
| ⌨️ Global Hotkeys       | Robust hotkey system with clear error messages     |
| 📝 Smart Text Processing | Automatic character compatibility handling          |
| 📋 Enhanced Queue        | Real-time queue status and management               |

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
   - Double-click the EXE or run `python gui/main_window.py`
   - Make sure the `models/` folder is next to the EXE/script

2. **Add Models**
   - **Download Online:** Use "Download Online Model" for Coqui TTS Hub models with real-time progress
   - **Import Custom:** Use "Import Model" to add your own model, config, and speaker mapping
   - **Manual:** Place model/checkpoint and config in a new folder under `models/`

3. **Select a Model**
   - Only real model files are shown (no more `speakers.pth` or `config.json` clutter!)
   - Multi-speaker models show a speaker dropdown—just pick your voice!

4. **Type Text & Speak**
   - Enter your text, click **Speak**, or **Save as WAV**
   - Use **Enter** to quickly add text to queue
   - Text is automatically preprocessed for character compatibility

5. **Queue Management**
   - Add multiple texts to the queue
   - See real-time status ("Speaking...", "Waiting...")
   - Remove items or clear the entire queue

6. **Global Hotkeys**
   - Set custom hotkeys for quick access
   - Default: `/` to toggle window visibility
   - Clear error messages for unsupported combinations

7. **Switch Phonemizer**
   - Use the dropdown to toggle between `gruut` and `espeak` (auto-updates config)

8. **Refresh Models**
   - Click **Refresh** if you add/remove models while the app is open

---

## 🆕 WHAT'S NEW IN PYQT6 VERSION?

- **Modern PyQt6 Interface:** Better performance, responsive design, and modern look
- **Real-time Download Progress:** See actual progress bars when downloading online models
- **Robust Hotkey System:** Clear error messages and reliable global hotkey registration
- **Smart Text Preprocessing:** Automatically handles special characters and compatibility issues
- **Enhanced Queue System:** Real-time status updates and better queue management
- **Better Error Handling:** User-friendly error messages and helpful troubleshooting tips
- **Character Compatibility:** Automatic conversion of problematic characters (é→e, ñ→n, etc.)
- **Download Warnings:** Informative dialogs about model compatibility issues
- **Thread-Safe Operations:** All UI updates are main-thread safe
- **Improved Model Organization:** Better folder structure and file naming

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
- **Character Vocabulary Errors?**
  - Text is automatically preprocessed, but some models have very limited character sets
  - Try using only basic English letters and punctuation
- **Download Failures?**
  - Some models may not be available for download
  - Check the console for detailed error messages
- **Hotkey Not Working?**
  - Some combinations (like Ctrl+A) are not supported globally
  - Try combinations with more modifiers (Alt+T, Ctrl+/)

---

## 📁 PROJECT STRUCTURE

```text
CocoSpeak/
├── gui/
│   ├── main_window.py     # Main PyQt6 application
│   └── dialogs.py         # Dialog windows (download, hotkey, etc.)
├── tts_module/
│   └── model_manager.py   # Model management utilities
├── cocospeak.spec         # PyInstaller config
├── requirements.txt       # Python dependencies
├── build.bat / build.ps1 # Windows build scripts
├── models/                # TTS models (not in git)
│   ├── custom/            # Custom imported models
│   └── [model folders]    # Downloaded/imported models
└── dist/cocospeak/        # Built executable (after build)
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
- **Character Compatibility:** Models with limited vocabularies automatically have text preprocessed

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

## 🔧 TECHNICAL DETAILS

- **Framework:** PyQt6 for modern, responsive UI
- **TTS Engine:** Coqui TTS with ModelManager integration
- **Audio:** Real-time synthesis with queue management
- **Threading:** All synthesis and downloads run in background threads
- **Hotkeys:** Global hotkey support with keyboard library
- **Text Processing:** Automatic character compatibility handling
- **Error Handling:** Comprehensive error messages and user guidance

--- 