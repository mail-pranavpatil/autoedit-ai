from autoedit.music import CORNFIELD, FEELING_BLUE, THANK_YOU, choose_track, coerce_music_id


def test_coerce_legacy_categories():
    assert coerce_music_id("cinematic") == CORNFIELD
    assert coerce_music_id("technology") == FEELING_BLUE
    assert coerce_music_id("thank_you") == THANK_YOU


def test_gratitude_picks_thank_you():
    assert (
        choose_track(
            summary="A thank you to everyone who supported this milestone",
            tone="warm grateful",
            transcript="Thank you. This journey means the world. I am so grateful.",
        )
        == THANK_YOU
    )


def test_dramatic_reveal_picks_cornfield():
    assert (
        choose_track(
            summary="This changes everything in medicine",
            tone="cinematic dramatic",
            transcript="Nobody saw this coming. High stakes. The secret breakthrough.",
        )
        == CORNFIELD
    )


def test_calm_explain_picks_feeling_blue():
    assert (
        choose_track(
            summary="What is photosynthesis explained simply",
            tone="calm educational",
            transcript="In this lesson I explain how plants make food, step by step.",
        )
        == FEELING_BLUE
    )


def test_ai_topic_alone_is_not_cornfield():
    assert (
        choose_track(
            summary="A calm intro to how large language models work",
            tone="calm educational",
            transcript="Today I explain what a transformer is and how to learn the basics.",
        )
        == FEELING_BLUE
    )
