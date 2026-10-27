from pathlib import Path

_src_mvc = Path(__file__).resolve().parent.parent / 'src' / 'mvc'
__path__ = [str(_src_mvc)]

from src.mvc import DocumentModel, MainView, MainController

try:
    from src.mvc.app import MALODOSApp
except Exception:  # pragma: no cover - GUI dependency may be absent in test envs
    MALODOSApp = None

__all__ = ["DocumentModel", "MainView", "MainController", "MALODOSApp"]
