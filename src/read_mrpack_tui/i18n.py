"""Translation resource loading for the MRPACK Inspector UI."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_LOCALE = "en-us"
SUPPORTED_LOCALES = ("en-us", "zh-cn", "zh-tw")
LOCALES_DIRECTORY = Path(__file__).resolve().parent / "locales"
EMOJI_RESOURCE = LOCALES_DIRECTORY / "emoji.yml"


class TranslationError(RuntimeError):
    """Raised when bundled translation resources are incomplete or malformed."""


def _flatten(values: Mapping[str, Any], prefix: str = "") -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in values.items():
        qualified_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, Mapping):
            result.update(_flatten(value, qualified_key))
        elif isinstance(value, str):
            result[qualified_key] = value
        else:
            raise TranslationError(f"Translation key '{qualified_key}' must have a string value")
    return result


def _load_resource(path: Path) -> dict[str, str]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            loaded = yaml.safe_load(stream)
    except OSError as error:
        raise TranslationError(f"Unable to read translation resource: {path}") from error
    except yaml.YAMLError as error:
        raise TranslationError(f"Invalid YAML in translation resource: {path}") from error
    if not isinstance(loaded, Mapping):
        raise TranslationError(f"Translation resource must contain a mapping: {path}")
    return _flatten(loaded)


@dataclass(frozen=True, slots=True)
class Translator:
    locale: str
    messages: Mapping[str, str]
    emojis: Mapping[str, str]

    def t(self, key: str, **values: object) -> str:
        try:
            message = self.messages[key]
        except KeyError as error:
            raise TranslationError(f"Missing translation key: {key}") from error
        try:
            return message.format(**values)
        except KeyError as error:
            raise TranslationError(f"Missing value '{error.args[0]}' for translation key: {key}") from error

    def ui(self, key: str, **values: object) -> str:
        """Return translated Textual UI copy prefixed with its semantic emoji."""
        try:
            emoji = self.emojis[key]
        except KeyError as error:
            raise TranslationError(f"Missing emoji key: {key}") from error
        return f"{emoji} {self.t(key, **values)}"


def load_translator(locale: str) -> Translator:
    normalized_locale = locale.casefold()
    if normalized_locale not in SUPPORTED_LOCALES:
        raise ValueError(f"Unsupported locale: {locale}")

    resources = {name: _load_resource(LOCALES_DIRECTORY / f"{name}.yml") for name in SUPPORTED_LOCALES}
    base_keys = set(resources[DEFAULT_LOCALE])
    for name, resource in resources.items():
        missing = sorted(base_keys - set(resource))
        extra = sorted(set(resource) - base_keys)
        if missing or extra:
            details = []
            if missing:
                details.append(f"missing: {', '.join(missing)}")
            if extra:
                details.append(f"extra: {', '.join(extra)}")
            raise TranslationError(f"Translation keys do not match for {name} ({'; '.join(details)})")

    emojis = _load_resource(EMOJI_RESOURCE)
    visible_keys = {key for key in base_keys if not key.startswith("cli.")}
    missing_emojis = sorted(visible_keys - set(emojis))
    extra_emojis = sorted(set(emojis) - visible_keys)
    if missing_emojis or extra_emojis:
        details = []
        if missing_emojis:
            details.append(f"missing: {', '.join(missing_emojis)}")
        if extra_emojis:
            details.append(f"extra: {', '.join(extra_emojis)}")
        raise TranslationError(f"Emoji keys do not match visible UI keys ({'; '.join(details)})")

    messages = dict(resources[DEFAULT_LOCALE])
    messages.update(resources[normalized_locale])
    return Translator(normalized_locale, messages, emojis)
