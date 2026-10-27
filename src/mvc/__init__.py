"""MVC layer for MALODOS.

This package intentionally avoids eager GUI imports to keep side effects low.
"""

__all__ = ["DocumentModel", "MainView", "MainController", "MALODOSApp"]


def __getattr__(name):
    if name == "DocumentModel":
        from .models import DocumentModel
        return DocumentModel
    if name == "MainView":
        from .views import MainView
        return MainView
    if name == "MainController":
        from .controllers import MainController
        return MainController
    if name == "MALODOSApp":
        from .app import MALODOSApp
        return MALODOSApp
    raise AttributeError(name)
