import logging
import os
from unittest.mock import patch

from pytest_mock import MockerFixture

from ulauncher.api.extension import Extension


class TestExtension:
    def test_init__verbose_env_controls_log_level(self, mocker: MockerFixture) -> None:
        mocker.patch("ulauncher.api.extension.Client")
        basic_config = mocker.patch("ulauncher.api.extension.logging.basicConfig")
        mocker.patch("ulauncher.api.extension.signal.signal")

        with patch.dict(os.environ, {"ULAUNCHER_EXTENSION_ID": "com.example.test", "VERBOSE": "0"}):
            Extension()

        assert basic_config.call_args_list[0].kwargs["level"] == logging.WARNING

        basic_config.reset_mock()

        with patch.dict(os.environ, {"ULAUNCHER_EXTENSION_ID": "com.example.test", "VERBOSE": "1"}):
            Extension()

        assert basic_config.call_args_list[0].kwargs["level"] == logging.DEBUG
