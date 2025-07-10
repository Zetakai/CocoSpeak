# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('venv/Lib/site-packages/TTS', 'TTS'),
        ('venv/Lib/site-packages/gruut', 'gruut'),
        ('venv/Lib/site-packages/trainer', 'trainer'),
        ('venv/Lib/site-packages/jamo', 'jamo'),
        ('gui', 'gui'),
        ('tts_module', 'tts_module'),
        ('utils', 'utils')
    ],
    hiddenimports=[
        'TTS', 'gruut', 'trainer', 'inflect', 'typeguard', 'jamo', 
        'TTS.tts.utils.text', 'TTS.tts.utils.text.cleaners', 
        'TTS.tts.utils.text.english.number_norm',
        'keyboard', 'threading', 'collections', 'pysbd',
        'TTS.utils.synthesizer', 'TTS.utils.manage', 'TTS.tts.utils.audio',
        'TTS.tts.utils.helpers', 'TTS.tts.utils.speakers', 'TTS.tts.utils.text.tokenizer',
        'sounddevice', 'soundfile', 'numpy', 'torch', 'requests',
        'platform', 'json', 'shutil', 'datetime', 're', 'ctypes',
        'tts_module.audio', 'tts_module.synthesis', 'tts_module.model_manager',
        'gui.main_window', 'gui.dialogs', 'utils.paths'
    ],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=['hook-hide_subprocess_windows.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='cocospeak',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='cocospeak',
)
