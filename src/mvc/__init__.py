"""MVC layer for MALODOS.

This package groups the application state (model), the rendering surface
(view) and the interaction flow (controller) without changing the underlying
GUI implementation.
"""

from .models import DocumentModel
from .views import MainView
from .controllers import MainController

__all__ = ["DocumentModel", "MainView", "MainController"]
