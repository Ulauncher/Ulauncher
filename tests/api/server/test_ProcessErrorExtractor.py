import io

from ulauncher.api.server.ProcessErrorExtractor import ProcessErrorExtractor


class TestProcessErrorExtractor:

    def test_extract_from_file_object(self):
        string = "line 1\nline2\nModuleNotFoundError: No module named 'mymodule'"
        e = ProcessErrorExtractor.extract_from_file_object(io.StringIO(string))
        assert e.error == "ModuleNotFoundError: No module named 'mymodule'"

    def test_is_import_error__true(self):
        e = ProcessErrorExtractor("ModuleNotFoundError: No module named 'mymodule'")
        assert e.is_import_error()

    def test_is_import_error__false(self):
        e = ProcessErrorExtractor("KeyError: abc")
        assert not e.is_import_error()

    def test_get_missing_package_name__returns_name(self):
        e = ProcessErrorExtractor("ModuleNotFoundError: No module named 'mymodule'")
        assert e.get_missing_package_name() == 'mymodule'
