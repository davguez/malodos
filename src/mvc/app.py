from .qt_setup import configure_qt_environment, get_qapplication_class

configure_qt_environment()
QApplication = get_qapplication_class()

from .controllers import MainController


if QApplication is not None:
    class MALODOSApp(QApplication):
        """Application bootstrap for the MVC architecture using Qt6."""

        def __init__(self, argv=None):
            self.controller = None
            super(MALODOSApp, self).__init__(argv or [])
            self.aboutToQuit.connect(self._cleanup)
            import database
            try:
                database.initialize()
            except Exception:
                pass
            self.controller = MainController()
            self.controller.run()

        def _cleanup(self):
            controller = getattr(self, 'controller', None)
            if controller is None:
                return
            try:
                view = getattr(controller, 'view', None)
                frame = getattr(view, 'frame', None) if view is not None else None
                if frame is not None:
                    try:
                        frame.hide()
                    except Exception:
                        pass
                    try:
                        frame.deleteLater()
                    except Exception:
                        pass
                    try:
                        view.frame = None
                    except Exception:
                        pass
            except Exception:
                pass
            self.controller = None

else:
    class MALODOSApp(object):
        """Fallback placeholder used when Qt is not installed."""

        def __init__(self, *args, **kwargs):
            raise RuntimeError('PySide6 is required to launch the MALODOS GUI.')
