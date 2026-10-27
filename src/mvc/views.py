import ast
import contextlib
import configparser
import os
import tempfile
import webbrowser
from urllib.parse import quote

from .qt_setup import get_qapplication_class


def _to_text(value):
    if value is None:
        return ''
    if isinstance(value, bytes):
        for encoding in ('utf-8', 'utf-8-sig', 'latin-1', 'ascii'):
            try:
                return value.decode(encoding)
            except UnicodeDecodeError:
                continue
        return value.decode('utf-8', 'replace')
    if isinstance(value, str):
        if value.startswith(("b'", 'b"')):
            try:
                parsed = ast.literal_eval(value)
                if isinstance(parsed, bytes):
                    for encoding in ('utf-8', 'utf-8-sig', 'latin-1', 'ascii'):
                        try:
                            return parsed.decode(encoding)
                        except UnicodeDecodeError:
                            continue
                    return parsed.decode('utf-8', 'replace')
            except Exception:
                pass
        return value
    return str(value)


@contextlib.contextmanager
def _suppress_native_output():
    """Temporarily silence low-level stdout/stderr writes from scanner backends."""
    null_fd = None
    old_stdout = None
    old_stderr = None
    try:
        null_fd = os.open(os.devnull, os.O_WRONLY)
        old_stdout = os.dup(1)
        old_stderr = os.dup(2)
        os.dup2(null_fd, 1)
        os.dup2(null_fd, 2)
        yield
    finally:
        try:
            if old_stdout is not None:
                os.dup2(old_stdout, 1)
            if old_stderr is not None:
                os.dup2(old_stderr, 2)
        finally:
            for fd in (old_stdout, old_stderr, null_fd):
                if fd is not None:
                    try:
                        os.close(fd)
                    except Exception:
                        pass

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QAction, QIcon, QImage, QPainter, QPixmap, QTextDocument
    from PySide6.QtPrintSupport import QPrintDialog, QPrinter
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QComboBox,
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QFormLayout,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSplitter,
        QSizePolicy,
        QTabWidget,
        QTextBrowser,
        QTextEdit,
        QToolBar,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover - optional in non-GUI test runs
    QAction = QToolBar = QApplication = QHBoxLayout = QLabel = QLineEdit = QListWidget = QListWidgetItem = QMainWindow = QPushButton = QTextBrowser = QVBoxLayout = QWidget = None
    QScrollArea = QSplitter = QSizePolicy = QTabWidget = QTreeWidget = QTreeWidgetItem = QAbstractItemView = None
    QFileDialog = None
    QInputDialog = QMessageBox = None
    QDialog = QDialogButtonBox = QFormLayout = QTextEdit = QCheckBox = QComboBox = None
    QPrinter = QPrintDialog = QTextDocument = None
    QPixmap = None
    QIcon = None
    Qt = None

QApplication = get_qapplication_class() or QApplication
_RUNTIME_QAPP = None


class _SimpleFrame(object):
    def __init__(self, title='MALODOS'):
        self.title = title
        self.docList = []

    def initialize(self):
        return self

    def Show(self, value=True):
        return value


class QtMainWindow(QMainWindow if QMainWindow is not None else object):
    def __init__(self, title='MALODOS'):
        global _RUNTIME_QAPP
        if QMainWindow is None:
            self.title = title
            self.docList = []
            return
        if QApplication is not None and QApplication.instance() is None:
            _RUNTIME_QAPP = QApplication([])
        super(QtMainWindow, self).__init__()
        self.setWindowTitle(title)
        self.docList = []
        self.basket = []
        self.controller = None
        self._search_in_progress = False

        self._viewer = QWidget(self)
        self._preview_panel = QWidget(self._viewer)
        self._viewer_layout = QVBoxLayout(self._viewer)
        self._viewer_layout.setContentsMargins(0, 0, 0, 0)

        self._main_toolbar = self._build_main_toolbar()

        self._search, self._search_button, self._advanced_button, self._search_bar = self._build_search_bar()
        self._list = QListWidget(self._viewer)
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.currentRowChanged.connect(self._on_current_row_changed)
        if QAbstractItemView is not None:
            self._list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self._folder_tree = QTreeWidget(self._viewer) if QTreeWidget is not None else None
        if self._folder_tree is not None:
            self._folder_tree.setHeaderLabel('Folders')
            self._folder_tree.itemSelectionChanged.connect(self._on_folder_tree_selection_changed)
            if QAbstractItemView is not None:
                self._folder_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self._tag_tree = QTreeWidget(self._viewer) if QTreeWidget is not None else None
        if self._tag_tree is not None:
            self._tag_tree.setHeaderLabel('Tags')
            self._tag_tree.itemSelectionChanged.connect(self._on_tag_tree_selection_changed)
            if QAbstractItemView is not None:
                self._tag_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self._basket_list = QListWidget(self._viewer)
        self._basket_list.itemClicked.connect(self._on_basket_item_clicked)
        self._basket_remove_button = QPushButton('Remove from basket', self._viewer)
        self._basket_remove_button.clicked.connect(self.action_basket_remove_selection)
        self._basket_clear_button = QPushButton('Clear basket', self._viewer)
        self._basket_clear_button.clicked.connect(self.action_basket_clear)

        self._left_tabs = QTabWidget(self._viewer) if QTabWidget is not None else None
        if self._left_tabs is not None:
            flat_tab = QWidget(self._left_tabs)
            flat_layout = QVBoxLayout(flat_tab)
            flat_layout.setContentsMargins(0, 0, 0, 0)
            flat_layout.addWidget(self._list)

            folder_tab = QWidget(self._left_tabs)
            folder_layout = QVBoxLayout(folder_tab)
            folder_layout.setContentsMargins(0, 0, 0, 0)
            if self._folder_tree is not None:
                folder_layout.addWidget(self._folder_tree)

            tag_tab = QWidget(self._left_tabs)
            tag_layout = QVBoxLayout(tag_tab)
            tag_layout.setContentsMargins(0, 0, 0, 0)
            if self._tag_tree is not None:
                tag_layout.addWidget(self._tag_tree)

            basket_tab = QWidget(self._left_tabs)
            basket_layout = QVBoxLayout(basket_tab)
            basket_layout.setContentsMargins(0, 0, 0, 0)
            basket_layout.addWidget(self._basket_list, 1)
            basket_buttons = QHBoxLayout()
            basket_buttons.addWidget(self._basket_remove_button)
            basket_buttons.addWidget(self._basket_clear_button)
            basket_layout.addLayout(basket_buttons)

            self._left_tabs.addTab(flat_tab, 'Flat view')
            self._left_tabs.addTab(folder_tab, 'Folder view')
            self._left_tabs.addTab(tag_tab, 'Tag folder view')
            self._left_tabs.addTab(basket_tab, 'Basket view')

        self._status = QLabel('0 document(s)', self._viewer)
        self._details = QTextBrowser(self._viewer)
        self._details.setPlaceholderText('Select a document to view details')
        self._image = QLabel('No document image', self._viewer)
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter if Qt is not None else 0)
        self._image.setMinimumHeight(220)
        self._image.setStyleSheet('border: 1px solid #aaaaaa; background: #f8f8f8;')
        if QSizePolicy is not None:
            self._image.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self._zoom = 1.0
        self._last_pixmap = None

        self._toolbar = self._build_toolbar()

        preview_layout = QVBoxLayout(self._preview_panel)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.addWidget(self._toolbar)
        self._image_scroll = QScrollArea(self._preview_panel) if QScrollArea is not None else None
        if self._image_scroll is not None:
            self._image_scroll.setWidget(self._image)
            self._image_scroll.setWidgetResizable(False)

        self._right_splitter = QSplitter(Qt.Orientation.Vertical, self._preview_panel) if QSplitter is not None and Qt is not None else None
        if self._right_splitter is not None:
            self._right_splitter.addWidget(self._details)
            if self._image_scroll is not None:
                self._right_splitter.addWidget(self._image_scroll)
            else:
                self._right_splitter.addWidget(self._image)
            self._right_splitter.setChildrenCollapsible(False)
            self._right_splitter.setStretchFactor(0, 1)
            self._right_splitter.setStretchFactor(1, 2)
            preview_layout.addWidget(self._right_splitter, 1)
        else:
            preview_layout.addWidget(self._details, 2)
            if self._image_scroll is not None:
                preview_layout.addWidget(self._image_scroll, 1)
            else:
                preview_layout.addWidget(self._image, 1)

        self._main_splitter = QSplitter(Qt.Orientation.Horizontal, self._viewer) if QSplitter is not None and Qt is not None else None
        if self._main_splitter is not None:
            self._main_splitter.addWidget(self._left_tabs if self._left_tabs is not None else self._list)
            self._main_splitter.addWidget(self._preview_panel)
            self._main_splitter.setChildrenCollapsible(False)
            self._main_splitter.setStretchFactor(0, 1)
            self._main_splitter.setStretchFactor(1, 2)

        self._viewer_layout.addWidget(self._search_bar)
        if self._main_splitter is not None:
            self._viewer_layout.addWidget(self._main_splitter, 1)
        else:
            content = QWidget(self._viewer)
            content_layout = QHBoxLayout(content)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.addWidget(self._left_tabs if self._left_tabs is not None else self._list, 1)
            content_layout.addWidget(self._preview_panel, 2)
            self._viewer_layout.addWidget(content, 1)
        self._viewer_layout.addWidget(self._status)
        self.setCentralWidget(self._viewer)
        self.resize(1024, 720)

    def _build_search_bar(self):
        search = QLineEdit(self._viewer)
        search.setPlaceholderText('Search documents...')
        search.textChanged.connect(self.actionSearch)
        search.returnPressed.connect(self.actionSearch)

        search_button = QPushButton('Search', self._viewer)
        search_button.clicked.connect(self.actionSearch)

        advanced_button = QPushButton('Advanced', self._viewer)
        advanced_button.clicked.connect(self.action_build_request)

        bar = QWidget(self._viewer)
        layout = QHBoxLayout(bar)
        layout.addWidget(search)
        layout.addWidget(search_button)
        layout.addWidget(advanced_button)
        return search, search_button, advanced_button, bar

    def _build_toolbar(self):
        toolbar = QToolBar('Preview tools', self._preview_panel)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.addAction(self._create_toolbar_action('Previous page', self.action_previous_page, icon_id='PREVIOUS_PAGE'))
        toolbar.addAction(self._create_toolbar_action('Next page', self.action_next_page, icon_id='NEXT_PAGE'))
        toolbar.addSeparator()
        toolbar.addAction(self._create_toolbar_action('Zoom +', self.action_zoom_in, icon_id='ZOOM_PLUS'))
        toolbar.addAction(self._create_toolbar_action('Zoom -', self.action_zoom_out, icon_id='ZOOM_MINUS'))
        return toolbar

    def _build_main_toolbar(self):
        toolbar = QToolBar('Main actions', self)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.addAction(self._create_toolbar_action('Add file', self.action_add_file, icon_id='ADD_FILE'))
        toolbar.addAction(self._create_toolbar_action('Add scan', self.action_add_scan, icon_id='ADD_SCAN'))
        toolbar.addAction(self._create_toolbar_action('Remove selection', self.action_remove_selection, icon_id='REMOVE_SELECTION'))
        toolbar.addAction(self._create_toolbar_action('Print', self.action_print_document, icon_id='DOC_PRINT'))
        toolbar.addAction(self._create_toolbar_action('Basket', self.action_basket, icon_id='DOC_BASKET'))
        toolbar.addAction(self._create_toolbar_action('Doc to go', self.action_doc_to_go, icon_id='DOC_ZIP'))
        toolbar.addAction(self._create_toolbar_action('Survey', self.action_start_survey, icon_id='SURVEY_WIN'))
        toolbar.addAction(self._create_toolbar_action('Preferences', self.action_show_preferences, icon_id='PREFS'))
        toolbar.addAction(self._create_toolbar_action('Credits', self.action_about, icon_id='CREDITS'))
        toolbar.addAction(self._create_toolbar_action('Bug report', self.action_report, icon_id='BUGREPORT'))
        toolbar.addAction(self._create_toolbar_action('Support', self.action_support, icon_id='SUPPORT'))
        self.addToolBar(toolbar)
        return toolbar

    def initialize(self):
        return self

    def Show(self, value=True):
        if value and QMainWindow is not None:
            self.show()
        return self

    def _icon_for(self, icon_id):
        if QIcon is None or not icon_id:
            return None
        try:
            import database.Resources as Resources
            icon_path = Resources.get_icon_filename(icon_id)
            if icon_path and os.path.exists(icon_path):
                return QIcon(icon_path)
        except Exception:
            pass
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            resources_file = os.path.join(project_root, 'resources', 'resources.ini')
            parser = configparser.ConfigParser(strict=False)
            parser.read(resources_file)
            if parser.has_option('icons', icon_id):
                icon_name = parser.get('icons', icon_id)
                icon_path = os.path.join(project_root, 'resources', 'icons', icon_name)
                if os.path.exists(icon_path):
                    return QIcon(icon_path)
        except Exception:
            pass
        return None

    def _create_toolbar_action(self, text, slot, icon_id=None):
        icon = self._icon_for(icon_id)
        if icon is not None and not icon.isNull():
            action = QAction(icon, text, self)
        else:
            action = QAction(text, self)
        action.triggered.connect(slot)
        return action

    def _document_title(self, row):
        if isinstance(row, dict):
            for key in ('title', 'filename', 'name', 'document_name'):
                if key in row and row[key] not in (None, ''):
                    return _to_text(row[key])
            return _to_text(row)
        if isinstance(row, (list, tuple)):
            try:
                import database
                idx = getattr(database.theBase, 'IDX_TITLE', None)
                if idx is not None and idx < len(row):
                    value = row[idx]
                    if value not in (None, ''):
                        return _to_text(value)
            except Exception:
                pass
            return ' '.join(_to_text(part) for part in row if part not in (None, '')) or _to_text(row)
        return _to_text(row)

    def actionSearch(self, *_args):
        if self.controller is None:
            return
        if self._search_in_progress:
            return
        self._search_in_progress = True
        try:
            query = self._search.text() if hasattr(self, '_search') else ''
            self.controller.search(query)
        finally:
            self._search_in_progress = False

    def _dispatch_controller_action(self, *method_names):
        if self.controller is None:
            return
        for method_name in method_names:
            method = getattr(self.controller, method_name, None)
            if callable(method):
                method()
                return

    def action_add_file(self):
        if QFileDialog is None:
            self._dispatch_controller_action('actionAddFile', 'add_file')
            return
        file_names, _selected_filter = QFileDialog.getOpenFileNames(
            self,
            'Select document file(s)',
            '',
            'All files (*.*)',
        )
        if not file_names:
            return
        add_entries_method = getattr(self.controller, 'add_file_entries', None)
        if callable(add_entries_method):
            entries = self._collect_metadata_entries(file_names, 'Add document metadata')
            if not entries:
                return
            added_count = add_entries_method(entries)
            self._status.setText('%d file(s) imported' % self._safe_int(added_count))
            return
        add_file_method = getattr(self.controller, 'add_file', None)
        if callable(add_file_method):
            added_count = add_file_method(file_names)
            self._status.setText('%d file(s) imported' % self._safe_int(added_count))
        else:
            self._dispatch_controller_action('actionAddFile', 'add_file')

    def action_add_scan(self):
        if QFileDialog is None:
            self._dispatch_controller_action('actionAddScan', 'add_scan')
            return
        file_names = self._acquire_scan_files()
        if not file_names:
            return
        add_entries_method = getattr(self.controller, 'add_file_entries', None)
        if callable(add_entries_method):
            entries = self._collect_metadata_entries(file_names, 'Scanned document metadata')
            if not entries:
                return
            added_count = add_entries_method(entries)
            self._status.setText('%d file(s) imported' % self._safe_int(added_count))
            return
        add_scan_method = getattr(self.controller, 'add_scan', None)
        if callable(add_scan_method):
            added_count = add_scan_method(file_names)
            self._status.setText('%d file(s) imported' % self._safe_int(added_count))
        else:
            self._dispatch_controller_action('actionAddScan', 'add_scan')

    def action_remove_selection(self):
        rows = self.get_selected_rows()
        if not rows:
            return
        remover = getattr(self.controller, 'remove_documents_with_mode', None)
        if not callable(remover):
            self._dispatch_controller_action('actionRemoveRecord', 'remove_selection')
            return
        if QMessageBox is None:
            remover(rows, 2)
            return

        message = 'This will delete %d selected record(s). Choose an action.' % len(rows)
        dialog = QMessageBox(self)
        dialog.setWindowTitle('Remove selection')
        dialog.setText(message)
        db_btn = dialog.addButton('Remove from database', QMessageBox.ButtonRole.AcceptRole)
        both_btn = dialog.addButton('Remove from database and disk', QMessageBox.ButtonRole.DestructiveRole)
        cancel_btn = dialog.addButton('Cancel', QMessageBox.ButtonRole.RejectRole)
        dialog.exec()

        clicked = dialog.clickedButton()
        if clicked is cancel_btn:
            return
        delete_mode = 2 if clicked is db_btn else 3
        removed = remover(rows, delete_mode)
        self._status.setText('%d record(s) removed' % self._safe_int(removed))

    def action_print_document(self):
        if not self.docList:
            if QMessageBox is not None:
                QMessageBox.information(self, 'Print', 'No document selected.')
            return
        row_index = self._list.currentRow() if hasattr(self, '_list') and self._list is not None else -1
        if row_index < 0 or row_index >= len(self.docList):
            row_index = 0
        selected = self.docList[row_index]

        if QPrinter is None or QPrintDialog is None or QTextDocument is None:
            self._status.setText('Print backend is not available in this environment')
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        document = QTextDocument()
        filename = self._document_filename(selected)
        pixmap = self._document_pixmap(filename)
        if pixmap is not None and not pixmap.isNull():
            painter = QPainter(printer)
            try:
                rect = painter.viewport()
                scaled = pixmap.scaled(
                    rect.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                painter.drawPixmap(0, 0, scaled)
            finally:
                painter.end()
        else:
            details = self._document_details(selected).replace('\n', '<br>')
            document.setHtml('<h2>MALODOS</h2><p>%s</p>' % details)
            document.print_(printer)
        self._status.setText('Document sent to printer')

    def action_basket(self):
        rows = self.get_selected_rows()
        if rows:
            self._basket_add_rows(rows)
        if self._left_tabs is not None:
            self._left_tabs.setCurrentIndex(3)
        self._dispatch_controller_action('actionBasket', 'open_basket')

    def action_basket_remove_selection(self):
        rows = []
        for item in self._basket_list.selectedItems():
            row = item.data(Qt.ItemDataRole.UserRole if Qt is not None else 0)
            if row is not None:
                rows.append(row)
        self._basket_remove_rows(rows)

    def action_basket_clear(self):
        self.basket = []
        self._refresh_basket_view()

    def action_build_request(self):
        if QInputDialog is None:
            return
        current = self._search.text() if hasattr(self, '_search') else ''
        query, accepted = QInputDialog.getText(
            self,
            'Advanced query',
            'Enter an advanced filter expression:',
            text=current,
        )
        if accepted:
            self._search.setText(query)

    def action_doc_to_go(self):
        if QFileDialog is None:
            self._dispatch_controller_action('actionDocToGo', 'doc_to_go')
            return

        legacy_exporter = getattr(self.controller, 'doc_to_go', None)
        do_action = getattr(self.controller, 'doc_to_go_action', None)

        # Compatibility path used by lightweight controller stubs and older call sites.
        if callable(legacy_exporter) and not callable(do_action):
            rows = self.get_selected_rows()
            if not rows:
                rows = list(self.docList)
            if not rows:
                self._status.setText('No document available for export')
                return
            zip_path, _selected_filter = QFileDialog.getSaveFileName(
                self,
                'Export documents',
                'documents.zip',
                'Zip archives (*.zip)',
            )
            if not zip_path:
                return
            if not zip_path.lower().endswith('.zip'):
                zip_path += '.zip'
            added = legacy_exporter(rows, zip_path)
            self._status.setText('%d file(s) exported to %s' % (self._safe_int(added), zip_path))
            return

        if QDialog is None or QFormLayout is None or QDialogButtonBox is None or QComboBox is None:
            self._dispatch_controller_action('actionDocToGo', 'doc_to_go')
            return

        dialog = QDialog(self)
        dialog.setWindowTitle('Document to go')
        layout = QFormLayout(dialog)

        action_combo = QComboBox(dialog)
        action_combo.addItem('Export database', 'export_database')
        action_combo.addItem('Export archive', 'export_archive')
        action_combo.addItem('Import archive', 'import_archive')

        scope_combo = QComboBox(dialog)
        scope_combo.addItem('Selected documents', 'selected')
        scope_combo.addItem('Current search result', 'filter')
        scope_combo.addItem('Basket documents', 'basket')
        scope_combo.addItem('All documents', 'all')

        layout.addRow('Action', action_combo)
        layout.addRow('Documents scope', scope_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, parent=dialog)
        layout.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        action_key = action_combo.currentData()
        scope_key = scope_combo.currentData()
        rows = self._rows_for_doc_to_go_scope(scope_key)

        if not callable(do_action):
            self._dispatch_controller_action('actionDocToGo', 'doc_to_go')
            return

        if action_key == 'import_archive':
            archive_path, _selected_filter = QFileDialog.getOpenFileName(
                self,
                'Import archive',
                '',
                'Zip archives (*.zip)',
            )
            if not archive_path:
                return
            import_dir = QFileDialog.getExistingDirectory(self, 'Select extraction directory')
            if not import_dir:
                return
            ok = do_action('import_archive', [], archive_path, import_dir)
            if not ok:
                self._status.setText('Unable to import archive')
            return

        default_name = 'documents.db' if action_key == 'export_database' else 'documents.zip'
        output_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            'Export',
            default_name,
            'Database files (*.db);;Zip archives (*.zip);;All files (*.*)',
        )
        if not output_path:
            return
        if action_key == 'export_archive' and not output_path.lower().endswith('.zip'):
            output_path += '.zip'
        ok = do_action(action_key, rows, output_path)
        if not ok:
            self._status.setText('Unable to export documents')

    def _rows_for_doc_to_go_scope(self, scope_key):
        if scope_key == 'selected':
            return self.get_selected_rows()
        if scope_key == 'basket':
            return list(self.basket)
        if scope_key == 'all':
            if self.controller is not None and hasattr(self.controller, 'model'):
                try:
                    return self.controller.model.search_documents('')
                except Exception:
                    return []
            return []
        return list(self.docList)

    def _show_survey_candidates_dialog(self, candidates):
        if QDialog is None or QVBoxLayout is None or QListWidget is None or QDialogButtonBox is None:
            return []
        dialog = QDialog(self)
        dialog.setWindowTitle('Directory survey')
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel('Files not in the database:', dialog))
        file_list = QListWidget(dialog)
        if QAbstractItemView is not None:
            file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        for path in candidates:
            item = QListWidgetItem(path)
            item.setSelected(True)
            file_list.addItem(item)
        layout.addWidget(file_list)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, parent=dialog)
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return []
        return [item.text() for item in file_list.selectedItems()]

    def action_start_survey(self):
        if self.controller is None:
            self._dispatch_controller_action('actionStartSurvey', 'start_survey')
            return
        lister = getattr(self.controller, 'survey_candidates', None)
        importer = getattr(self.controller, 'add_file_entries', None)
        if not callable(lister) or not callable(importer):
            starter = getattr(self.controller, 'start_survey', None)
            if callable(starter):
                imported = starter()
                self._status.setText('%d file(s) imported from survey' % self._safe_int(imported))
            return
        candidates = lister()
        if not candidates:
            self._status.setText('No new file found in survey directories')
            return
        selected = self._show_survey_candidates_dialog(candidates)
        if not selected:
            return
        entries = self._collect_metadata_entries(selected, 'Survey document metadata')
        if not entries:
            return
        imported = importer(entries)
        self._status.setText('%d file(s) imported from survey' % self._safe_int(imported))

    def _safe_int(self, value):
        try:
            return int(value or 0)
        except Exception:
            return 0

    def _collect_metadata_entries(self, file_names, window_title):
        if QDialog is None or QFormLayout is None or QDialogButtonBox is None:
            return [{'path': path} for path in file_names if path]
        entries = []
        for path in file_names:
            metadata = self._ask_document_metadata(path, window_title)
            if metadata is None:
                break
            entries.append(metadata)
        return entries

    def _ask_document_metadata(self, file_path, window_title):
        dialog = QDialog(self)
        dialog.setWindowTitle(window_title)
        layout = QFormLayout(dialog)

        title_default = os.path.splitext(os.path.basename(file_path))[0] or 'untitled'
        title_edit = QLineEdit(title_default, dialog)
        tags_edit = QLineEdit('', dialog)
        description_edit = QTextEdit(dialog)
        description_edit.setMinimumHeight(120)
        date_edit = QLineEdit('', dialog)
        date_edit.setPlaceholderText('YYYY-MM-DD (optional)')
        preview_label = QLabel(dialog)
        preview_label.setMinimumHeight(180)
        preview_label.setStyleSheet('border: 1px solid #aaaaaa; background: #f8f8f8;')
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        preview_pixmap = self._document_pixmap(file_path)
        if preview_pixmap is not None and not preview_pixmap.isNull():
            preview_label.setPixmap(
                preview_pixmap.scaled(
                    320,
                    240,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            preview_label.setText('No preview available')

        layout.addRow('File', QLabel(file_path, dialog))
        layout.addRow('Preview', preview_label)
        layout.addRow('Title', title_edit)
        layout.addRow('Tags', tags_edit)
        layout.addRow('Description', description_edit)
        layout.addRow('Document date', date_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, parent=dialog)
        layout.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        return {
            'path': file_path,
            'title': title_edit.text().strip() or title_default,
            'tags': tags_edit.text().strip(),
            'description': description_edit.toPlainText().strip(),
            'document_date': date_edit.text().strip(),
        }

    def _acquire_scan_files(self):
        if os.name == 'nt':
            return self._acquire_scan_files_twain()
        return self._acquire_scan_files_sane()

    def _acquire_scan_files_twain(self):
        try:
            import twain
            from PIL import Image as PILImage
        except Exception:
            if QMessageBox is not None:
                QMessageBox.warning(
                    self,
                    'Scan',
                    'TWAIN backend is unavailable. Select scanned files manually.',
                )
            file_names, _selected_filter = QFileDialog.getOpenFileNames(
                self,
                'Select scanned file(s)',
                '',
                'Images and PDF (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.pdf);;All files (*.*)',
            )
            return file_names

        source_manager = None
        source = None
        files = []
        handles = []
        try:
            hwnd = int(self.winId()) if hasattr(self, 'winId') else 0
            source_manager = twain.SourceManager(hwnd, ProductName='MALODOS')
            source_list = source_manager.GetSourceList() or []
            if not source_list:
                if QMessageBox is not None:
                    QMessageBox.warning(self, 'Scan', 'No TWAIN scanner source detected.')
                return []

            selected_source, accepted = QInputDialog.getItem(
                self,
                'Scanner source',
                'Choose a scanner source:',
                list(source_list),
                0,
                False,
            )
            if not accepted:
                return []

            source = source_manager.OpenSource(selected_source)
            source.RequestAcquire(0, 0)

            while True:
                try:
                    handle, more_to_come = source.XferImageNatively()
                except Exception:
                    break
                if not handle:
                    break
                handles.append(handle)
                fd_bmp, bmp_path = tempfile.mkstemp(prefix='malodos_twain_', suffix='.bmp')
                os.close(fd_bmp)
                twain.DIBToBMFile(handle, bmp_path)

                fd_png, png_path = tempfile.mkstemp(prefix='malodos_scan_', suffix='.png')
                os.close(fd_png)
                with PILImage.open(bmp_path) as img:
                    img.load()
                    img.save(png_path)
                try:
                    os.unlink(bmp_path)
                except Exception:
                    pass
                files.append(png_path)
                if not more_to_come:
                    break

            if not files and QMessageBox is not None:
                QMessageBox.warning(self, 'Scan', 'No image received from TWAIN source.')
            return files
        except Exception as exc:
            if QMessageBox is not None:
                QMessageBox.warning(self, 'Scan', 'TWAIN acquisition failed: %s' % exc)
            return []
        finally:
            for handle in handles:
                try:
                    twain.GlobalHandleFree(handle)
                except Exception:
                    pass
            if source is not None:
                try:
                    source.destroy()
                except Exception:
                    pass
            if source_manager is not None:
                try:
                    source_manager.destroy()
                except Exception:
                    pass

    def _acquire_scan_files_sane(self):
        try:
            import sane
            from PIL import Image as PILImage
        except Exception:
            if QMessageBox is not None:
                QMessageBox.warning(
                    self,
                    'Scan',
                    'SANE backend is unavailable. Select scanned files manually.',
                )
            file_names, _selected_filter = QFileDialog.getOpenFileNames(
                self,
                'Select scanned file(s)',
                '',
                'Images and PDF (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.pdf);;All files (*.*)',
            )
            return file_names

        try:
            with _suppress_native_output():
                sane.init()
                devices = sane.get_devices() or []
            if not devices:
                if QMessageBox is not None:
                    QMessageBox.warning(self, 'Scan', 'No SANE scanner device detected.')
                return []
            device_labels = [d[2] or d[0] for d in devices]
            selected_label, accepted = QInputDialog.getItem(
                self,
                'Scanner source',
                'Choose a scanner source:',
                device_labels,
                0,
                False,
            )
            if not accepted:
                return []
            idx = device_labels.index(selected_label)
            scanner_name = devices[idx][0]

            with _suppress_native_output():
                scanner = sane.open(scanner_name)
                image = scanner.scan()
                scanner.close()

            if not isinstance(image, PILImage.Image):
                if QMessageBox is not None:
                    QMessageBox.warning(self, 'Scan', 'Scanner did not return an image.')
                return []

            fd, tmp_path = tempfile.mkstemp(prefix='malodos_scan_', suffix='.png')
            os.close(fd)
            image.save(tmp_path)
            return [tmp_path]
        except Exception as exc:
            if QMessageBox is not None:
                QMessageBox.warning(self, 'Scan', 'SANE acquisition failed: %s' % exc)
            return []

    def action_show_preferences(self):
        if QDialog is None or QFormLayout is None or QDialogButtonBox is None:
            self._dispatch_controller_action('actionShowPrefs', 'show_preferences')
            return
        try:
            import database
            config = getattr(database, 'theConfig', None)
        except Exception:
            config = None
        if config is None:
            self._status.setText('Configuration is not available')
            return

        dialog = QDialog(self)
        dialog.setWindowTitle('Preferences')
        layout = QFormLayout(dialog)

        language_edit = QLineEdit(config.get_param('language', 'current', 'sys'), dialog)
        ext_edit = QLineEdit(config.get_survey_extension_list(), dialog)
        auto_ocr = QCheckBox(dialog)
        auto_ocr.setChecked(config.get_param('OCR', 'autoStart', '1') in ('1', 'true', 'True'))
        auto_scan = QCheckBox(dialog)
        auto_scan.setChecked(config.get_param('scanner', 'autoScan', 'False', True).lower() == 'true')
        auto_filename = QCheckBox(dialog)
        auto_filename.setChecked(config.get_param('scanner', 'autoFileName', 'False', True).lower() == 'true')
        scan_prefix = QLineEdit(config.get_param('scanner', 'autoFileNamePrefix', 'file', True), dialog)
        default_scan_dir = QLineEdit(config.get_param('scanner', 'defaultDir', '', True), dialog)
        encrypt_data = QCheckBox(dialog)
        encrypt_data.setChecked(config.get_param('encryption', 'encryptData', 'False', True).lower() == 'true')
        encrypt_db = QCheckBox(dialog)
        encrypt_db.setChecked(config.get_param('encryption', 'encryptDatabase', 'False', True).lower() == 'true')

        layout.addRow('Language', language_edit)
        layout.addRow('Survey extensions', ext_edit)
        layout.addRow('Auto-start OCR', auto_ocr)
        layout.addRow('Auto scan', auto_scan)
        layout.addRow('Automatic file name', auto_filename)
        layout.addRow('Auto file name prefix', scan_prefix)
        layout.addRow('Default scan directory', default_scan_dir)
        layout.addRow('Encrypt image files', encrypt_data)
        layout.addRow('Encrypt database file', encrypt_db)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, parent=dialog)
        layout.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        config.set_current_language(language_edit.text().strip() or 'sys')
        config.set_survey_extension_list(ext_edit.text().strip())
        config.set_param('OCR', 'autoStart', '1' if auto_ocr.isChecked() else '0')
        config.set_param('scanner', 'autoScan', 'True' if auto_scan.isChecked() else 'False', True)
        config.set_param('scanner', 'autoFileName', 'True' if auto_filename.isChecked() else 'False', True)
        config.set_param('scanner', 'autoFileNamePrefix', scan_prefix.text().strip() or 'file', True)
        config.set_param('scanner', 'defaultDir', default_scan_dir.text().strip(), True)
        config.set_param('encryption', 'encryptData', 'True' if encrypt_data.isChecked() else 'False', True)
        config.set_param('encryption', 'encryptDatabase', 'True' if encrypt_db.isChecked() else 'False', True)
        config.commit_config()
        self._status.setText('Preferences saved')

    def action_about(self):
        if QMessageBox is None:
            self._dispatch_controller_action('actionAbout', 'show_about')
            return
        try:
            from homeDocs import __version__
        except Exception:
            __version__ = 'unknown'
        text = (
            'MALODOS (MAnagement of LOcal DOcument System)\\n\\n'
            'Simple document archiving and navigation utility.\\n'
            'Version: %s\\n\\n'
            'Project website: http://sites.google.com/site/malodospage/'
        ) % __version__
        QMessageBox.about(self, 'About MALODOS', text)

    def action_report(self):
        if QDialog is None or QFormLayout is None or QTextEdit is None or QDialogButtonBox is None:
            self._dispatch_controller_action('actionReport', 'report_bug')
            return
        dialog = QDialog(self)
        dialog.setWindowTitle('Bug report')
        layout = QFormLayout(dialog)

        name_edit = QLineEdit(dialog)
        description_edit = QTextEdit(dialog)
        description_edit.setMinimumHeight(180)

        layout.addRow('Your name', name_edit)
        layout.addRow('Bug description', description_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, parent=dialog)
        layout.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            from homeDocs import __version__
        except Exception:
            __version__ = 'unknown'

        subject = 'BUG report for MALODOS version %s' % __version__
        body = 'Hello, my name is %s\\nI found a bug described here:\\n%s\\n' % (
            name_edit.text().strip(),
            description_edit.toPlainText().strip(),
        )

        try:
            import database
            conf_dir = getattr(getattr(database, 'theConfig', None), 'conf_dir', None)
            if conf_dir:
                logfilename = os.path.join(conf_dir, 'messages.log')
                if os.path.exists(logfilename):
                    with open(logfilename, 'r', encoding='utf-8', errors='replace') as log_file:
                        body += '\\n\\nLog file content:\\n----------\\n'
                        body += log_file.read()
        except Exception:
            pass

        mailto_url = 'mailto:guezdav@gmail.com?subject=%s&body=%s' % (
            quote(subject),
            quote(body),
        )
        webbrowser.open(mailto_url)
        self._status.setText('Bug report draft opened in your mail client')

    def action_support(self):
        webbrowser.open(
            'https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=D7H33JFSFA98J&lc=IL&item_name=David%20GUEZ&item_number=MALODOS&currency_code=ILS&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted'
        )
        self._status.setText('Support page opened in your browser')

    def _on_item_clicked(self, item):
        self.select_document(self._list.row(item))

    def _on_current_row_changed(self, row):
        self.select_document(row)

    def _on_folder_tree_selection_changed(self):
        if self._folder_tree is None:
            return
        selected_rows = []
        for item in self._folder_tree.selectedItems():
            row = item.data(0, Qt.ItemDataRole.UserRole if Qt is not None else 0)
            if row is not None:
                selected_rows.append(row)
        if selected_rows:
            self.select_document(selected_rows[0])

    def _on_tag_tree_selection_changed(self):
        if self._tag_tree is None:
            return
        selected_rows = []
        for item in self._tag_tree.selectedItems():
            row = item.data(0, Qt.ItemDataRole.UserRole if Qt is not None else 0)
            if row is not None:
                selected_rows.append(row)
        if selected_rows:
            self.select_document(selected_rows[0])

    def _on_basket_item_clicked(self, item):
        row = item.data(Qt.ItemDataRole.UserRole if Qt is not None else 0)
        if row is not None:
            self.select_document(row)

    def _document_id(self, row):
        if isinstance(row, dict):
            for key in ('id', 'rowid', 'doc_id'):
                if key in row and row[key] is not None:
                    return row[key]
            return None
        if isinstance(row, (list, tuple)):
            try:
                import database
                idx_rowid = getattr(database.theBase, 'IDX_ROWID', None)
                if idx_rowid is not None and idx_rowid < len(row):
                    return row[idx_rowid]
            except Exception:
                return None
        return None

    def _document_tags(self, row):
        raw = None
        if isinstance(row, dict):
            raw = row.get('tags')
        elif isinstance(row, (list, tuple)):
            try:
                import database
                idx_tags = getattr(database.theBase, 'IDX_TAGS', None)
                if idx_tags is not None and idx_tags < len(row):
                    raw = row[idx_tags]
            except Exception:
                raw = None
        text = _to_text(raw)
        if not text:
            return []
        return [part.strip() for part in text.split(',') if part.strip()]

    def _document_folder_paths(self, row):
        doc_id = self._document_id(row)
        if doc_id is None:
            return []
        try:
            import database
            folder_ids = database.theBase.folders_list_for(doc_id)
            paths = []
            for folder_id in folder_ids:
                genealogy = database.theBase.folders_genealogy_of(folder_id, True)
                if genealogy:
                    if isinstance(genealogy[0], str):
                        paths.append('/'.join(genealogy))
                    else:
                        names = [name for (_fid, name) in genealogy if name]
                        if names:
                            paths.append('/'.join(names))
            return paths
        except Exception:
            return []

    def _document_details(self, row):
        if isinstance(row, dict):
            title = row.get('title') or row.get('name') or row.get('filename') or 'Untitled'
            description = row.get('description') or 'No description available.'
            filename = row.get('filename') or row.get('path') or 'No file'
            return 'Title: %s\n\nDescription:\n%s\n\nFile: %s' % (_to_text(title), _to_text(description), _to_text(filename))
        if isinstance(row, (list, tuple)):
            try:
                import database
                idx_title = getattr(database.theBase, 'IDX_TITLE', None)
                idx_desc = getattr(database.theBase, 'IDX_DESCRIPTION', None)
                idx_filename = getattr(database.theBase, 'IDX_FILENAME', None)
                title = row[idx_title] if idx_title is not None and idx_title < len(row) else 'Untitled'
                description = row[idx_desc] if idx_desc is not None and idx_desc < len(row) else 'No description available.'
                filename = row[idx_filename] if idx_filename is not None and idx_filename < len(row) else 'No file'
                return 'Title: %s\n\nDescription:\n%s\n\nFile: %s' % (_to_text(title), _to_text(description), _to_text(filename))
            except Exception:
                pass
        return 'Selected document\n\n%s' % _to_text(row)

    def _document_filename(self, row):
        if isinstance(row, dict):
            for key in ('filename', 'path', 'file', 'document_path'):
                value = row.get(key)
                if value not in (None, ''):
                    return _to_text(value)
            return None
        if isinstance(row, (list, tuple)):
            try:
                import database
                idx_filename = getattr(database.theBase, 'IDX_FILENAME', None)
                if idx_filename is not None and idx_filename < len(row):
                    value = row[idx_filename]
                    if value not in (None, ''):
                        return _to_text(value)
            except Exception:
                pass
            return None
        if isinstance(row, str):
            return _to_text(row)
        return None

    def _resolve_document_path(self, filename):
        if not filename:
            return None
        normalized = str(filename).strip()
        if not normalized:
            return None

        expanded = os.path.expanduser(normalized)
        base_name = os.path.basename(expanded)
        candidates = []

        seen = set()

        def add_candidate(path):
            if not path:
                return
            norm = os.path.abspath(os.path.normpath(path))
            if norm not in seen:
                seen.add(norm)
                candidates.append(norm)

        add_candidate(expanded)
        add_candidate(os.path.abspath(expanded))
        add_candidate(os.path.join(os.getcwd(), expanded))

        for root in [
            os.path.expanduser('~'),
            '/home',
            '/mnt',
            '/media',
            '/tmp',
            os.getcwd(),
        ]:
            if root and os.path.isdir(root):
                add_candidate(os.path.join(root, base_name))

        search_roots = []
        try:
            import database
            config = getattr(database, 'theConfig', None)
            if config is not None:
                conf_dir = getattr(config, 'conf_dir', None)
                if conf_dir:
                    add_candidate(os.path.join(conf_dir, expanded))
                    add_candidate(os.path.join(conf_dir, base_name))
                    search_roots.append(conf_dir)
                doc_dir = getattr(config, 'documents_dir', None)
                if doc_dir:
                    add_candidate(os.path.join(doc_dir, expanded))
                    add_candidate(os.path.join(doc_dir, base_name))
                    search_roots.append(doc_dir)
                default_dir = getattr(config, 'defaultdir', None)
                if default_dir:
                    add_candidate(os.path.join(default_dir, expanded))
                    add_candidate(os.path.join(default_dir, base_name))
                    search_roots.append(default_dir)
                for section_name in ('survey', 'scanner'):
                    try:
                        section = config.get_all_params_in(section_name) if hasattr(config, 'get_all_params_in') else {}
                    except Exception:
                        section = {}
                    for key in ('directory_list', 'defaultdir', 'lastdir'):
                        value = section.get(key)
                        if not value:
                            continue
                        if isinstance(value, str):
                            for item in value.split('|'):
                                item = item.strip()
                                if item.startswith('*'):
                                    item = item[1:]
                                if item:
                                    item = os.path.expanduser(item)
                                    search_roots.append(item)
                                    add_candidate(os.path.join(item, base_name))
                                    add_candidate(os.path.join(item, expanded))
        except Exception:
            pass

        home_root = os.path.expanduser('~')
        for extra in (
            os.path.join(home_root, 'scans'),
            os.path.join(home_root, 'Documents'),
            os.path.join(home_root, '.malodos', 'documents'),
            '/home/david/scans',
            '/home/david/Documents',
            '/mnt',
            '/media',
        ):
            if extra and os.path.isdir(extra):
                search_roots.append(extra)

        if base_name:
            for root in list(dict.fromkeys(search_roots)):
                if not root or not os.path.isdir(root):
                    continue
                for current_root, _, files in os.walk(root):
                    if current_root.startswith('/proc') or current_root.startswith('/sys'):
                        continue
                    if base_name in files:
                        add_candidate(os.path.join(current_root, base_name))
                        break

        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate

        return expanded if os.path.exists(expanded) else None

    def _pixmap_from_pil(self, pil_image):
        if pil_image is None:
            return None
        if QImage is None or QPixmap is None:
            return None
        try:
            rgba = pil_image.convert('RGBA')
            image_data = rgba.tobytes('raw', 'RGBA')
            # Force a deep copy so Qt does not keep a dangling pointer to Python-owned bytes.
            qimage = QImage(image_data, rgba.width, rgba.height, rgba.width * 4, QImage.Format_RGBA8888).copy()
            return QPixmap.fromImage(qimage)
        except Exception:
            return None

    def _document_pixmap(self, filename):
        resolved = self._resolve_document_path(filename)
        if not resolved:
            return None
        if QPixmap is not None:
            pixmap = QPixmap(resolved)
            if pixmap is not None and not pixmap.isNull():
                return pixmap
        try:
            from PIL import Image as PILImage
            with PILImage.open(resolved) as pil_image:
                if getattr(pil_image, 'n_frames', 1) > 1:
                    pil_image.seek(0)
                pixmap = self._pixmap_from_pil(pil_image)
                if pixmap is not None and not pixmap.isNull():
                    return pixmap
        except Exception:
            pass
        try:
            if resolved.lower().endswith('.pdf'):
                import pypdfium2 as pdfium
                pdf = pdfium.PdfDocument(resolved)
                if len(pdf):
                    page = pdf[0]
                    bitmap = page.render(scale=1.0)
                    pil_image = bitmap.to_pil()
                    pixmap = self._pixmap_from_pil(pil_image)
                    if pixmap is not None and not pixmap.isNull():
                        return pixmap
        except Exception:
            pass
        return None

    def _set_document_image(self, row):
        if getattr(self, '_image', None) is None:
            return
        self._last_pixmap = None
        self._zoom = 1.0
        filename = self._document_filename(row)
        pixmap = self._document_pixmap(filename)
        if pixmap is None or pixmap.isNull():
            self._image.setText('No document image')
            self._image.setPixmap(QPixmap() if QPixmap is not None else None)
            return
        self._last_pixmap = pixmap
        self._apply_image_zoom()

    def _apply_image_zoom(self):
        if getattr(self, '_image', None) is None:
            return
        if self._last_pixmap is None:
            return
        base = self._last_pixmap
        try:
            width = max(1, int(base.width() * self._zoom))
            height = max(1, int(base.height() * self._zoom))
            scaled = base.scaled(
                width,
                height,
                Qt.AspectRatioMode.KeepAspectRatio if Qt is not None else 0,
                Qt.TransformationMode.SmoothTransformation if Qt is not None else 0,
            )
            self._image.setPixmap(scaled)
            self._image.resize(scaled.size())
            self._image.setText('')
        except Exception:
            pass

    def action_previous_page(self):
        if self.docList:
            row = self._list.currentRow() if hasattr(self, '_list') and self._list is not None else -1
            if row <= 0:
                row = len(self.docList) - 1
            else:
                row -= 1
            self._list.setCurrentRow(row)
            self.select_document(row)

    def action_next_page(self):
        if self.docList:
            row = self._list.currentRow() if hasattr(self, '_list') and self._list is not None else 0
            if row >= len(self.docList) - 1:
                row = 0
            else:
                row += 1
            self._list.setCurrentRow(row)
            self.select_document(row)

    def action_zoom_in(self):
        self._zoom = min(3.0, self._zoom + 0.25)
        self._apply_image_zoom()

    def action_zoom_out(self):
        self._zoom = max(0.25, self._zoom - 0.25)
        self._apply_image_zoom()

    def select_document(self, row):
        if not hasattr(self, '_list') or self._list is None:
            return None
        if isinstance(row, int):
            if row < 0 or row >= len(self.docList):
                self._details.setPlainText('Select a document to view details')
                self._set_document_image(None)
                return None
            selected = self.docList[row]
        else:
            selected = row
        if selected is None:
            self._details.setPlainText('Select a document to view details')
            self._set_document_image(None)
            return None
        self._details.setPlainText(self._document_details(selected))
        self._set_document_image(selected)
        return selected

    def set_documents(self, documents):
        self.docList = list(documents or [])
        if not hasattr(self, '_list'):
            return
        previous_signal_state = self._list.blockSignals(True)
        try:
            self._list.clear()
            if not self.docList:
                self._list.addItem(QListWidgetItem('No documents found'))
                self._status.setText('0 document(s)')
                self._details.setPlainText('No document selected')
                self._refresh_folder_tree()
                self._refresh_tag_tree()
                return
            for document in self.docList:
                item = QListWidgetItem(self._document_title(document))
                item.setData(Qt.ItemDataRole.UserRole if Qt is not None else 0, document)
                self._list.addItem(item)
        finally:
            self._list.blockSignals(previous_signal_state)
        self._status.setText('%d document(s)' % len(self.docList))
        self._refresh_folder_tree()
        self._refresh_tag_tree()
        self._refresh_basket_view()
        if self._list.count() > 0:
            self._details.setPlainText('Select a document to view details')
            self._set_document_image(None)

    def _refresh_folder_tree(self):
        if self._folder_tree is None:
            return
        self._folder_tree.blockSignals(True)
        try:
            self._folder_tree.clear()
            root = QTreeWidgetItem(['ROOT'])
            root.setData(0, Qt.ItemDataRole.UserRole if Qt is not None else 0, None)
            self._folder_tree.addTopLevelItem(root)

            unclassified = QTreeWidgetItem(['Unclassified'])
            unclassified.setData(0, Qt.ItemDataRole.UserRole if Qt is not None else 0, None)
            root.addChild(unclassified)

            folder_nodes = {}
            for row in self.docList:
                title = self._document_title(row)
                folder_paths = self._document_folder_paths(row)
                if not folder_paths:
                    doc_item = QTreeWidgetItem([title])
                    doc_item.setData(0, Qt.ItemDataRole.UserRole if Qt is not None else 0, row)
                    unclassified.addChild(doc_item)
                    continue
                for path in folder_paths:
                    parent = root
                    current_path = []
                    for part in [p for p in path.split('/') if p]:
                        current_path.append(part)
                        key = '/'.join(current_path)
                        node = folder_nodes.get(key)
                        if node is None:
                            node = QTreeWidgetItem([part])
                            node.setData(0, Qt.ItemDataRole.UserRole if Qt is not None else 0, None)
                            parent.addChild(node)
                            folder_nodes[key] = node
                        parent = node
                    doc_item = QTreeWidgetItem([title])
                    doc_item.setData(0, Qt.ItemDataRole.UserRole if Qt is not None else 0, row)
                    parent.addChild(doc_item)
            self._folder_tree.expandAll()
        finally:
            self._folder_tree.blockSignals(False)

    def _refresh_tag_tree(self):
        if self._tag_tree is None:
            return
        self._tag_tree.blockSignals(True)
        try:
            self._tag_tree.clear()
            root = QTreeWidgetItem(['ROOT'])
            root.setData(0, Qt.ItemDataRole.UserRole if Qt is not None else 0, None)
            self._tag_tree.addTopLevelItem(root)

            tagged_rows = []
            untagged = []
            for row in self.docList:
                if self._document_tags(row):
                    tagged_rows.append(row)
                else:
                    untagged.append(row)

            self._fill_tag_tree_recursive(root, tagged_rows, set())

            if untagged:
                untagged_item = QTreeWidgetItem(['Untagged'])
                untagged_item.setData(0, Qt.ItemDataRole.UserRole if Qt is not None else 0, None)
                root.addChild(untagged_item)
                for row in untagged:
                    doc_item = QTreeWidgetItem([self._document_title(row)])
                    doc_item.setData(0, Qt.ItemDataRole.UserRole if Qt is not None else 0, row)
                    untagged_item.addChild(doc_item)

            self._tag_tree.expandAll()
        finally:
            self._tag_tree.blockSignals(False)

    def _fill_tag_tree_recursive(self, parent_item, rows, refused_tags):
        if not rows:
            return

        tag_freq = {}
        for row in rows:
            for tag in self._document_tags(row):
                key = tag.lower()
                if key in refused_tags:
                    continue
                bucket = tag_freq.setdefault(key, {'label': tag, 'count': 0})
                bucket['count'] += 1

        if not tag_freq:
            for row in rows:
                doc_item = QTreeWidgetItem([self._document_title(row)])
                doc_item.setData(0, Qt.ItemDataRole.UserRole if Qt is not None else 0, row)
                parent_item.addChild(doc_item)
            return

        # Mimic legacy behavior: only split into subgroups when a tag is frequent enough.
        top_key, top_info = max(tag_freq.items(), key=lambda kv: kv[1]['count'])
        if top_info['count'] <= 5:
            for row in rows:
                doc_item = QTreeWidgetItem([self._document_title(row)])
                doc_item.setData(0, Qt.ItemDataRole.UserRole if Qt is not None else 0, row)
                parent_item.addChild(doc_item)
            return

        grouped = []
        remaining = []
        for row in rows:
            row_tags = {t.lower() for t in self._document_tags(row)}
            if top_key in row_tags:
                grouped.append(row)
            else:
                remaining.append(row)

        group_item = QTreeWidgetItem([top_info['label']])
        group_item.setData(0, Qt.ItemDataRole.UserRole if Qt is not None else 0, None)
        parent_item.addChild(group_item)

        self._fill_tag_tree_recursive(group_item, grouped, refused_tags | {top_key})
        self._fill_tag_tree_recursive(parent_item, remaining, refused_tags)

    def _basket_add_rows(self, rows):
        if not rows:
            return
        existing = {self._document_id(row) for row in self.basket}
        for row in rows:
            doc_id = self._document_id(row)
            if doc_id is not None and doc_id in existing:
                continue
            if doc_id is not None:
                existing.add(doc_id)
            self.basket.append(row)
        self._refresh_basket_view()

    def _basket_remove_rows(self, rows):
        if not rows:
            return
        remove_ids = {self._document_id(row) for row in rows}
        new_basket = []
        for row in self.basket:
            doc_id = self._document_id(row)
            if doc_id in remove_ids:
                continue
            new_basket.append(row)
        self.basket = new_basket
        self._refresh_basket_view()

    def _refresh_basket_view(self):
        self._basket_list.blockSignals(True)
        try:
            self._basket_list.clear()
            for row in self.basket:
                item = QListWidgetItem(self._document_title(row))
                item.setData(Qt.ItemDataRole.UserRole if Qt is not None else 0, row)
                self._basket_list.addItem(item)
        finally:
            self._basket_list.blockSignals(False)

    def get_selected_rows(self):
        rows = []
        active_tab = self._left_tabs.currentIndex() if self._left_tabs is not None else 0
        if active_tab == 0:
            for item in self._list.selectedItems():
                row = item.data(Qt.ItemDataRole.UserRole if Qt is not None else 0)
                if row is not None:
                    rows.append(row)
        elif active_tab == 1 and self._folder_tree is not None:
            for item in self._folder_tree.selectedItems():
                row = item.data(0, Qt.ItemDataRole.UserRole if Qt is not None else 0)
                if row is not None:
                    rows.append(row)
        elif active_tab == 2 and self._tag_tree is not None:
            for item in self._tag_tree.selectedItems():
                row = item.data(0, Qt.ItemDataRole.UserRole if Qt is not None else 0)
                if row is not None:
                    rows.append(row)
        elif active_tab == 3:
            for item in self._basket_list.selectedItems():
                row = item.data(Qt.ItemDataRole.UserRole if Qt is not None else 0)
                if row is not None:
                    rows.append(row)
        return rows


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

    def set_frame(self, frame):
        self.frame = frame
        if frame is not None:
            setattr(frame, 'controller', self.controller)
        return self

    def initialize(self):
        if self._is_initialized:
            return self.frame
        if self.frame is None:
            if QMainWindow is not None:
                self.frame = QtMainWindow(self.title)
            else:
                self.frame = _SimpleFrame(self.title)
        if hasattr(self.frame, 'initialize'):
            self.frame.initialize()
        if self.controller is not None:
            setattr(self.frame, 'controller', self.controller)
        self._is_initialized = True
        return self.frame

    def show(self):
        frame = self.initialize()
        if hasattr(frame, 'Show'):
            frame.Show(True)
        elif hasattr(frame, 'show'):
            frame.show()
        return frame

    def display_documents(self, documents):
        self.docList = list(documents or [])
        frame = self.frame
        if frame is None:
            self.initialize()
            frame = self.frame
        if hasattr(frame, 'set_documents'):
            frame.set_documents(self.docList)
        elif hasattr(frame, 'docList'):
            frame.docList = self.docList
        return self.docList
