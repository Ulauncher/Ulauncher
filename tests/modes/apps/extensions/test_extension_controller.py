import pytest
from pytest_mock import MockerFixture

from ulauncher.modes.extensions.extension_controller import ExtensionController, supervisor


@pytest.fixture(autouse=True)
def unclaimed_supervisor(mocker: MockerFixture) -> None:
    mocker.patch.object(supervisor, "is_owner", False)


def test_start__raises_when_process_does_not_own_extension_runtimes() -> None:
    controller = ExtensionController("test.guard", "/nonexistent")
    with pytest.raises(RuntimeError):
        controller.start()


def test_send_message__raises_when_process_does_not_own_extension_runtimes() -> None:
    controller = ExtensionController("test.guard", "/nonexistent")
    with pytest.raises(RuntimeError):
        controller.send_message({"type": "event:unload"})
