"""Laeuft nur auf macOS (SSH in GUI-Session).

Aufruf: PYTHONPATH=src .venv/bin/python tests/e2e/test_monitors_macos.py
"""
from whisper_key.platform.macos import monitors


def main():
    mons = monitors.enumerate_monitors()
    assert len(mons) >= 1, "keine Monitore gefunden"
    for m in mons:
        assert m.width > 0 and m.height > 0, f"ungueltige Groesse: {m}"
        assert m.work_width <= m.width and m.work_height <= m.height, f"work > frame: {m}"
    p = monitors.get_primary_monitor()
    assert p.is_primary
    assert p.x == 0 and p.y == 0, f"Primary muss Top-Left-Ursprung (0,0) haben: {p}"
    c = monitors.get_monitor_at_cursor()
    assert c.index in {m.index for m in mons}
    f = monitors.get_monitor_of_focused_window()
    assert f.index in {m.index for m in mons}
    print("OK:", [f"{m.name} {m.width}x{m.height}@({m.x},{m.y})" for m in mons])


if __name__ == "__main__":
    main()
