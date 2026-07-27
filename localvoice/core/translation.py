from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import stat
import zipfile
from typing import Callable

from .validation import normalize_language


class TranslationMissingError(RuntimeError):
    pass


@dataclass(slots=True)
class TranslationPair:
    source: str
    target: str
    installed: bool


class LocalTranslator:
    """Offline translation through explicitly installed Argos Translate packages."""

    MAX_TEXT_LENGTH = 500_000
    MAX_PACKAGE_BYTES = 2 * 1024 * 1024 * 1024
    MAX_PACKAGE_FILES = 10_000
    MAX_UNCOMPRESSED_BYTES = 8 * 1024 * 1024 * 1024

    @staticmethod
    def _installed_languages():
        from argostranslate import translate
        return translate.get_installed_languages()

    def installed_pairs(self) -> list[TranslationPair]:
        pairs: list[TranslationPair] = []
        for language in self._installed_languages():
            for translation in language.translations_from:
                pairs.append(TranslationPair(language.code, translation.to_lang.code, True))
        return sorted(pairs, key=lambda item: (item.source, item.target))

    def _graph(self) -> dict[str, list[tuple[str, object]]]:
        graph: dict[str, list[tuple[str, object]]] = {}
        for language in self._installed_languages():
            for translation in language.translations_from:
                graph.setdefault(language.code, []).append((translation.to_lang.code, translation))
        return graph

    def find_route(self, source: str, target: str, preferred_intermediate: str = "en") -> list[object]:
        source = normalize_language(source, allow_auto=False, default="")
        target = normalize_language(target, allow_auto=False, default="")
        preferred_intermediate = normalize_language(preferred_intermediate, allow_auto=False, default="en")
        if not source or not target:
            return []
        if source == target:
            return []
        graph = self._graph()
        # Prefer a direct model, then an explicitly selected bridge language.
        for destination, translation in graph.get(source, []):
            if destination == target:
                return [translation]
        if source != preferred_intermediate and target != preferred_intermediate:
            first = next((item for destination, item in graph.get(source, []) if destination == preferred_intermediate), None)
            second = next((item for destination, item in graph.get(preferred_intermediate, []) if destination == target), None)
            if first is not None and second is not None:
                return [first, second]
        # Fall back to the shortest installed route, capped to avoid poor multi-hop chains.
        queue = deque([(source, [])])
        visited = {source}
        while queue:
            current, route = queue.popleft()
            if len(route) >= 3:
                continue
            for destination, translation in graph.get(current, []):
                if destination in visited:
                    continue
                next_route = route + [translation]
                if destination == target:
                    return next_route
                visited.add(destination)
                queue.append((destination, next_route))
        return []

    def can_translate(self, source: str, target: str, preferred_intermediate: str = "en") -> bool:
        return source == target or bool(self.find_route(source, target, preferred_intermediate))

    def translate(self, text: str, source: str, target: str, preferred_intermediate: str = "en") -> str:
        if not text or source == target:
            return text
        if len(text) > self.MAX_TEXT_LENGTH:
            raise RuntimeError("Text is too large for a single local translation job.")
        route = self.find_route(source, target, preferred_intermediate)
        if not route:
            raise TranslationMissingError(f"TRANSLATION_MODEL_MISSING:{source}:{target}")
        result = text
        for translation in route:
            result = translation.translate(result)
        return result

    @staticmethod
    def _validate_download(path_value: object) -> Path:
        path = Path(str(path_value)).resolve()
        if not path.is_file():
            raise RuntimeError("The downloaded translation package is missing.")
        if path.suffix.lower() != ".argosmodel":
            raise RuntimeError("Unexpected translation package format.")
        size = path.stat().st_size
        if size <= 0 or size > LocalTranslator.MAX_PACKAGE_BYTES:
            raise RuntimeError("The downloaded translation package has an invalid size.")
        if not zipfile.is_zipfile(path):
            raise RuntimeError("The translation package is not a valid archive.")
        total = 0
        with zipfile.ZipFile(path, "r") as archive:
            members = archive.infolist()
            if not members or len(members) > LocalTranslator.MAX_PACKAGE_FILES:
                raise RuntimeError("The translation package contains an unsafe number of files.")
            for member in members:
                normalized = PurePosixPath(member.filename.replace("\\", "/"))
                if normalized.is_absolute() or ".." in normalized.parts or not normalized.parts:
                    raise RuntimeError("The translation package contains an unsafe path.")
                unix_mode = (member.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(unix_mode):
                    raise RuntimeError("The translation package may not contain symbolic links.")
                total += max(0, int(member.file_size))
                if total > LocalTranslator.MAX_UNCOMPRESSED_BYTES:
                    raise RuntimeError("The translation package expands beyond the safety limit.")
                if member.compress_size > 0 and member.file_size / member.compress_size > 2_000:
                    raise RuntimeError("The translation package has a suspicious compression ratio.")
        return path

    def install_pair(
        self,
        source: str,
        target: str,
        progress: Callable[[str], None] | None = None,
        preferred_intermediate: str = "en",
    ) -> None:
        from argostranslate import package

        source = normalize_language(source, allow_auto=False, default="")
        target = normalize_language(target, allow_auto=False, default="")
        intermediate = normalize_language(preferred_intermediate, allow_auto=False, default="en")
        if not source or not target or source == target:
            raise RuntimeError("Invalid translation language pair.")
        if self.can_translate(source, target, intermediate):
            return
        if progress:
            progress("index")
        package.update_package_index()
        available = package.get_available_packages()
        direct = next((item for item in available if item.from_code == source and item.to_code == target), None)
        selected = [direct] if direct is not None else []
        if not selected and source != intermediate and target != intermediate:
            first = next((item for item in available if item.from_code == source and item.to_code == intermediate), None)
            second = next((item for item in available if item.from_code == intermediate and item.to_code == target), None)
            if first and second:
                selected = [first, second]
        if not selected:
            raise TranslationMissingError(f"TRANSLATION_PACKAGE_UNAVAILABLE:{source}:{target}")
        for item in selected:
            # Do not reinstall a pair that another step already provided.
            if self.can_translate(item.from_code, item.to_code, intermediate):
                continue
            if progress:
                progress("download")
            download_path = self._validate_download(item.download())
            if progress:
                progress("install")
            package.install_from_path(download_path)
        if not self.can_translate(source, target, intermediate):
            raise RuntimeError("The translation package was installed but the route is still unavailable.")
