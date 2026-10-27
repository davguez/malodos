import unittest
import sys


class MvcArchitectureTest(unittest.TestCase):
    def test_mvc_packages_exist(self):
        import mvc
        from mvc.models import DocumentModel
        from mvc.views import MainView
        from mvc.controllers import MainController

        self.assertTrue(hasattr(mvc, '__package__'))
        self.assertTrue(callable(DocumentModel))
        self.assertTrue(callable(MainView))
        self.assertTrue(callable(MainController))

    def test_main_controller_holds_view_and_model(self):
        from mvc.controllers import MainController

        controller = MainController()

        self.assertIsNotNone(controller.model)
        self.assertIsNotNone(controller.view)

    def test_main_view_renders_document_list(self):
        from mvc.views import MainView

        view = MainView()
        view.initialize()
        frame = view.frame

        self.assertIsNotNone(frame)
        self.assertTrue(hasattr(frame, 'set_documents'))
        frame.set_documents([{'title': 'Alpha'}, {'title': 'Beta'}])
        self.assertEqual(frame.docList[0]['title'], 'Alpha')
        self.assertEqual(frame._list.count(), 2)

    def test_main_view_updates_details_when_document_selected(self):
        from mvc.views import MainView

        view = MainView()
        view.initialize()
        frame = view.frame
        frame.set_documents([
            {'title': 'Alpha', 'description': 'First doc', 'filename': 'alpha.pdf'},
            {'title': 'Beta', 'description': 'Second doc', 'filename': 'beta.pdf'},
        ])

        frame.select_document(1)

        self.assertIn('Beta', frame._details.toPlainText())
        self.assertIn('Second doc', frame._details.toPlainText())

    def test_main_view_display_document_image_preview_when_available(self):
        import os
        import tempfile
        from PIL import Image
        from mvc.views import MainView

        view = MainView()
        view.initialize()
        frame = view.frame

        fd, filepath = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        Image.new('RGB', (20, 20), color='blue').save(filepath)

        try:
            frame.set_documents([
                {'title': 'Preview Doc', 'description': 'Has picture', 'filename': filepath},
            ])
            frame.select_document(0)
            self.assertFalse(frame._image.text())
            self.assertIsNotNone(frame._image.pixmap())
            self.assertFalse(frame._image.pixmap().isNull())
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_pdf_preview_does_not_import_wx_modules(self):
        import os
        import tempfile
        from PIL import Image
        from mvc.views import MainView

        view = MainView()
        view.initialize()
        frame = view.frame

        fd, filepath = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        Image.new('RGB', (64, 64), color='white').save(filepath, 'PDF')

        wx_modules_before = {name for name in sys.modules if name == 'wx' or name.startswith('wx.')}
        try:
            frame.set_documents([
                {'title': 'PDF Preview', 'description': 'pdf test', 'filename': filepath},
            ])
            frame.select_document(0)
            wx_modules_after = {name for name in sys.modules if name == 'wx' or name.startswith('wx.')}
            self.assertEqual(wx_modules_before, wx_modules_after)
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_main_view_resolves_relative_document_paths_for_preview(self):
        import os
        import sys
        import tempfile
        import types
        from PIL import Image
        from mvc.views import MainView

        view = MainView()
        view.initialize()
        frame = view.frame

        config_dir = tempfile.mkdtemp(prefix='malodos-config-')
        saved_module = sys.modules.get('database')
        stub_database = types.SimpleNamespace(theConfig=types.SimpleNamespace(conf_dir=config_dir))
        sys.modules['database'] = stub_database

        filepath = os.path.join(config_dir, 'nested', 'preview.png')
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        Image.new('RGB', (30, 30), color='green').save(filepath)

        try:
            relative_path = os.path.relpath(filepath, start=config_dir)
            frame.set_documents([
                {'title': 'Relative Preview', 'description': 'Uses a relative path', 'filename': relative_path},
            ])
            frame.select_document(0)
            self.assertFalse(frame._image.text())
            self.assertIsNotNone(frame._image.pixmap())
            self.assertFalse(frame._image.pixmap().isNull())
        finally:
            if saved_module is None:
                sys.modules.pop('database', None)
            else:
                sys.modules['database'] = saved_module
            if os.path.exists(filepath):
                os.remove(filepath)
            if os.path.exists(os.path.dirname(filepath)):
                os.rmdir(os.path.dirname(filepath))
            if os.path.exists(config_dir):
                os.rmdir(config_dir)

    def test_main_view_decodes_bytes_in_document_fields(self):
        from mvc.views import MainView

        view = MainView()
        view.initialize()
        frame = view.frame

        frame.set_documents([
            {'title': b'Alpha', 'description': b'First doc', 'filename': b'alpha.pdf'},
        ])
        frame.select_document(0)

        self.assertIn('Alpha', frame._details.toPlainText())
        self.assertNotIn("b'Alpha'", frame._details.toPlainText())
        self.assertNotIn("b'alpha.pdf'", frame._details.toPlainText())

    def test_main_view_resolves_legacy_windows_paths_to_current_files(self):
        import os
        import tempfile
        from PIL import Image
        from mvc.views import MainView

        view = MainView()
        view.initialize()
        frame = view.frame

        base_dir = tempfile.mkdtemp(prefix='malodos-legacy-')
        moved_path = os.path.join(base_dir, 'documents', 'lettre_cours_conduite.pdf')
        os.makedirs(os.path.dirname(moved_path), exist_ok=True)
        Image.new('RGB', (20, 20), color='purple').save(moved_path)

        try:
            resolved = frame._resolve_document_path('/mnt/win2/scans/lettre_cours_conduite.pdf')
            self.assertIsNotNone(resolved)
            self.assertTrue(os.path.exists(resolved))
            self.assertEqual(os.path.basename(resolved), 'lettre_cours_conduite.pdf')
        finally:
            if os.path.exists(moved_path):
                os.remove(moved_path)
            if os.path.exists(os.path.dirname(moved_path)):
                os.rmdir(os.path.dirname(moved_path))
            if os.path.exists(base_dir):
                os.rmdir(base_dir)

    def test_main_view_exposes_legacy_preview_toolbar(self):
        from mvc.views import MainView

        view = MainView()
        view.initialize()
        frame = view.frame

        self.assertTrue(hasattr(frame, '_toolbar'))
        self.assertTrue(hasattr(frame, 'action_previous_page'))
        self.assertTrue(hasattr(frame, 'action_next_page'))
        self.assertTrue(hasattr(frame, 'action_zoom_in'))
        self.assertTrue(hasattr(frame, 'action_zoom_out'))

    def test_main_view_uses_splitters_for_three_panes(self):
        from mvc.views import MainView

        view = MainView()
        view.initialize()
        frame = view.frame

        self.assertTrue(hasattr(frame, '_main_splitter'))
        self.assertTrue(hasattr(frame, '_right_splitter'))
        self.assertIsNotNone(frame._main_splitter)
        self.assertIsNotNone(frame._right_splitter)
        self.assertEqual(frame._main_splitter.count(), 2)
        self.assertEqual(frame._right_splitter.count(), 2)

    def test_select_document_does_not_resize_main_window(self):
        import os
        import tempfile
        from PIL import Image
        from mvc.views import MainView

        view = MainView()
        view.initialize()
        frame = view.frame

        fd, filepath = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        Image.new('RGB', (2400, 1600), color='red').save(filepath)

        try:
            frame.resize(900, 600)
            before = frame.size()
            frame.set_documents([
                {'title': 'Large Preview', 'description': 'big image', 'filename': filepath},
            ])
            frame.select_document(0)
            after = frame.size()
            self.assertEqual(before.width(), after.width())
            self.assertEqual(before.height(), after.height())
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_main_view_exposes_legacy_main_toolbar(self):
        from mvc.views import MainView

        view = MainView()
        view.initialize()
        frame = view.frame

        self.assertTrue(hasattr(frame, '_main_toolbar'))
        self.assertIsNotNone(frame._main_toolbar)
        self.assertGreaterEqual(len(frame._main_toolbar.actions()), 11)

    def test_preview_toolbar_is_attached_to_preview_widget(self):
        from mvc.views import MainView

        view = MainView()
        view.initialize()
        frame = view.frame

        self.assertIsNotNone(frame._toolbar)
        self.assertTrue(frame._toolbar.parent() is frame._preview_panel)

        parent = frame._toolbar.parent()
        found_viewer = False
        seen = set()
        while parent is not None and id(parent) not in seen:
            seen.add(id(parent))
            if parent is frame._viewer:
                found_viewer = True
                break
            parent = parent.parent()
        self.assertTrue(found_viewer)

    def test_preview_toolbar_actions_have_icons_when_available(self):
        from mvc.views import MainView

        view = MainView()
        view.initialize()
        frame = view.frame

        action_icons = [action.icon() for action in frame._toolbar.actions() if action.text()]
        self.assertTrue(any(icon is not None and not icon.isNull() for icon in action_icons))

    def test_display_documents_does_not_reenter_search_action(self):
        from mvc.views import MainView

        view = MainView()
        view.initialize()
        frame = view.frame

        frame._search.setText('alpha')
        frame.actionSearch = lambda _event: (_ for _ in ()).throw(RuntimeError('recursive search'))

        try:
            view.display_documents([{'title': 'Alpha'}])
        except RuntimeError:
            self.fail('display_documents should not re-trigger actionSearch recursively')

    def test_typing_in_search_triggers_live_search(self):
        from mvc.views import MainView

        class _ControllerStub(object):
            def __init__(self):
                self.queries = []

            def search(self, query):
                self.queries.append(query)

        view = MainView()
        view.initialize()
        frame = view.frame
        controller = _ControllerStub()
        frame.controller = controller

        frame._search.setText('abc')

        self.assertTrue(controller.queries)
        self.assertEqual(controller.queries[-1], 'abc')

    def test_root_mvc_package_exports_app_module(self):
        import importlib
        import mvc

        app_module = importlib.import_module('mvc.app')
        self.assertTrue(hasattr(app_module, 'MALODOSApp'))
        self.assertTrue(hasattr(mvc, 'MALODOSApp'))


if __name__ == '__main__':
    unittest.main()
