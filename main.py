"""Dictation app — hold Right Option to dictate, release to transcribe.

Uses PyObjC NSApplication run loop for menu bar + overlay.
"""

import logging
import os
import threading
import time
import sys

import objc

# Set up logging to file
log_path = os.environ.get("DICTATION_LOG", os.path.join(os.path.dirname(__file__), "dictation.log"))
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("dictation")
from AppKit import (
    NSApplication, NSApp, NSStatusBar, NSMenu, NSMenuItem,
    NSVariableStatusItemLength, NSImage, NSObject,
    NSApplicationActivationPolicyAccessory,
    NSOnState, NSOffState,
)
from Foundation import NSRunLoop, NSDate
from PyObjCTools import AppHelper
from pynput.keyboard import Controller as KeyboardController

from audio import AudioRecorder
from config import MIN_DURATION, SAMPLE_RATE, MODEL_SIZE, AVAILABLE_MODELS
from hotkey import HotkeyListener
from overlay import Overlay
from transcriber import Transcriber


def on_main(func):
    """Run func on the main thread."""
    AppHelper.callAfter(func)


class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        self._setup()

    def _setup(self):
        self.recorder = AudioRecorder()
        self.keyboard = KeyboardController()
        self.overlay = Overlay()
        self._recording = False
        self._model_loading = True
        self._current_model = MODEL_SIZE

        # Menu bar icon
        self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )
        self.status_item.setTitle_("🎤")
        self.status_item.setHighlightMode_(True)

        # Build menu
        menu = NSMenu.alloc().init()

        # Model submenu
        model_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Model", None, "")
        model_submenu = NSMenu.alloc().init()
        self._model_menu_items = {}
        for m in AVAILABLE_MODELS:
            mi = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(m, "selectModel:", "")
            mi.setTarget_(self)
            mi.setState_(NSOnState if m == MODEL_SIZE else NSOffState)
            self._model_menu_items[m] = mi
            model_submenu.addItem_(mi)
        model_item.setSubmenu_(model_submenu)
        menu.addItem_(model_item)

        menu.addItem_(NSMenuItem.separatorItem())

        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "quitApp:", "q")
        quit_item.setTarget_(self)
        menu.addItem_(quit_item)

        self.status_item.setMenu_(menu)

        # Start hotkey listener on main thread (must be here for event monitor)
        self.hotkey_listener = HotkeyListener(
            on_activate=self._on_hotkey_press,
            on_deactivate=self._on_hotkey_release,
        )
        self.hotkey_listener.start()

        # Load model in background
        self.status_item.setTitle_("⏳")
        threading.Thread(target=self._load_model, daemon=True).start()

    def _load_model(self):
        self.transcriber = Transcriber(self._current_model)
        self._model_loading = False
        on_main(lambda: self.status_item.setTitle_("🎤"))
        log.info("Dictation app is ready. Hold Right Option to dictate.")

    @objc.IBAction
    def selectModel_(self, sender):
        model_name = sender.title()
        if model_name == self._current_model:
            return
        for name, item in self._model_menu_items.items():
            item.setState_(NSOnState if name == model_name else NSOffState)
        self._current_model = model_name
        self._model_loading = True
        on_main(lambda: self.status_item.setTitle_("⏳"))

        def load():
            self.transcriber.load_model(model_name)
            self._model_loading = False
            on_main(lambda: self.status_item.setTitle_("🎤"))
            log.info(f"Switched to model '{model_name}'.")

        threading.Thread(target=load, daemon=True).start()

    @objc.IBAction
    def quitApp_(self, sender):
        if hasattr(self, "hotkey_listener"):
            self.hotkey_listener.stop()
        NSApp.terminate_(None)

    def _on_hotkey_press(self):
        if self._recording or self._model_loading:
            return
        self._recording = True
        self.recorder.start()
        on_main(lambda: self.overlay.show("Listening..."))
        on_main(lambda: self.status_item.setTitle_("🔴"))

    def _on_hotkey_release(self):
        if not self._recording:
            return
        self._recording = False
        audio = self.recorder.stop()

        if audio.size < SAMPLE_RATE * MIN_DURATION:
            on_main(lambda: self.overlay.hide())
            on_main(lambda: self.status_item.setTitle_("🎤"))
            return

        on_main(lambda: self.overlay.set_status("Transcribing..."))
        threading.Thread(target=self._transcribe_and_type, args=(audio,), daemon=True).start()

    def _transcribe_and_type(self, audio):
        try:
            log.info(f"Audio stats: min={audio.min():.4f} max={audio.max():.4f} mean={abs(audio).mean():.4f}")
            text = self.transcriber.transcribe(audio)
            log.info(f"Transcription result: '{text}'")
            on_main(lambda: self.overlay.hide())
            on_main(lambda: self.status_item.setTitle_("🎤"))
            if text:
                time.sleep(0.15)
                log.info("Typing text...")
                self.keyboard.type(text)
                log.info("Text typed")
        except Exception as e:
            log.error(f"Transcription error: {e}", exc_info=True)
            on_main(lambda: self.overlay.hide())
            on_main(lambda: self.status_item.setTitle_("🎤"))


LOCK_FILE = os.path.join(os.path.dirname(__file__), ".dictation.pid")


def acquire_lock():
    """Ensure only one instance runs at a time."""
    if os.path.exists(LOCK_FILE):
        try:
            old_pid = int(open(LOCK_FILE).read().strip())
            os.kill(old_pid, 0)  # Check if still running
            # Still running — kill it so we take over
            os.kill(old_pid, 15)
            time.sleep(0.5)
        except (ProcessLookupError, ValueError, PermissionError):
            pass  # Already dead
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def release_lock():
    try:
        os.remove(LOCK_FILE)
    except OSError:
        pass


def main():
    acquire_lock()
    try:
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        delegate = AppDelegate.alloc().init()
        app.setDelegate_(delegate)
        log.info("Starting Dictation app...")
        AppHelper.runEventLoop()
    finally:
        release_lock()


if __name__ == "__main__":
    main()
