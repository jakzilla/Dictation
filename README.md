# Dication

A local macOS dictation app powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Hold a hotkey to record, release to transcribe and type the result at your cursor. Everything runs locally — no API calls, no cloud services.

## Features

- **Press-and-hold dictation** — hold Right Option key to record, release to transcribe
- **Local Whisper** — runs faster-whisper locally with the `base` model (int8 quantized)
- **Menu bar icon** — 🎤 with model switching (tiny, base, small, medium) and quit
- **Animated overlay** — floating indicator at the bottom of the screen while listening
- **Types at cursor** — transcribed text is typed wherever your cursor is, in any app
- **Starts on login** — can be added as a Login Item or launched from Applications

## Requirements

- macOS 13+
- Python 3.11
- Homebrew

## Setup

```bash
# Clone the repo
git clone https://github.com/jakzilla/Dication.git
cd Dication

# Install dependencies
./setup.sh
```

Or manually:

```bash
brew install portaudio
pip3 install -r requirements.txt
```

## Usage

### Run from Terminal

```bash
cd Dication
arch -arm64 python3 -u main.py
```

### Install as an app

Create a Dictation.app using AppleScript (Script Editor > save as Application), with this script:

```applescript
on run
    do shell script "pkill -f \"Dication/main.py\" 2>/dev/null; true"
    delay 0.5
    tell application "Terminal"
        set w to do script "cd ~/Dication && arch -arm64 /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -u main.py; exit"
        delay 1
        set miniaturized of front window to true
    end tell
end run
```

Save it to `/Applications/Dictation.app`.

### Start on login

Add Dictation.app as a Login Item in **System Settings > General > Login Items**.

## Permissions

You must grant the following in **System Settings > Privacy & Security**:

| Permission | What needs it | Why |
|---|---|---|
| **Accessibility** | Python.app, Terminal | Typing text at cursor |
| **Input Monitoring** | Python.app, Terminal | Detecting the hotkey |
| **Microphone** | Terminal | Recording audio (prompted automatically) |

Python.app is located at:
`/Library/Frameworks/Python.framework/Versions/3.11/Resources/Python.app`

## Configuration

Edit `config.py` to change:

- **Hotkey** — default is Right Option (`Key.alt_r`)
- **Model size** — default is `base` (also changeable from the menu bar)
- **Overlay appearance** — colors, size, position, animation speed

## How it works

1. A CGEventTap on a background thread detects Right Option press/release
2. On press: starts recording audio via `sounddevice` (16kHz mono) and shows the overlay
3. On release: stops recording, runs `faster-whisper` transcription in a worker thread
4. Transcribed text is typed at the cursor position via `pynput`
5. The menu bar and overlay use PyObjC (`NSStatusBar`, `NSWindow`)

## License

MIT
