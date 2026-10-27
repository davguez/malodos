import unittest


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


if __name__ == '__main__':
    unittest.main()
