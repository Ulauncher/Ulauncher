from __future__ import annotations

from typing import Literal

from ulauncher.modes.extensions.extension_controller import ExtensionController

ExtStatus = Literal["on", "off", "error", "stopped", "preview"]


def get_status_str(ext: ExtensionController) -> ExtStatus:
    if ext.has_error:
        return "error"
    if not ext.is_enabled:
        return "off"
    if not ext.is_running:
        return "stopped"
    if ext.is_preview:
        return "preview"
    return "on"


def get_error_message(error_type: str, error_message: str, ext: ExtensionController) -> str:
    """Generate appropriate error message based on error type"""
    ext_url = ext.state.url

    if error_type == "Invalid":
        return (
            "The extension has an invalid manifest. Please report this issue to the extension "
            "developer, and attach the logs for details."
        )

    if error_type == "Terminated":
        message = (
            "The extension crashed. Ensure that you read and followed the instructions on the "
            "extension repository page, and check the error log and report the error otherwise."
        )
        if ext_url:
            message += f'\n\n<small>Repository: <a href="{ext_url}">{ext_url}</a></small>'
        return message

    if error_type == "Incompatible":
        return "The extension is not compatible with this version of Ulauncher."

    if error_type == "MissingInternals":
        return (
            "The extension is trying to import internal Ulauncher application methods which are not "
            "part of the extension API. This is not supported and it can break the extension any time "
            "Ulauncher changes, moves or removes internal code. Please report this issue to the "
            "extension developer."
        )

    if error_type == "MissingModule":
        module_name = error_message
        message = (
            f"The extension crashed because it could not import module <b>{module_name}</b>.\n\n"
            f"Try installing this module manually:\n"
            f'<span face="monospace" bgcolor="#00000030">pip3 install {module_name} --user</span>\n\n'
            f"Then restart Ulauncher."
        )
        if ext_url:
            message += (
                f"\n\n<small>If that doesn't help, report the issue: "
                f'<a href="{ext_url}/issues">{ext_url}/issues</a></small>'
            )
        return message

    message = error_message or f"Unknown error type: {error_type}"
    if ext_url and error_type not in ["MissingModule"]:
        message += "\n\n<small>You can let the author know about this problem by creating an issue: "
        message += f'<a href="{ext_url}/issues">{ext_url}/issues</a></small>'
    return message
