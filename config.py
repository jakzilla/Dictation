"""Configuration constants for the dictation app."""

from pynput.keyboard import Key

# Hotkey: hold this key to record
HOTKEY = Key.alt_r  # Right Option key

# Audio settings
SAMPLE_RATE = 16000  # Hz — Whisper expects 16kHz
CHANNELS = 1         # Mono
MIN_DURATION = 0.3   # Seconds — ignore taps shorter than this

# Whisper model
MODEL_SIZE = "base"
COMPUTE_TYPE = "int8"
AVAILABLE_MODELS = ["tiny", "base", "small", "medium"]

# Overlay appearance
OVERLAY_WIDTH = 200
OVERLAY_HEIGHT = 60
OVERLAY_BOTTOM_MARGIN = 80  # Pixels from bottom of screen
OVERLAY_BG_COLOR = (0.1, 0.1, 0.18, 0.9)  # RGBA
OVERLAY_FG_COLOR = (0.88, 0.88, 0.88, 1.0)
OVERLAY_DOT_ACTIVE_COLOR = (0.0, 0.83, 1.0, 1.0)
OVERLAY_DOT_DIM_COLOR = (0.23, 0.23, 0.37, 1.0)
OVERLAY_DOT_INTERVAL = 0.2  # seconds between dot animation frames
