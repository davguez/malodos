class _SimpleFrame(object):
    def __init__(self, title='MALODOS'):
        self.title = title
        self.docList = []

    def initialize(self):
        return self

    def Show(self, value=True):
        return value


class MainView(object):
    """View layer: presentation concerns and UI binding only."""

    def __init__(self, title='MALODOS', frame=None):
        self.title = title
        self.frame = frame
        self.controller = None
        self.docList = []
        self._is_initialized = False

    def attach_controller(self, controller):
        self.controller = controller
        return self

    def initialize(self):
        if self._is_initialized:
            return self.frame
        if self.frame is None:
            try:
                from gui.mainBoard import MainFrame
                self.frame = MainFrame(None, self.title)
            except Exception:
                self.frame = _SimpleFrame(self.title)
        if hasattr(self.frame, 'initialize'):
            self.frame.initialize()
        self._is_initialized = True
        return self.frame

    def show(self):
        frame = self.initialize()
        if hasattr(frame, 'Show'):
            frame.Show(True)
        return frame

    def display_documents(self, documents):
        self.docList = list(documents or [])
        frame = self.frame
        if frame is None:
            self.initialize()
            frame = self.frame
        if hasattr(frame, 'docList'):
            frame.docList = self.docList
        if hasattr(frame, 'actionSearch'):
            try:
                frame.actionSearch(None)
            except Exception:
                pass
        return self.docList
