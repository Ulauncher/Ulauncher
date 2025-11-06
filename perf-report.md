## Hotkey Toggle Performance Findings

- Rendering the initial search results dominates the UI idle phase, with `results:render[3]` taking roughly 60 ms on lower-spec hardware (`ulauncher/ui/windows/ulauncher_window.py:474`). Recycling or lazily instantiating result widgets should reduce this stall.
- `core:load_triggers:AppMode` accounts for about 65 ms because it loads 144 desktop entries each toggle (`ulauncher/core.py:121`). App trigger discovery needs caching or incremental loading to shrink the first-toggle latency.
- Other stages, including GTK window bring-up and non-App modes, stay within a few milliseconds, so the bottlenecks are isolated to result rendering and AppMode trigger loading.


# My Conclusion

- `AppMode.get_triggers` is the primary culprit for the toggle delay due to loading many desktop entries.