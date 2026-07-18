"""Tests for services.py — pure rendering helpers."""
from __future__ import annotations

import pytest
from services import build_main_text, truncate_text_naturally, render_credits


class TestBuildMainText:
    def test_includes_title_and_artist(self):
        text = build_main_text("Blinding Lights", "The Weeknd", "", "Loaded")
        assert "Blinding Lights" in text
        assert "The Weeknd" in text

    def test_includes_status_text(self):
        text = build_main_text("T", "A", "", "Đã tải dữ liệu.")
        assert "Đã tải dữ liệu." in text

    def test_thumb_anchor_present_when_url_given(self):
        text = build_main_text("T", "A", "https://img.example.com/t.jpg", "OK")
        assert "https://img.example.com/t.jpg" in text

    def test_no_anchor_when_thumb_empty(self):
        text = build_main_text("T", "A", "", "OK")
        assert "<a href=" not in text

    def test_html_escaping_applied(self):
        text = build_main_text("A & B", "Artist <X>", "", "OK")
        assert "&amp;" in text
        assert "&lt;" in text

    def test_returns_non_empty_string(self):
        text = build_main_text("T", "A", "", "S")
        assert len(text) > 0


class TestTruncateTextNaturally:
    def test_short_text_unchanged(self):
        s = "Hello world"
        assert truncate_text_naturally(s, 100) == s

    def test_exact_length_not_truncated(self):
        s = "exactly11c"  # 10 chars
        assert truncate_text_naturally(s, 10) == s

    def test_truncation_adds_ellipsis(self):
        result = truncate_text_naturally("hello world is long", 8)
        assert result.endswith("...")

    def test_prefers_newline_boundary(self):
        text = "Line one\nLine two extra content here that is very long"
        result = truncate_text_naturally(text, 12)
        assert result.endswith("...")
        # Should have cut at the newline, not mid-word
        assert "Line one" in result

    def test_falls_back_to_space_boundary(self):
        text = "hello world this is long"
        result = truncate_text_naturally(text, 11)
        assert result.endswith("...")
        assert "hello world" in result

    def test_hard_cut_when_no_boundary_found(self):
        text = "abcdefghijklmnopqrstuvwxyz"
        result = truncate_text_naturally(text, 10)
        assert result.endswith("...")
        assert len(result) <= 13  # 10 + "..."


class TestRenderCredits:
    def test_includes_track_and_artist(self):
        text = render_credits(None, {}, None, "Track Name", "Artist Name")
        assert "Track Name" in text
        assert "Artist Name" in text

    def test_vi_no_data_message(self):
        text = render_credits(None, {}, None, "T", "A", lang="vi")
        assert "Không có credits gốc" in text

    def test_en_no_data_message(self):
        text = render_credits(None, {}, None, "T", "A", lang="en")
        assert "No original credits available" in text

    def test_genius_credits_rendered(self):
        genius = {"credits": {"Producer": "Metro Boomin", "Label": "Republic"}}
        text = render_credits(genius, {}, None, "T", "A")
        assert "Metro Boomin" in text
        assert "Republic" in text

    def test_yt_credits_rendered_when_genius_missing(self):
        text = render_credits(None, {"Mixing Engineer": "Alex M"}, None, "T", "A")
        assert "Alex M" in text

    def test_genius_field_wins_over_yt_same_field(self):
        genius = {"credits": {"Producer": "Genius P"}}
        yt = {"Producer": "YT P"}
        text = render_credits(genius, yt, None, "T", "A")
        assert "Genius P" in text
        assert "YT P" not in text

    def test_mb_isrc_and_label_added(self):
        text = render_credits(None, {}, None, "T", "A", mb_data={"isrc": "VNAM999", "label": "Sony"})
        assert "VNAM999" in text
        assert "Sony" in text

    def test_mb_does_not_overwrite_existing_isrc(self):
        genius = {"credits": {"ISRC": "GENIUS_ISRC"}}
        text = render_credits(genius, {}, None, "T", "A", mb_data={"isrc": "MB_ISRC", "label": ""})
        # Genius already had ISRC — mb should not override
        assert "GENIUS_ISRC" in text

    def test_db_credits_community_section_vi(self):
        text = render_credits(None, {}, "Producer: Someone", "T", "A", lang="vi")
        assert "Someone" in text
        assert "cộng đồng" in text

    def test_db_credits_community_section_en(self):
        text = render_credits(None, {}, "Producer: Someone", "T", "A", lang="en")
        assert "Someone" in text
        assert "Community description" in text

    def test_db_credits_lines_without_colon_skipped(self):
        text = render_credits(None, {}, "no colon here\nProducer: Valid", "T", "A")
        assert "no colon here" not in text
        assert "Valid" in text

    def test_rights_line_present(self):
        text = render_credits(None, {}, None, "T", "My Artist")
        assert "My Artist" in text
        assert "rights" in text.lower()

    def test_strips_artist_dash_from_title(self):
        # "The Weeknd - Blinding Lights" title with artist "The Weeknd"
        text = render_credits(None, {}, None, "The Weeknd - Blinding Lights", "The Weeknd")
        # The "The Weeknd - " prefix should be stripped from the Track: line
        assert "The Weeknd - Blinding Lights" not in text

    def test_default_lang_is_en(self):
        text = render_credits(None, {}, None, "T", "A")
        assert "No original credits available" in text
