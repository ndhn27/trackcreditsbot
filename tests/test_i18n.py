"""Tests for i18n.py — translation lookup and completeness."""
from __future__ import annotations

import pytest
from i18n import t, t_lang, LANG_DICT
from tests.conftest import FakeContext


class TestTLang:
    def test_returns_en_string(self):
        assert t_lang("analyzing", "en") == "Analyzing track data..."

    def test_falls_back_to_en_on_unknown_lang(self):
        assert t_lang("analyzing", "xx") == "Analyzing track data..."

    def test_returns_bracket_placeholder_for_missing_key(self):
        result = t_lang("__nonexistent_key_xyz__", "en")
        assert result == "[__nonexistent_key_xyz__]"

    def test_no_empty_en_values(self):
        empty = [k for k, v in LANG_DICT["en"].items() if not v]
        assert not empty, f"Empty en translations: {empty}"

    @pytest.mark.parametrize("key,placeholder", [
        ("top_title",               "page"),
        ("admin_dashboard",         "count"),
        ("admin_approved",          "sub_type"),
        ("admin_rejected",          "sub_type"),
        ("user_contrib_approved",   "sub_type"),
        ("disambig_prompt",         "query"),
        ("admin_promo_prompt",      "promo_type"),
        ("searching_other_artists", "title"),
        ("no_other_artists",        "title"),
        ("lyrics_source_label",     "source"),
        ("community_source_label",  "source"),
        ("community_contrib_label", "contributor"),
        ("credits_community_by",    "contributor"),
        ("credits_rights",          "artist"),
    ])
    def test_template_key_has_placeholder(self, key, placeholder):
        val = LANG_DICT["en"][key]
        assert f"{{{placeholder}}}" in val, (
            f"key={key}: missing {{{placeholder}}}"
        )

    def test_template_keys_are_formattable(self):
        """All template keys must not raise when .format() is called with dummy args."""
        fakes = dict(
            page=1, count=0, sub_type="credits", title="T", query="Q",
            promo_type="Instrumental", source="Genius", contributor="user",
            artist="Artist", balance=100, credits=10,
        )
        for key, val in LANG_DICT["en"].items():
            try:
                val.format(**fakes)
            except KeyError as exc:
                pytest.fail(f"en key '{key}' uses unknown placeholder: {exc}")


class TestT:
    def test_reads_lang_from_context(self):
        ctx = FakeContext(lang="en")
        assert t("analyzing", ctx) == "Analyzing track data..."

    def test_defaults_to_en_when_no_lang_key(self):
        ctx = FakeContext()
        ctx.user_data = {}
        assert t("analyzing", ctx) == "Analyzing track data..."

    def test_handles_none_user_data_gracefully(self):
        ctx = FakeContext()
        ctx.user_data = None
        result = t("analyzing", ctx)
        assert result == "Analyzing track data..."

    def test_works_with_object_lacking_user_data(self):
        class Bare:
            pass
        result = t("analyzing", Bare())
        assert result == "Analyzing track data..."
