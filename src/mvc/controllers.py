from .models import DocumentModel
from .views import MainView


class MainController(object):
    """Controller coordinating model and view."""

    def __init__(self, model=None, view=None):
        self.model = model or DocumentModel()
        self.view = view or MainView()
        self.view.attach_controller(self)
        self._is_initialized = False

    def initialize(self):
        if not self._is_initialized:
            self.view.initialize()
            self._is_initialized = True
        return self

    def bind_frame(self, frame):
        if hasattr(self.view, 'set_frame'):
            self.view.set_frame(frame)
        if frame is not None:
            setattr(frame, 'controller', self)
        return self

    def search(self, query=''):
        documents = self.model.search_documents(query)
        self.view.display_documents(documents)
        if hasattr(self.view, 'frame') and self.view.frame is not None:
            self.view.frame.docList = list(documents)
        return documents

    def refresh_documents(self, query=''):
        return self.search(query)

    def select_document(self, row):
        frame = getattr(self.view, 'frame', None)
        if frame is not None and hasattr(frame, 'actionDocSelect'):
            frame.actionDocSelect(row)
        return row

    def run(self):
        self.initialize()
        self.search('')
        self.view.show()
        return self

    def open(self):
        return self.run()

    def set_view(self, view):
        self.view = view
        self.view.attach_controller(self)
        self._is_initialized = False
        return self
