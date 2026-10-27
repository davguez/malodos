import ast
import configparser
import os

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

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QAction, QIcon, QImage, QPixmap
    from PySide6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QPushButton,
        QScrollArea,
        QSplitter,
        QSizePolicy,
        QTextBrowser,
        QToolBar,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover - optional in non-GUI test runs
    QAction = QToolBar = QApplication = QHBoxLayout = QLabel = QLineEdit = QListWidget = QListWidgetItem = QMainWindow = QPushButton = QTextBrowser = QVBoxLayout = QWidget = None
    QScrollArea = QSplitter = QSizePolicy = None
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
        self.controller = None
        self._search_in_progress = False

        self._viewer = QWidget(self)
        self._preview_panel = QWidget(self._viewer)
        self._viewer_layout = QVBoxLayout(self._viewer)
        self._viewer_layout.setContentsMargins(0, 0, 0, 0)

        self._main_toolbar = self._build_main_toolbar()

        self._search, self._search_button, self._search_bar = self._build_search_bar()
        self._list = QListWidget(self._viewer)
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.currentRowChanged.connect(self._on_current_row_changed)

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
            self._main_splitter.addWidget(self._list)
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
            content_layout.addWidget(self._list, 1)
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

        bar = QWidget(self._viewer)
        layout = QHBoxLayout(bar)
        layout.addWidget(search)
        layout.addWidget(search_button)
        return search, search_button, bar

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
        self._dispatch_controller_action('actionAddFile', 'add_file')

    def action_add_scan(self):
        self._dispatch_controller_action('actionAddScan', 'add_scan')

    def action_remove_selection(self):
        self._dispatch_controller_action('actionRemoveRecord', 'remove_selection')

    def action_print_document(self):
        self._dispatch_controller_action('actionDoPrint', 'print_document')

    def action_basket(self):
        self._dispatch_controller_action('actionBasket', 'open_basket')

    def action_doc_to_go(self):
        self._dispatch_controller_action('actionDocToGo', 'doc_to_go')

    def action_start_survey(self):
        self._dispatch_controller_action('actionStartSurvey', 'start_survey')

    def action_show_preferences(self):
        self._dispatch_controller_action('actionShowPrefs', 'show_preferences')

    def action_about(self):
        self._dispatch_controller_action('actionAbout', 'show_about')

    def action_report(self):
        self._dispatch_controller_action('actionReport', 'report_bug')

    def action_support(self):
        self._dispatch_controller_action('actionSupport', 'show_support')

    def _on_item_clicked(self, item):
        self.select_document(self._list.row(item))

    def _on_current_row_changed(self, row):
        self.select_document(row)

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
                return
            for document in self.docList:
                item = QListWidgetItem(self._document_title(document))
                item.setData(Qt.ItemDataRole.UserRole if Qt is not None else 0, document)
                self._list.addItem(item)
        finally:
            self._list.blockSignals(previous_signal_state)
        self._status.setText('%d document(s)' % len(self.docList))
        if self._list.count() > 0:
            self._details.setPlainText('Select a document to view details')
            self._set_document_image(None)


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
