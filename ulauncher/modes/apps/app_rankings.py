"""
Ranks apps by a recency-weighted launch score so that recently-used apps
surface above apps that were once popular but are no longer being opened.
"""

from __future__ import annotations

from ulauncher import paths
from ulauncher.data import JsonKeyValueConf

APP_RANKINGS_PATH = f"{paths.STATE}/app_rankings.json"
# Controls decay aggressiveness. The new app needs N*(2^(1/(DECAY_RATE+1))-1) launches
# to overtake an old app with N total history - about 19% of history at DECAY_RATE=3.
# Higher values make old habits fade faster; lower values make rankings more stable.
DECAY_RATE = 3


class AppRankings(JsonKeyValueConf[str, float]):
    """
    Each app has a float score. Launching an app gives it +1 and slightly
    reduces every other app's score. This means an app you stop using will
    gradually fall behind the ones you keep opening, even if it had a long
    head start.

    The amount of decay per launch adapts to how much history exists: the
    more launches in total, the smaller the decay per launch. A new favourite
    app doesn't need to match the old one's full history to overtake it -
    it only needs to be opened consistently while the old one goes unused.
    The total launch count is recovered from the sum of all scores, so no
    separate counter is needed.
    """

    _ranking_cache: list[str] | None = None

    def _total_launches(self) -> int:
        return max(0, round((DECAY_RATE + 1) * sum(self.values()) - DECAY_RATE))

    def get_app_ids(self) -> list[str]:
        if self._ranking_cache is None:
            self._ranking_cache = sorted(self, key=self.__getitem__, reverse=True)
        return self._ranking_cache

    def bump(self, app_id: str) -> None:
        n = self._total_launches()
        decay = n / (n + DECAY_RATE)
        for k in list(self):
            self[k] *= decay
        self[app_id] = self.get(app_id, 0) + 1.0
        self._ranking_cache = None
        self.save()

    @classmethod
    def load(cls) -> AppRankings:  # type: ignore[override]
        return super().load(APP_RANKINGS_PATH)
