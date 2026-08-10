"""Unit tests for src/preprocessing/cleaner.py"""

from src.preprocessing.cleaner import clean_text, detect_language


def test_clean_text_strips_html_tags():
    raw = "Great product<br />Highly recommend"
    result = clean_text(raw)
    assert "<br" not in result
    assert "Great product" in result
    assert "Highly recommend" in result


def test_clean_text_decodes_html_entities():
    raw = "Price &amp; quality are great"
    result = clean_text(raw)
    assert "&amp;" not in result
    assert "&" in result


def test_clean_text_collapses_whitespace():
    raw = "Too   many\n\nspaces"
    result = clean_text(raw)
    assert "  " not in result


def test_detect_language_returns_none_for_short_text():
    assert detect_language("Love it") is None


def test_detect_language_detects_english_on_long_text():
    text = "This spray is really nice. It smells really good and works great every time."
    assert detect_language(text) == "en"
