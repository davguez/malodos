import os
from pathlib import Path


try:
    import PySide6
except ImportError:  # pragma: no cover - optional in non-GUI environments
    PySide6 = None


def configure_qt_environment():
    """Apply the Qt runtime settings before creating widgets."""
    if PySide6 is None:
        return False

    # Keep setup minimal, but ensure required platform plugins remain discoverable.
    pyside_root = Path(PySide6.__file__).resolve().parent
    qt_plugins = pyside_root / 'Qt' / 'plugins'
    qt_platforms = qt_plugins / 'platforms'
    if qt_plugins.exists():
        current_plugin_path = os.environ.get('QT_PLUGIN_PATH')
        if not current_plugin_path:
            os.environ['QT_PLUGIN_PATH'] = str(qt_plugins)
    if qt_platforms.exists():
        current_platform_plugin_path = os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH')
        if not current_platform_plugin_path:
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(qt_platforms)

    # Set MALODOS_GUI_PLATFORM to force a specific Qt platform plugin.
    forced_platform = os.environ.get('MALODOS_GUI_PLATFORM')
    if forced_platform:
        os.environ['QT_QPA_PLATFORM'] = forced_platform

    # Accessibility bridge can be disabled explicitly when required.
    if os.environ.get('MALODOS_DISABLE_AT_BRIDGE') == '1':
        os.environ.setdefault('NO_AT_BRIDGE', '1')

    # Keep headless test runs deterministic without overriding desktop sessions.
    if not os.environ.get('QT_QPA_PLATFORM') and not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    return True


def get_qapplication_class():
    """Return the QApplication class if Qt is available."""
    if PySide6 is None:
        return None
    from PySide6.QtWidgets import QApplication
    return QApplication
