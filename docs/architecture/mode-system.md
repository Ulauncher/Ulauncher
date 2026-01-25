# Mode System

Ulauncher's query handling uses a mode-based architecture. Each mode handles specific types of queries.

## BaseMode Interface

Located in `ulauncher/modes/base_mode.py`. Key methods:

- **`matches_query_str(query)`** - Return True if this mode should handle the query
- **`handle_query(query, callback)`** - Process query and call callback with results
- **`activate_result(result)`** - Handle user selecting a result (perform action or return new results)
- **`get_triggers()`** - Return trigger keywords/shortcuts for this mode
- **`get_fallback_results()`** - Provide results when no specific matches found

## Flow

1. User types → `UlauncherCore` iterates through modes
2. First mode where `matches_query_str()` returns True handles the query
3. That mode's `handle_query()` generates results
4. User selects result → `activate_result()` performs action

## When to Create a New Mode

Create a mode when adding a new query handler type:

- New special command syntax (like `!` for calculator)
- New keyword-triggered feature (like file browser)
- New fallback result provider

## Examples

See existing modes in `ulauncher/modes/`:

- `apps/` - Application launcher
- `calc/` - Calculator mode
- `file_browser/` - File navigation
- `extensions/` - Extension query handling
