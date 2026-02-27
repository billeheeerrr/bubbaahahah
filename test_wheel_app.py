from wheel_app import WheelEntry, expanded_entries, pick_winner


def test_pick_winner_basic_angles() -> None:
    entries = [
        WheelEntry("A", "#111111"),
        WheelEntry("B", "#222222"),
        WheelEntry("C", "#333333"),
        WheelEntry("D", "#444444"),
    ]
    assert pick_winner(entries, 0).name == "B"
    assert pick_winner(entries, 90).name == "A"
    assert pick_winner(entries, 180).name == "D"
    assert pick_winner(entries, 270).name == "C"


def test_pick_winner_requires_entries() -> None:
    try:
        pick_winner([], 12)
    except ValueError as exc:
        assert "must not be empty" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_expanded_entries_uses_weight() -> None:
    entries = [WheelEntry("A", "#111", weight=1), WheelEntry("B", "#222", weight=3)]
    bag = expanded_entries(entries)
    assert [x.name for x in bag] == ["A", "B", "B", "B"]


def test_pick_winner_respects_weight_bias() -> None:
    entries = [WheelEntry("Low", "#111", weight=1), WheelEntry("High", "#222", weight=9)]
    winners = [pick_winner(entries, angle).name for angle in range(0, 360, 36)]
    assert winners.count("High") > winners.count("Low")
