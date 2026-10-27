class DocumentModel(object):
    """Model responsible for reading and mutating the application data."""

    def __init__(self, db=None):
        self.db = db

    def _get_db(self):
        if self.db is not None:
            return self.db
        try:
            import database
            return getattr(database, 'theBase', None)
        except Exception:
            return None

    def search_documents(self, query=''):
        db = self._get_db()
        if db is None:
            return []
        try:
            if not query:
                rows = db.find_documents(None)
                return list(rows) if rows is not None else []
            import algorithms.stringFunctions as SF
            request, pars = SF.req_to_sql(query)
            rows = db.find_sql(request, pars)
            return list(rows) if rows is not None else []
        except Exception:
            return []

    def add_document(self, *args, **kwargs):
        db = self._get_db()
        if db is None or not hasattr(db, 'add_document'):
            return None
        return db.add_document(*args, **kwargs)

    def delete_documents(self, rows, **kwargs):
        db = self._get_db()
        if db is None or not hasattr(db, 'delete_documents'):
            return False
        db.delete_documents(rows, **kwargs)
        return True

    def update_document(self, *args, **kwargs):
        db = self._get_db()
        if db is None or not hasattr(db, 'update_document'):
            return False
        return db.update_document(*args, **kwargs)
