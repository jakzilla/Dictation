"""Global hotkey listener using CGEventTap on a dedicated thread with its own CFRunLoop."""

import logging
import threading
import Quartz

log = logging.getLogger("dictation")

RIGHT_OPTION_KEYCODE = 61
NSAlternateKeyMask = 1 << 19


class HotkeyListener:
    def __init__(self, on_activate, on_deactivate):
        self._on_activate = on_activate
        self._on_deactivate = on_deactivate
        self._pressed = False
        self._run_loop = None
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if self._run_loop:
            Quartz.CFRunLoopStop(self._run_loop)

    def _callback(self, proxy, event_type, event, refcon):
        try:
            keycode = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
            flags = Quartz.CGEventGetFlags(event)

            if keycode == RIGHT_OPTION_KEYCODE:
                option_down = bool(flags & NSAlternateKeyMask)
                if option_down and not self._pressed:
                    self._pressed = True
                    log.info("Right Option pressed")
                    self._on_activate()
                elif not option_down and self._pressed:
                    self._pressed = False
                    log.info("Right Option released")
                    self._on_deactivate()
        except Exception as e:
            log.error(f"Hotkey callback error: {e}")

        return event

    def _run(self):
        mask = (Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged) |
                Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown) |
                Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp))
        tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionListenOnly,
            mask,
            self._callback,
            None,
        )

        if tap is None:
            log.error("Failed to create CGEventTap — check Accessibility/Input Monitoring permissions")
            return

        source = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
        self._run_loop = Quartz.CFRunLoopGetCurrent()
        Quartz.CFRunLoopAddSource(self._run_loop, source, Quartz.kCFRunLoopDefaultMode)
        Quartz.CGEventTapEnable(tap, True)
        log.info("Hotkey listener started (CGEventTap on dedicated thread)")
        Quartz.CFRunLoopRun()
