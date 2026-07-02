"""NSPanel-basiertes Preview-Overlay fuer macOS.

Alle AppKit-Aufrufe laufen via AppHelper.callAfter auf dem Main-Thread
(die NSApplication-Loop aus platform/macos/app.py pumpt dort Events).
tkinter ist auf macOS in Hintergrund-Threads nicht nutzbar.
"""
import logging
import threading

from AppKit import (
    NSPanel, NSTextField, NSColor, NSFont, NSMakeRect,
    NSWindowStyleMaskBorderless, NSWindowStyleMaskNonactivatingPanel,
    NSBackingStoreBuffered, NSStatusWindowLevel, NSTextAlignmentCenter,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorStationary,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
)
from PyObjCTools import AppHelper

from . import monitors
from ...overlay_layout import DEFAULTS, resolve_target_monitor, calculate_position

PAD_X = 20
PAD_Y = 12
MAX_TEXT_WIDTH = 700.0


def _hex_to_nscolor(hex_str, alpha=1.0):
    h = hex_str.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return NSColor.colorWithSRGBRed_green_blue_alpha_(r, g, b, alpha)


class _PanelBundle:
    __slots__ = ('panel', 'label', 'fixed_monitor')

    def __init__(self, panel, label, fixed_monitor=None):
        self.panel = panel
        self.label = label
        self.fixed_monitor = fixed_monitor


class PreviewOverlay:
    def __init__(self, overlay_config: dict = None):
        self.logger = logging.getLogger(__name__)
        self._config = {**DEFAULTS, **(overlay_config or {})}
        self._panels = {}
        self._visible = False
        self._all_mode = self._config['monitor'] == 'all'
        self._ready = threading.Event()
        AppHelper.callAfter(self._build_initial)

    # --- Aufbau (Main-Thread) ---

    def _build_initial(self):
        try:
            if self._all_mode:
                self._build_all_panels()
            else:
                self._panels[0] = self._make_panel()
        except Exception as e:
            self.logger.error(f"Preview overlay failed: {e}")
        finally:
            self._ready.set()

    def _make_panel(self, fixed_monitor=None):
        style = NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel
        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 400, 60), style, NSBackingStoreBuffered, False)
        panel.setLevel_(NSStatusWindowLevel)
        panel.setOpaque_(False)
        panel.setAlphaValue_(float(self._config['opacity']))
        panel.setIgnoresMouseEvents_(True)
        panel.setHidesOnDeactivate_(False)
        panel.setHasShadow_(True)
        panel.setBackgroundColor_(_hex_to_nscolor(self._config['bg_color']))
        panel.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary)

        label = NSTextField.wrappingLabelWithString_("")
        label.setFont_(NSFont.boldSystemFontOfSize_(float(self._config['font_size'])))
        label.setTextColor_(_hex_to_nscolor(self._config['text_color']))
        label.setAlignment_(NSTextAlignmentCenter)
        label.setDrawsBackground_(False)
        panel.contentView().addSubview_(label)
        return _PanelBundle(panel, label, fixed_monitor)

    def _build_all_panels(self):
        self._destroy_panels()
        for mon in monitors.enumerate_monitors():
            self._panels[mon.index] = self._make_panel(fixed_monitor=mon)

    def _destroy_panels(self):
        for pb in self._panels.values():
            pb.panel.orderOut_(None)
            pb.panel.close()
        self._panels.clear()

    # --- Layout (Main-Thread) ---

    def _layout_panel(self, pb, text):
        pb.label.setStringValue_(text)
        pb.label.setPreferredMaxLayoutWidth_(MAX_TEXT_WIDTH)
        size = pb.label.intrinsicContentSize()
        text_w = min(max(size.width, 40.0), MAX_TEXT_WIDTH)
        text_h = max(size.height, 20.0)
        win_w = text_w + 2 * PAD_X
        win_h = text_h + 2 * PAD_Y

        mon = pb.fixed_monitor if pb.fixed_monitor else resolve_target_monitor(monitors, self._config)
        x, y_top = calculate_position(self._config, mon, int(win_w), int(win_h))
        y_cocoa = monitors.primary_height() - y_top - win_h

        pb.label.setFrame_(NSMakeRect(PAD_X, PAD_Y, text_w, text_h))
        pb.panel.setFrame_display_(NSMakeRect(x, y_cocoa, win_w, win_h), True)

    # --- Public API (thread-safe) ---

    def update_text(self, text):
        def _update():
            for pb in self._panels.values():
                self._layout_panel(pb, text)
                if not self._visible:
                    pb.panel.orderFrontRegardless()
            self._visible = True
        AppHelper.callAfter(_update)

    def show(self):
        def _show():
            for pb in self._panels.values():
                pb.panel.orderFrontRegardless()
            self._visible = True
        AppHelper.callAfter(_show)

    def hide(self):
        def _hide():
            for pb in self._panels.values():
                pb.panel.orderOut_(None)
            self._visible = False
        AppHelper.callAfter(_hide)

    def update_config(self, overlay_config: dict):
        self._config = {**DEFAULTS, **(overlay_config or {})}
        new_all_mode = self._config['monitor'] == 'all'

        def _apply():
            if new_all_mode != self._all_mode:
                self._all_mode = new_all_mode
                if new_all_mode:
                    self._build_all_panels()
                else:
                    self._destroy_panels()
                    self._panels[0] = self._make_panel()

            for pb in self._panels.values():
                pb.panel.setAlphaValue_(float(self._config['opacity']))
                pb.panel.setBackgroundColor_(_hex_to_nscolor(self._config['bg_color']))
                pb.label.setFont_(NSFont.boldSystemFontOfSize_(float(self._config['font_size'])))
                pb.label.setTextColor_(_hex_to_nscolor(self._config['text_color']))
                if self._visible:
                    self._layout_panel(pb, str(pb.label.stringValue()))
                    pb.panel.orderFrontRegardless()
        AppHelper.callAfter(_apply)
