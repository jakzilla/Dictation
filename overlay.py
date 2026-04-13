"""Floating overlay indicator using PyObjC (NSWindow)."""

import objc
from AppKit import (
    NSWindow, NSView, NSColor, NSFont, NSTextField,
    NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
    NSFloatingWindowLevel, NSMakeRect, NSScreen,
    NSTimer, NSRunLoop, NSDefaultRunLoopMode,
    NSViewWidthSizable, NSTextAlignmentCenter,
    NSApplication, NSEvent,
)

from config import (
    OVERLAY_WIDTH, OVERLAY_HEIGHT, OVERLAY_BOTTOM_MARGIN,
    OVERLAY_BG_COLOR, OVERLAY_FG_COLOR,
    OVERLAY_DOT_ACTIVE_COLOR, OVERLAY_DOT_DIM_COLOR,
    OVERLAY_DOT_INTERVAL,
)


class DotView(NSView):
    """Custom view that draws 3 animated dots."""

    def initWithFrame_(self, frame):
        self = objc.super(DotView, self).initWithFrame_(frame)
        if self:
            self._dot_index = 0
        return self

    def drawRect_(self, rect):
        bg = NSColor.colorWithRed_green_blue_alpha_(*OVERLAY_BG_COLOR)
        bg.setFill()
        path = __import__("AppKit").NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            self.bounds(), 12, 12
        )
        path.fill()

        dot_radius = 6
        dot_spacing = 24
        dot_y = 16
        start_x = (OVERLAY_WIDTH - dot_spacing * 2) / 2

        for i in range(3):
            if i == self._dot_index:
                color = NSColor.colorWithRed_green_blue_alpha_(*OVERLAY_DOT_ACTIVE_COLOR)
            else:
                color = NSColor.colorWithRed_green_blue_alpha_(*OVERLAY_DOT_DIM_COLOR)
            color.setFill()
            cx = start_x + i * dot_spacing
            dot_rect = NSMakeRect(cx - dot_radius, dot_y - dot_radius, dot_radius * 2, dot_radius * 2)
            __import__("AppKit").NSBezierPath.bezierPathWithOvalInRect_(dot_rect).fill()

    def advanceDot_(self, timer):
        self._dot_index = (self._dot_index + 1) % 3
        self.setNeedsDisplay_(True)


class Overlay:
    def __init__(self):
        frame = NSMakeRect(0, 0, OVERLAY_WIDTH, OVERLAY_HEIGHT)
        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False,
        )
        self._window.setLevel_(NSFloatingWindowLevel)
        self._window.setOpaque_(False)
        self._window.setBackgroundColor_(NSColor.clearColor())
        self._window.setIgnoresMouseEvents_(True)
        self._window.setHasShadow_(True)

        # Dot view
        content_frame = NSMakeRect(0, 0, OVERLAY_WIDTH, OVERLAY_HEIGHT)
        self._dot_view = DotView.alloc().initWithFrame_(content_frame)
        self._window.contentView().addSubview_(self._dot_view)

        # Status label
        label_frame = NSMakeRect(0, 2, OVERLAY_WIDTH, 20)
        self._label = NSTextField.alloc().initWithFrame_(label_frame)
        self._label.setStringValue_("Listening...")
        self._label.setBezeled_(False)
        self._label.setDrawsBackground_(False)
        self._label.setEditable_(False)
        self._label.setSelectable_(False)
        self._label.setAlignment_(NSTextAlignmentCenter)
        self._label.setFont_(NSFont.systemFontOfSize_(12))
        self._label.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(*OVERLAY_FG_COLOR))
        self._window.contentView().addSubview_(self._label)

        self._timer = None

    def _center_on_screen(self):
        # Use the screen containing the mouse cursor (active screen)
        mouse_loc = NSEvent.mouseLocation()
        target_screen = None
        for screen in NSScreen.screens():
            if screen.frame().origin.x <= mouse_loc.x < screen.frame().origin.x + screen.frame().size.width:
                target_screen = screen
                break
        if target_screen is None:
            target_screen = NSScreen.mainScreen()

        sf = target_screen.frame()
        x = sf.origin.x + (sf.size.width - OVERLAY_WIDTH) / 2
        y = sf.origin.y + OVERLAY_BOTTOM_MARGIN
        from Foundation import NSMakePoint
        self._window.setFrameOrigin_(NSMakePoint(x, y))

    def show(self, status="Listening..."):
        self._label.setStringValue_(status)
        self._dot_view._dot_index = 0
        self._dot_view.setNeedsDisplay_(True)
        self._center_on_screen()
        self._window.orderFront_(None)
        self._start_animation()

    def hide(self):
        self._stop_animation()
        self._window.orderOut_(None)

    def set_status(self, status):
        self._label.setStringValue_(status)

    def _start_animation(self):
        self._stop_animation()
        self._timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            OVERLAY_DOT_INTERVAL, self._dot_view, "advanceDot:", None, True
        )
        NSRunLoop.currentRunLoop().addTimer_forMode_(self._timer, NSDefaultRunLoopMode)

    def _stop_animation(self):
        if self._timer is not None:
            self._timer.invalidate()
            self._timer = None
