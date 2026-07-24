"""Tests for merger.py — pure data transformation, no I/O."""
from __future__ import annotations

from merger import merge_track_metadata, parse_youtube_credits, pick_best_lyrics


class TestMergeTrackMetadata:
    def test_prefers_genius_title_over_yt(self):
        r = merge_track_metadata(
            genius_data={"title": "G Title", "artist": "G Artist"},
            yt_data={"title": "YT Title", "artist": "YT Artist"},
        )
        assert r["title"] == "G Title"
        assert r["artist"] == "G Artist"

    def test_falls_back_to_yt_when_genius_missing_title(self):
        r = merge_track_metadata(genius_data={}, yt_data={"title": "YT Title", "artist": "YT Artist"})
        assert r["title"] == "YT Title"

    def test_all_empty_returns_empty_strings(self):
        r = merge_track_metadata()
        assert r["title"] == ""
        assert r["artist"] == ""
        assert r["thumb"] == ""

    def test_none_inputs_safe(self):
        r = merge_track_metadata(genius_data=None, mb_data=None, yt_data=None)
        assert r["title"] == ""

    def test_mb_label_beats_genius_label(self):
        r = merge_track_metadata(
            genius_data={"credits": {"Label": "G Label"}},
            mb_data={"label": "MB Label", "isrc": ""},
        )
        assert r["label"] == "MB Label"

    def test_genius_label_used_when_mb_absent(self):
        r = merge_track_metadata(genius_data={"credits": {"Label": "G Label"}}, mb_data={})
        assert r["label"] == "G Label"

    def test_isrc_from_mb(self):
        r = merge_track_metadata(mb_data={"isrc": "VNAM12345678", "label": ""})
        assert r["isrc"] == "VNAM12345678"

    def test_thumb_from_yt(self):
        r = merge_track_metadata(yt_data={"thumb": "https://img.example.com/t.jpg"})
        assert r["thumb"] == "https://img.example.com/t.jpg"

    def test_album_from_genius_credits(self):
        r = merge_track_metadata(genius_data={"credits": {"Album": "After Hours"}})
        assert r["album"] == "After Hours"

    def test_release_date_from_genius_credits(self):
        r = merge_track_metadata(genius_data={"credits": {"Released on": "2020-03-20"}})
        assert r["release_date"] == "2020-03-20"


class TestParseYoutubeCredits:
    def test_parses_composer(self):
        desc = "Composer: Nguyen Van A\nLyricist: Tran Thi B"
        r = parse_youtube_credits(desc)
        assert r["Composer"] == "Nguyen Van A"
        assert r["Lyricist"] == "Tran Thi B"

    def test_parses_released_on(self):
        r = parse_youtube_credits("Released on: 2023-05-01")
        assert r["Released on"] == "2023-05-01"

    def test_maps_provided_to_youtube(self):
        r = parse_youtube_credits("Provided to YouTube by Universal Music")
        assert r["Distributed by"] == "Universal Music"

    def test_empty_returns_empty(self):
        assert parse_youtube_credits("") == {}

    def test_none_returns_empty(self):
        assert parse_youtube_credits(None) == {}  # type: ignore[arg-type]

    def test_first_occurrence_wins(self):
        r = parse_youtube_credits("Producer: A\nProducer: B")
        assert r["Producer"] == "A"

    def test_unknown_lines_ignored(self):
        r = parse_youtube_credits("Some random line\nAnother line")
        assert r == {}

    def test_mixer_maps_to_mixing_engineer(self):
        r = parse_youtube_credits("Mixer: DJ Mike")
        assert r["Mixing Engineer"] == "DJ Mike"

    def test_multiline_desc(self):
        desc = (
            "Composer: Le Hieu\n"
            "Lyricist: Phung Khanh Linh\n"
            "Label: Vietnam Music Box\n"
            "Released on: 2022-01-15\n"
        )
        r = parse_youtube_credits(desc)
        assert r["Composer"] == "Le Hieu"
        assert r["Lyricist"] == "Phung Khanh Linh"
        assert r["Label"] == "Vietnam Music Box"
        assert r["Released on"] == "2022-01-15"


class TestPickBestLyrics:
    def test_prefers_genius(self):
        lyrics, source = pick_best_lyrics({"lyrics": "Genius text"}, "Auto text")
        assert lyrics == "Genius text"
        assert source == "Genius"

    def test_falls_back_to_auto_when_genius_empty(self):
        lyrics, source = pick_best_lyrics({"lyrics": ""}, "Auto text")
        assert lyrics == "Auto text"
        assert source == "Auto-fetched"

    def test_none_genius_uses_auto(self):
        lyrics, source = pick_best_lyrics(None, "Auto text")
        assert lyrics == "Auto text"

    def test_both_none_returns_none_tuple(self):
        lyrics, source = pick_best_lyrics(None, None)
        assert lyrics is None
        assert source is None

    def test_genius_without_lyrics_key_falls_back(self):
        lyrics, source = pick_best_lyrics({}, "Auto text")
        assert lyrics == "Auto text"
