# Configuration Tips for Twistt

This document explains the different input and output modes available in Twistt, their use cases, and limitations.

## Output Methods (`--paste-method`)

| Method | Command | Keyboard Layout | Local Terminal | GUI Apps | Via Barrier/Synergy | Wayland |
|--------|---------|-----------------|----------------|----------|---------------------|---------|
| `clipboard` | Ctrl+V | N/A | Escape sequences | OK | Sync issue* | OK |
| `primary` | Middle-click | N/A | OK | OK | Sync issue* | OK |
| `xdotool` | xdotool type | Respected (AZERTY) | OK | OK | OK | No (X11 only) |

*Barrier syncs both buffers, but only when copy happens on the active machine. If Twistt copies while on source, target won't have it until you return.

### Recommendations

- **Local terminal**: Use `primary` (middle-click)
- **GUI applications**: Use `clipboard` or `xdotool`
- **Via Barrier/Synergy**: Use `xdotool` (only method that works)
- **Non-QWERTY layout**: Use `xdotool` (respects keyboard layout)
- **Wayland**: Use `clipboard` or `primary` (xdotool doesn't work)

### Details

#### `clipboard` (default)
- Copies text to CLIPBOARD selection, then sends Ctrl+V
- Hold Shift during recording to use Ctrl+Shift+V instead (for terminals)
- **Issue in terminals**: Navigation keys (arrows, delete) appear as escape sequences (`^[[D`, `^[[3~`)

#### `primary`
- Copies text to PRIMARY selection (X11), then sends middle-click
- Works well in terminals
- **Limitation**: Not synchronized by Barrier/Synergy to remote machines

#### `xdotool`
- Types text character by character via X11
- Respects current keyboard layout (AZERTY, QWERTZ, etc.)
- Works through Barrier/Synergy
- **Limitation**: X11 only, does not work on Wayland

## Typing Mode (`--use-typing` / `-t`)

Uses ydotool to type ASCII characters one by one instead of pasting.

| Feature | Typing Mode | Paste Mode |
|---------|-------------|------------|
| Speed | Slower (key delays) | Fast |
| Keyboard Layout | QWERTY only | N/A |
| Non-ASCII chars | Falls back to paste | Paste |

**Note**: The `-t` option uses ydotool which sends raw keycodes. This means it types in QWERTY regardless of your keyboard layout. For non-QWERTY layouts, use `--paste-method xdotool` instead.

## Input Methods

### Keyboard Hotkey Detection

| Method | Permissions | Setup | Use Case |
|--------|-------------|-------|----------|
| evdev (default) | `input` group | Add user to group | Full keyboard access |
| pynput (`--use-pynput`) | None | None | When evdev fails |
| API only (`--no-hotkey`) | None | None | StreamDeck/external triggers |

### Recommendations

- **Standard use**: Let Twistt auto-detect (evdev with pynput fallback)
- **StreamDeck/API only**: Use `--no-hotkey` to skip keyboard detection entirely
- **Permission issues**: Use `--use-pynput` or `--no-hotkey`

## Indicator (`--no-indicator`)

The indicator displays "(Twistting...)" while recording to show activity.

| Setting | Terminal | GUI Apps |
|---------|----------|----------|
| Indicator ON | Escape sequences appear | OK |
| Indicator OFF (`--no-indicator`) | OK | No visual feedback |

**Recommendation**: Use `--no-indicator` when working primarily in terminals.

## Example Configurations

### StreamDeck with Barrier (recommended for multi-PC setup)

```env
TWISTT_NO_HOTKEY=yes
TWISTT_NO_INDICATOR=yes
TWISTT_PASTE_METHOD=xdotool
TWISTT_LANGUAGE=fr
```

### Local terminal use only

```env
TWISTT_NO_INDICATOR=yes
TWISTT_PASTE_METHOD=primary
TWISTT_HOTKEY=f12
```

### GUI applications (default behavior)

```env
TWISTT_PASTE_METHOD=clipboard
TWISTT_HOTKEY=f12
```

### Wayland with terminal

```env
TWISTT_NO_INDICATOR=yes
TWISTT_PASTE_METHOD=primary
TWISTT_HOTKEY=f12
```

## Troubleshooting

### Escape sequences in terminal (`^[[D`, `^[[3~`)

These are arrow/delete keys sent by the indicator or correction mode.

**Solutions**:
1. Add `--no-indicator` to disable the "(Twistting...)" indicator
2. Use `--paste-method primary` or `--paste-method xdotool`

### Text typed in QWERTY instead of AZERTY

The `-t` (typing) mode uses ydotool which sends raw keycodes.

**Solution**: Use `--paste-method xdotool` instead of `-t`

### Paste doesn't work via Barrier/Synergy

Barrier syncs both CLIPBOARD and PRIMARY, but the sync only happens when the copy occurs on the active (target) machine. If Twistt copies text while you're on the source machine, the buffer won't be synced to the target until you return to the source.

**Solution**: Use `--paste-method xdotool` which types directly via X11

### xdotool doesn't work

You're probably on Wayland. Check with:
```bash
echo $XDG_SESSION_TYPE
```

**Solution**: Use `--paste-method primary` or `--paste-method clipboard`
