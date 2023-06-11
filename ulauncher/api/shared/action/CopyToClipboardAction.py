def CopyToClipboardAction(text: str):
    return {"type": "action:clipboard_store", "data": text}
