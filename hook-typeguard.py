# PyInstaller hook for typeguard
from PyInstaller.utils.hooks import collect_data_files

# Collect data files
datas = collect_data_files('typeguard')

# Include all typeguard modules
hiddenimports = ['typeguard', 'typeguard._decorators', 'typeguard._functions', 'typeguard._transformer']

# Runtime hook to patch typeguard
def _typeguard_runtime_hook():
    import sys
    if hasattr(sys, '_MEIPASS'):
        # We're in a PyInstaller bundle, patch typeguard to avoid source inspection
        import typeguard
        import inspect
        
        # Patch inspect.getsource to return a dummy string
        original_getsource = inspect.getsource
        def dummy_getsource(obj):
            return "# dummy source for PyInstaller bundle"
        
        inspect.getsource = dummy_getsource 