import os
import zipfile

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

    def _selected_rows(self):
        frame = getattr(self.view, 'frame', None)
        if frame is None or not hasattr(frame, 'get_selected_rows'):
            return []
        try:
            return frame.get_selected_rows() or []
        except Exception:
            return []

    def actionBasket(self):
        frame = getattr(self.view, 'frame', None)
        if frame is None or not hasattr(frame, '_basket_add_rows'):
            return []
        rows = self._selected_rows()
        frame._basket_add_rows(rows)
        return rows

    def open_basket(self):
        return self.actionBasket()

    def _current_query(self):
        frame = getattr(self.view, 'frame', None)
        if frame is not None and hasattr(frame, '_search'):
            try:
                return frame._search.text()
            except Exception:
                return ''
        return ''

    def _set_status(self, text):
        frame = getattr(self.view, 'frame', None)
        if frame is not None and hasattr(frame, '_status'):
            frame._status.setText(text)

    def _document_filename(self, row):
        if isinstance(row, dict):
            for key in ('filename', 'path', 'file', 'document_path'):
                value = row.get(key)
                if value not in (None, ''):
                    return str(value)
            return None
        if isinstance(row, (list, tuple)):
            db = self.model._get_db()
            idx = getattr(db, 'IDX_FILENAME', None) if db is not None else None
            if idx is not None and idx < len(row):
                value = row[idx]
                if value not in (None, ''):
                    return str(value)
        return None

    def actionRemoveRecord(self):
        rows = self._selected_rows()
        if not rows:
            return False
        if self.model.delete_documents(rows):
            self.search(self._current_query())
            return True
        return False

    def remove_documents_with_mode(self, rows, delete_mode):
        rows = rows or self._selected_rows()
        if not rows:
            return 0
        try:
            self.model.delete_documents(rows, delete_files=delete_mode)
            self.search(self._current_query())
            return len(rows)
        except Exception:
            return 0

    def add_file(self, file_paths):
        added = 0
        for path in file_paths or []:
            try:
                if not path or not os.path.isfile(path):
                    continue
                title = os.path.splitext(os.path.basename(path))[0] or 'untitled'
                result = self.model.add_document(path, title)
                if result:
                    added += 1
            except Exception:
                continue
        self.search(self._current_query())
        self._set_status('%d file(s) imported' % added)
        return added

    def add_file_entries(self, entries):
        added = 0
        for entry in entries or []:
            try:
                path = entry.get('path') if isinstance(entry, dict) else None
                if not path or not os.path.isfile(path):
                    continue
                title = (entry.get('title') or os.path.splitext(os.path.basename(path))[0] or 'untitled') if isinstance(entry, dict) else 'untitled'
                description = entry.get('description', '') if isinstance(entry, dict) else ''
                tags = entry.get('tags', '') if isinstance(entry, dict) else ''
                document_date = entry.get('document_date') if isinstance(entry, dict) else None
                if not document_date:
                    document_date = None
                result = self.model.add_document(
                    path,
                    title,
                    description,
                    None,
                    document_date,
                    None,
                    tags,
                )
                if result:
                    added += 1
            except Exception:
                continue
        self.search(self._current_query())
        self._set_status('%d file(s) imported' % added)
        return added

    def add_scan(self, file_paths):
        # In Qt mode, scan import currently reuses file import semantics.
        return self.add_file(file_paths)

    def add_scan_entries(self, entries):
        return self.add_file_entries(entries)

    def start_survey(self):
        db = self.model._get_db()
        if db is None:
            return 0
        try:
            import database
            config = getattr(database, 'theConfig', None)
            if config is None:
                return 0
            extensions_raw = config.get_survey_extension_list() or ''
            accepted = set()
            for token in str(extensions_raw).replace(',', ' ').split():
                token = token.strip().lower()
                if not token:
                    continue
                if not token.startswith('.'):
                    token = '.' + token
                accepted.add(token)

            existing = set()
            rows = self.model.search_documents('')
            idx_filename = getattr(db, 'IDX_FILENAME', None)
            if idx_filename is not None:
                for row in rows:
                    if isinstance(row, (list, tuple)) and idx_filename < len(row):
                        filename = row[idx_filename]
                        if filename:
                            existing.add(os.path.abspath(str(filename)))

            dir_list, recursive_idx = config.get_survey_directory_list()
            imported = 0
            for i, root in enumerate(dir_list):
                if not root or not os.path.isdir(root):
                    continue
                is_recursive = i in recursive_idx
                if is_recursive:
                    iterator = os.walk(root)
                else:
                    iterator = [(root, [], os.listdir(root))]
                for current_root, _dirs, files in iterator:
                    for name in files:
                        full_path = os.path.abspath(os.path.join(current_root, name))
                        if accepted and os.path.splitext(name)[1].lower() not in accepted:
                            continue
                        if full_path in existing:
                            continue
                        title = os.path.splitext(os.path.basename(full_path))[0] or 'untitled'
                        if self.model.add_document(full_path, title):
                            existing.add(full_path)
                            imported += 1
            self.search(self._current_query())
            self._set_status('%d file(s) imported from survey' % imported)
            return imported
        except Exception:
            return 0

    def survey_candidates(self):
        try:
            import database
            config = getattr(database, 'theConfig', None)
            db = self.model._get_db()
            if config is None or db is None:
                return []

            extensions_raw = config.get_survey_extension_list() or ''
            accepted = set()
            for token in str(extensions_raw).replace(',', ' ').split():
                token = token.strip().lower()
                if not token:
                    continue
                if not token.startswith('.'):
                    token = '.' + token
                accepted.add(token)

            existing = set()
            rows = self.model.search_documents('')
            idx_filename = getattr(db, 'IDX_FILENAME', None)
            if idx_filename is not None:
                for row in rows:
                    if isinstance(row, (list, tuple)) and idx_filename < len(row):
                        filename = row[idx_filename]
                        if filename:
                            existing.add(os.path.abspath(str(filename)))

            dir_list, recursive_idx = config.get_survey_directory_list()
            candidates = []
            seen = set()
            for i, root in enumerate(dir_list):
                if not root or not os.path.isdir(root):
                    continue
                is_recursive = i in recursive_idx
                if is_recursive:
                    iterator = os.walk(root)
                else:
                    iterator = [(root, [], os.listdir(root))]
                for current_root, _dirs, files in iterator:
                    for name in files:
                        full_path = os.path.abspath(os.path.join(current_root, name))
                        if accepted and os.path.splitext(name)[1].lower() not in accepted:
                            continue
                        if full_path in existing or full_path in seen:
                            continue
                        seen.add(full_path)
                        candidates.append(full_path)
            return sorted(candidates)
        except Exception:
            return []

    def doc_to_go(self, rows, zip_path):
        if not zip_path:
            return 0
        selected_rows = rows or self.model.search_documents('')
        files = []
        for row in selected_rows:
            filename = self._document_filename(row)
            if not filename:
                continue
            if os.path.isfile(filename):
                files.append(filename)
        if not files:
            return 0
        added = 0
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in files:
                archive.write(path, arcname=os.path.basename(path))
                added += 1
        self._set_status('%d file(s) exported' % added)
        return added

    def doc_to_go_action(self, action, rows, output_path, import_dir=None):
        try:
            db = self.model._get_db()
            if db is None:
                return False
            selected_rows = rows or []
            if action == 'export_database':
                db.export_database(output_path, selected_rows)
                self._set_status('Database exported: %s' % output_path)
                return True
            if action == 'export_archive':
                db.export_archive(output_path, selected_rows)
                self._set_status('Archive exported: %s' % output_path)
                return True
            if action == 'import_archive':
                if not import_dir:
                    return False
                db.import_archive(output_path, import_dir)
                try:
                    import database
                    config = getattr(database, 'theConfig', None)
                    if config is not None:
                        dbname = os.path.join(import_dir, 'database.db')
                        config.set_database_name(dbname)
                        config.commit_config()
                except Exception:
                    pass
                self.search(self._current_query())
                self._set_status('Archive imported: %s' % output_path)
                return True
            return False
        except Exception:
            return False

    def actionAddFile(self):
        return True

    def actionAddScan(self):
        return True

    def actionDoPrint(self):
        return True

    def actionDocToGo(self):
        return True

    def actionStartSurvey(self):
        return self.start_survey()

    def actionShowPrefs(self):
        return True

    def actionAbout(self):
        return True

    def actionReport(self):
        return True

    def actionSupport(self):
        return True

    def open(self):
        return self.run()

    def set_view(self, view):
        self.view = view
        self.view.attach_controller(self)
        self._is_initialized = False
        return self
