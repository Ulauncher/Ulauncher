import os
import pytest
from ulauncher.utils.Theme import Theme, ThemeManifestError


class TestTheme:

    @pytest.fixture
    def theme(self, tmpdir):
        th = Theme(str(tmpdir))
        with open(os.path.join(str(tmpdir), 'theme.css'), 'w') as f:
            f.write('')

        th._data = {
            "manifest_version": "1",
            "name": "light",
            "display_name": "Elementary Light",
            "extend_theme": None,
            "css_file": "theme.css",
            "css_file_gtk_3.20+": "theme.css",
            "matched_text_hl_colors": {
                "when_selected": "#2c74cc",
                "when_not_selected": "#2c74cc"
            }
        }
        return th

    def test_validate__not_raises_on_valid_manifest(self, theme):
        theme.validate()

    def test_validate__raises_on_invalid_manifest_version(self, theme):
        theme._data['manifest_version'] = 3
        with pytest.raises(ThemeManifestError):
            theme.validate()

    def test_validate__raises_when_css_file_doesnt_exist(self, theme):
        theme._data['css_file_gtk_3.20+'] = 'css_file_gtk_3.20.css'
        with pytest.raises(ThemeManifestError):
            theme.validate()
