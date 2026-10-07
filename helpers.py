def fake_inputs(monkeypatch, answers):
    """Make input() return the given answers, one per call."""
    answers = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))