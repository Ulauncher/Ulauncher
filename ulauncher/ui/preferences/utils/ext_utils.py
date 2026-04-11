from __future__ import annotations

import html
import re
from typing import Literal

from ulauncher.modes.extensions.extension_controller import ExtensionController

ExtStatus = Literal["on", "off", "error", "stopped", "preview"]


def fmt_pango_code_block(text: str) -> str:
    """Format text as an inline code block with Pango markup (monospace font with background)."""
    return f'<span face="monospace" bgcolor="#90600050">{html.escape(text)}</span>'


_CODE_TAG_RE = re.compile(r"<code(?:\s+[^>]*)?>(.*?)</code>", flags=re.IGNORECASE | re.DOTALL)


def autofmt_pango_code_block(text: str) -> str:
    """Convert HTML <code> tags to Pango-formatted inline code blocks."""
    if "<code" not in text:
        return text

    def repl(match: re.Match[str]) -> str:
        code_text = html.unescape(match.group(1))
        return fmt_pango_code_block(code_text)

    return _CODE_TAG_RE.sub(repl, text)


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
            f"{fmt_pango_code_block(f'pip3 install {module_name} --user')}\n\n"
            f"Then restart Ulauncher."
        )
        if ext_url:
            message += (
                f"\n\n<small>If that doesn't help, report the issue: "
                f'<a href="{ext_url}/issues">{ext_url}/issues</a></small>'
            )
        return message

    message = error_message or f"Unknown error type: {error_type}"
    if ext_url and error_type != "MissingModule":
        message += "\n\n<small>You can let the author know about this problem by creating an issue: "
        message += f'<a href="{ext_url}/issues">{ext_url}/issues</a></small>'
    return message
