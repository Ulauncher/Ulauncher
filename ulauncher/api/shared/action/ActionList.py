def ActionList(actions: list):  # type: ignore[no-untyped-def]
    return {"type": "action:legacy_run_many", "data": actions}
