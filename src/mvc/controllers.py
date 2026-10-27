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

    def search(self, query=''):
        documents = self.model.search_documents(query)
        self.view.display_documents(documents)
        return documents

    def run(self):
        self.initialize()
        self.view.show()
        return self

    def open(self):
        return self.run()
