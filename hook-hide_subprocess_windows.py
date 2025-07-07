import sys

if sys.platform == "win32":
    import subprocess
    # Only patch if STARTUPINFO is a class (not an instance)
    if isinstance(subprocess.STARTUPINFO, type):
        _original_popen_init = subprocess.Popen.__init__
        def _patched_popen_init(self, *args, **kwargs):
            if "startupinfo" not in kwargs or kwargs["startupinfo"] is None:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE
                kwargs["startupinfo"] = si
            return _original_popen_init(self, *args, **kwargs)
        subprocess.Popen.__init__ = _patched_popen_init
        print("hook-hide_subprocess_windows: subprocess.Popen patched to hide windows.")
    else:
        print("hook-hide_subprocess_windows: subprocess.STARTUPINFO is not a class, skipping patch.") 