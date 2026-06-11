import unicodedata

import pytest

from card_downloader.decklist.normalize import normalize_name


def test_curly_apostrophe():
    assert normalize_name("Urza\u2019s Saga") == "Urza's Saga"


def test_curly_double_quotes():
    assert normalize_name("\u201cTest\u201d") == '"Test"'


def test_whitespace_trim_and_collapse():
    assert normalize_name("  Sol   Ring  ") == "Sol Ring"


def test_nfc_normalization():
    # e + combining acute -> é (single codepoint)
    composed = unicodedata.normalize("NFC", "e\u0301")
    assert normalize_name(composed) == composed
