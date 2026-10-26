from imagekit.cachefiles.strategies import Optimistic


class SafeOptimistic(Optimistic):
    """Optimistic strategy that skips generation when the source file is
    missing on disk (e.g. media not synced), instead of raising FileNotFoundError."""

    @staticmethod
    def _source_exists(file):
        source = getattr(file.generator, 'source', None)
        if not source:
            return False
        try:
            return source.storage.exists(source.name)
        except Exception:
            return False

    def on_source_saved(self, file):
        if self._source_exists(file):
            super().on_source_saved(file)

    def on_existence_required(self, file):
        if self._source_exists(file):
            super().on_existence_required(file)
