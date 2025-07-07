CocoSpeak - TTS GUI App
=======================

CocoSpeak is a Python-based Text-to-Speech (TTS) GUI app that supports custom models, phonemizer switching (gruut/espeak), and robust PyInstaller packaging.

Features:
---------
- Load and use custom TTS models (VITS, Tacotron, etc.)
- Switch between gruut and espeak phonemizers from the GUI
- Robust handling of TTS output (works with both single and multi-sentence input)
- CUDA and CPU support
- Modern, user-friendly interface
- Portable EXE build with PyInstaller

Setup Instructions:
-------------------
1. **Create and activate a virtual environment:**
   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```
2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```
   - Make sure requirements.txt matches your venv's installed versions for best compatibility.

3. **Run the app:**
   ```
   python cocospeak.py
   ```

4. **Build the EXE (Windows):**
   ```
   powershell -ExecutionPolicy Bypass -File build.ps1
   # or
   build.bat
   ```
   - Run the EXE from the command line to see debug output if you have issues.

5. **Add your models:**
   - Place your model files and config.json in the `models/` directory (or use the GUI to import).

6. **Phonemizer switching:**
   - Use the dropdown in the GUI to switch between gruut and espeak. The app will update the config and reload the model automatically.

Troubleshooting:
----------------
- If you hear static, gibberish, or short/unclear audio in the EXE, make sure:
  - Your requirements.txt matches your venv (especially torch, torchaudio, gruut, and language packs)
  - The correct phonemizer is set in the config and matches what the model was trained with
  - All model and config files are present in the EXE's models directory
- Run the EXE from the command line to see debug output.

Contributing:
-------------
Pull requests and issues are welcome!

License:
--------
See LICENSE file.

---

## 🚀 Quick Start

### Option 1: Use Pre-built Executable
1. Download the `cocospeak` folder from releases
2. Double-click `cocospeak.exe`
3. Start using TTS models!

### Option 2: Build from Source
1. Install Python 3.8+ and dependencies: `pip install -r requirements.txt`
2. Run the build script:
   - **Windows:** Double-click `build.bat` or run `build.ps1` in PowerShell
   - **Manual:** `pyinstaller cocospeak.spec`
3. Find your exe in `dist/cocospeak/cocospeak.exe`

---

## 🛠️ How to Use

### 1. **Run the App**
- Double-click `cocospeak.exe` (or run `python cocospeak.py` if using source).
- Make sure the `models/` folder is next to the `.exe` or script.

### 2. **Add Models**
- **Download Online Model:** Use the "Download Model" button to fetch models from the Coqui model hub with real-time progress tracking.
- **Import Custom Model:** Use the "Import Model" button to add your own model files (`.pth`, `.pt`, `.ckpt`, or `.safetensors`) and config files. Each import creates a new folder under `models/custom/`.
- **Manual Add:** Create a new folder in `models/` (or `models/custom/`), and place both the model file (`.pth`, `.pt`, `.ckpt`, or `.safetensors`) and its config file there.

**Note:** The app supports multiple model formats: `.pth`, `.pt`, `.ckpt`, and `.safetensors`. All PyTorch-compatible model formats are supported. **Currently tested with `.pth` files.**

### 3. **Select and Use Models**
- Use the dropdown to select a model (now with better model name display).
- Enter text, click **Speak** to play, or **Save as WAV** to export audio.
- Adjust speed and pitch settings as needed.

### 4. **Refresh Model List**
- Click **Refresh** if you add/remove models while the app is open.

---

## 🆕 New Features


- **Real-time Download Progress:** Model downloads now show actual progress with cancel option
- **Improved Model Display:** Better model names and organization
- **Enhanced UI:** Modern, beautiful interface with better user experience
- **Robust Build Process:** Automated build scripts with proper dependency handling

---

## ⚠️ Important Notes

- **Each `.pth` file must have its own matching config file in the same folder.**
- **Multiple model formats are supported**: `.pth`, `.pt`, `.ckpt`, and `.safetensors` - all PyTorch-compatible formats work. **Currently tested with `.pth` files.**
- If you have multiple `.pth` files that use the same config, you can keep them together in one folder (they will appear as separate models in the app).
- If a model does not appear, click **Refresh**.
- If you move the `.exe`, always move the `models/` folder with it.
- **For Distribution:** Send the entire `dist/cocospeak` folder, not just the exe.

---

## 🧩 Troubleshooting

### Build Issues
- **Clean Build:** Always clean `dist/` and `build/` folders before rebuilding
- **Missing Dependencies:** Run `pip install -r requirements.txt` before building
- **PyInstaller Errors:** Use the provided build scripts for best results

### Runtime Issues
- **Model not loaded / config not found:**  
  Make sure both files are present and compatible in the same folder.
- **App not finding models:**  
  Check that `models/` is next to the `.exe` and each model has its own folder.
- **Audio not playing:**  
  Ensure your system audio is working and all dependencies are installed.
- **Missing VERSION files:**  
  The build process handles this automatically, but if issues persist, manually add `trainer/VERSION` file.

---

## 📁 Project Structure

```
my-tts/
├── cocospeak.py          # Main application
├── cocospeak.spec        # PyInstaller configuration
├── requirements.txt         # Python dependencies
├── build.bat               # Windows build script
├── build.ps1               # PowerShell build script
├── models/                 # TTS models (not in git)
│   ├── custom/            # Custom imported models
│   └── [model folders]    # Downloaded/imported models
└── dist/cocospeak/      # Built executable (after build)
```

---

## 💡 Contributing

Pull requests and suggestions are welcome!  
If you find a bug or want a new feature, open an issue or PR.

---

## 📄 License

This project is licensed under the MIT License.  
See [LICENSE](LICENSE) for details.

---

## 🙋‍♂️ Contact

For help or to report issues, open an issue on this GitHub repo.

---

## 🧠 Model Compatibility

- **Supported:** TTS models such as VITS, Tacotron, FastPitch, GlowTTS, Capacitron, and similar.
- **Not Supported:** Vocoder-only models (e.g., HiFiGAN, MelGAN) are automatically hidden and cannot be selected or downloaded.

## 🛠️ Troubleshooting

- If you see an error about "phonemizer" or "use_phonemes," you may have tried to load a vocoder or an unsupported model. Only TTS models are supported. 

## 🪟 Windows Build Note: Hiding Subprocess Windows

To prevent unwanted command prompt windows from appearing when running the EXE on Windows, CocoSpeak uses a PyInstaller runtime hook:

- **File:** `hook-hide_subprocess_windows.py`
- **Purpose:** Patches all subprocesses to hide their windows by default on Windows.
- **How to use:**
  1. Ensure `hook-hide_subprocess_windows.py` is present in your project root.
  2. In your `cocospeak.spec`, add it to the `runtime_hooks` list:
     ```python
     runtime_hooks=['hook-hide_subprocess_windows.py'],
     ```
  3. Build with PyInstaller as usual.

**Troubleshooting:**
- If you see `'STARTUPINFO' object is not callable`, make sure you have NOT assigned `subprocess.STARTUPINFO = subprocess.STARTUPINFO()` anywhere in your code. This will break all subprocess usage.
- The runtime hook is defensive and will not patch if `STARTUPINFO` is not a class.

--- 