"""macOS monitor enumeration via NSScreen/Quartz.

Alle Koordinaten werden in ein globales Top-Left-Koordinatensystem normiert
(Ursprung: linke obere Ecke des Primär-Monitors, y wächst nach unten) — wie
beim Windows Virtual Screen und bei CoreGraphics. Die Overlay-Schicht
konvertiert bei Bedarf zurück nach Cocoa (bottom-left).
"""
from dataclasses import dataclass

from AppKit import NSScreen, NSWorkspace
import Quartz


@dataclass
class MonitorInfo:
    index: int = 0
    name: str = "Primary"
    x: int = 0
    y: int = 0
    width: int = 1920
    height: int = 1080
    work_x: int = 0
    work_y: int = 0
    work_width: int = 1920
    work_height: int = 1080
    is_primary: bool = True


def primary_height() -> float:
    screens = NSScreen.screens()
    return screens[0].frame().size.height if screens else 0.0


def _to_monitor_info(screen, index, primary_h):
    f = screen.frame()
    v = screen.visibleFrame()
    name = str(screen.localizedName()) if hasattr(screen, 'localizedName') else f"Display {index}"
    return MonitorInfo(
        index=index,
        name=name,
        x=int(f.origin.x),
        y=int(primary_h - f.origin.y - f.size.height),
        width=int(f.size.width),
        height=int(f.size.height),
        work_x=int(v.origin.x),
        work_y=int(primary_h - v.origin.y - v.size.height),
        work_width=int(v.size.width),
        work_height=int(v.size.height),
        is_primary=(index == 0),
    )


def enumerate_monitors():
    primary_h = primary_height()
    screens = NSScreen.screens()
    if not screens:
        return [MonitorInfo()]
    return [_to_monitor_info(s, i, primary_h) for i, s in enumerate(screens)]


def get_monitor_by_index(index):
    mons = enumerate_monitors()
    for m in mons:
        if m.index == index:
            return m
    return mons[0]


def get_primary_monitor():
    return enumerate_monitors()[0]


def _monitor_at_point(x, y):
    mons = enumerate_monitors()
    for m in mons:
        if m.x <= x < m.x + m.width and m.y <= y < m.y + m.height:
            return m
    return mons[0]


def get_monitor_at_cursor():
    event = Quartz.CGEventCreate(None)
    loc = Quartz.CGEventGetLocation(event)  # CG = Top-Left-Koordinaten
    return _monitor_at_point(loc.x, loc.y)


def get_monitor_of_focused_window():
    try:
        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if app is None:
            return get_monitor_at_cursor()
        pid = app.processIdentifier()
        options = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
        for info in Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID) or []:
            if info.get(Quartz.kCGWindowOwnerPID) != pid:
                continue
            if info.get(Quartz.kCGWindowLayer, 1) != 0:
                continue
            b = info.get(Quartz.kCGWindowBounds)
            if not b:
                continue
            cx = b['X'] + b['Width'] / 2
            cy = b['Y'] + b['Height'] / 2
            return _monitor_at_point(cx, cy)
    except Exception:
        pass
    return get_monitor_at_cursor()


def set_dpi_awareness():
    pass
