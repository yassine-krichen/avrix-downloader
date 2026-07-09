import pytest

from app.services.download_options import build_ydl_attempts


def build(**overrides):
    fields = {
        "format_type": "mp4",
        "quality": "1080p",
        "download_policy": "best_effort",
        "output_template": "C:/downloads/%(title)s.%(ext)s",
        "progress_hook": lambda data: None,
        "download_subtitles": False,
        "subtitle_languages": "en",
        "embed_thumbnail": False,
        "ffmpeg_location": "C:/ffmpeg/ffmpeg.exe",
        **overrides,
    }
    return build_ydl_attempts(**fields)


def test_strict_quality_video_produces_a_single_attempt_with_no_fallback():
    attempts = build(download_policy="strict_quality")

    assert len(attempts) == 1
    assert attempts[0]["format"] == "bestvideo[height<=1080]+bestaudio"


def test_best_effort_video_adds_a_looser_fallback_attempt():
    attempts = build(download_policy="best_effort")

    assert len(attempts) == 2
    assert attempts[0]["format"] == "bestvideo[height<=1080]+bestaudio"
    assert attempts[1]["format"] == "best[ext=mp4]/best"


def test_best_effort_sets_403_workaround_extractor_args():
    attempts = build(download_policy="best_effort")

    for attempt in attempts:
        assert attempt["extractor_args"] == {"youtube": {"player_client": ["android", "web"]}}
        assert attempt["skip_unavailable_fragments"] is True


def test_strict_quality_does_not_set_403_workaround_extractor_args():
    attempts = build(download_policy="strict_quality")

    assert "extractor_args" not in attempts[0]
    assert attempts[0]["skip_unavailable_fragments"] is False


def test_strict_quality_video_without_ffmpeg_raises():
    with pytest.raises(RuntimeError, match="requires ffmpeg"):
        build(download_policy="strict_quality", ffmpeg_location=None)


def test_best_effort_video_without_ffmpeg_does_not_raise():
    attempts = build(download_policy="best_effort", ffmpeg_location=None)

    assert len(attempts) == 2


def test_quality_best_requests_bestvideo_plus_bestaudio_uncapped():
    attempts = build(quality="best", download_policy="strict_quality")

    assert attempts[0]["format"] == "bestvideo+bestaudio"


def test_quality_height_cap_is_derived_from_the_quality_label():
    attempts = build(quality="480p", download_policy="strict_quality")

    assert attempts[0]["format"] == "bestvideo[height<=480]+bestaudio"


def test_mp3_format_never_requires_ffmpeg_check_and_has_two_attempts():
    attempts = build(format_type="mp3", download_policy="strict_quality", ffmpeg_location=None)

    assert len(attempts) == 2
    assert attempts[0]["format"] == "bestaudio[ext=m4a]/bestaudio/best"
    assert attempts[1]["format"] == "bestaudio/best"
    assert all(a["postprocessors"] == [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}] for a in attempts)


def test_subtitles_parse_comma_separated_languages_and_strip_whitespace():
    attempts = build(download_subtitles=True, subtitle_languages="en, fr ,es")

    assert attempts[0]["writesubtitles"] is True
    assert attempts[0]["subtitleslangs"] == ["en", "fr", "es"]


def test_subtitles_off_by_default():
    attempts = build(download_subtitles=False)

    assert "writesubtitles" not in attempts[0]


def test_embed_thumbnail_sets_writethumbnail():
    attempts = build(embed_thumbnail=True)

    assert attempts[0]["writethumbnail"] is True


def test_bundled_ffmpeg_location_is_passed_through_to_ydl_opts():
    attempts = build(ffmpeg_location="C:/bundled/ffmpeg.exe")

    assert attempts[0]["ffmpeg_location"] == "C:/bundled/ffmpeg.exe"


def test_no_ffmpeg_location_omits_the_ydl_option():
    attempts = build(download_policy="best_effort", ffmpeg_location=None)

    assert "ffmpeg_location" not in attempts[0]
