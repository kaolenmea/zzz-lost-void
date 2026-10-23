# zzz-lost-void

English | [简体中文](README.md)

Full automation for the **Lost Void** mode of Zenless Zone Zero, plus a **Battle Assistant** (auto battle / dodge assist).

Split from [ZenlessZoneZero-OneDragon](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon), keeping only Lost Void and the Battle Assistant, and focusing on better navigation, selection logic and stability in Lost Void.

- **Lost Void**: enters and clears Lost Void automatically (Frontline Purge / Task Force / Matrix Operation, etc.), including team selection, movement between floors, Resonium / gear picks and combat.
- **Battle Assistant**: auto battle, dodge assist, auto-battle config templates and debug tools.

## What's improved in Lost Void compared with OneDragon

### Navigation and movement

| Improvement | How | Result |
|---|---|---|
| Monocular depth obstacle avoidance | Adds Depth Anything V2 Small. The frame is split into 16 columns with an estimated obstacle distance each; the aim column is chosen by obstacle depth plus turning cost, preferring the emptier side | Fewer wall bumps and less zig-zagging; about 16 s saved in the first room of floor 1 in a real run. GPU only (CUDA / DirectML); disabled automatically without a GPU, no CPU fallback |
| Stuck detection and escape | Detects "stuck" from scene-static frame differencing (1.5 s) plus the target icon position; strafes with A/D, switches side after 2 failed attempts, and restarts the floor after 12 stuck events | No more sitting in place until timeout |
| Route planning from the Tab map | Reads the Tab map, scores routes by region-type priority, locks the planned entry and skips doors of types already visited in the room | More stable routes within a floor, less detouring |
| YOLO HUD mask | Blacks out the avatar and notification icons before detection | Fewer false detections on the HUD |

### Choices and resources

| Improvement | How | Result |
|---|---|---|
| Resonium selection | Priority: same faction → NEW → configured priority → quiz fallback → blind click; refreshes automatically when no same-faction option is offered | Builds come together more reliably |
| Bangboo shop | Refresh costs 50/100/200/300; refreshes about 3 times, then saves coins for the last rest area; always keeps enough to buy a Resonium | Doesn't burn all coins on refreshes |
| Battle end detection | OCR on the distance hint every 0.8 s | Moves on right after a fight ends instead of idling |
| Run memory | Used NPCs and picks of the current run are persisted to `lost_void_run_memory.yml`; the label is checked before interacting on the entry floor | No duplicate interactions after a retry |

### Configuration and usability

- Planned run count (1–99); stops automatically when reached.
- Selectable difficulty (1–6); Frontline Purge supports an Aether Activity boost choice.
- GUI reduced to five pages: Home / Lost Void / Battle Assistant / Resources / Settings, with a Chinese / English UI switch (Settings → UI Language).
- A navigation sampling tool writes per-run data to `.debug/lost_void_navigation/` for tuning.

## Usage

### End users: portable package

1. Download the latest `ZZZLostVoid-vX.Y.Z.zip` from [Releases](https://github.com/kaolenmea/zzz-lost-void/releases) and extract it fully to a fixed folder (preferably a path without non-ASCII characters or spaces).
2. Set the game to 1920×1080 (windowed or fullscreen) and double-click `ZZZLostVoid.exe` (accept the administrator prompt).
3. On the Lost Void page, choose a farming goal and planned run count, then press Start.

The portable package needs no Python installation and already includes the models. Settings and FAQ: [User Manual](docs/user/README.md) (Chinese). Packaging: [Release](docs/develop/setup/release.md).

### Developers: run from source

Windows only; designed for a 1920×1080 game resolution.

```powershell
# 1. Install uv: https://github.com/astral-sh/uv
winget install --id=astral-sh.uv -e

# 2. Install dependencies (uv prepares Python 3.11 automatically)
uv sync --group dev
# Add the gamepad group if you need gamepad background mode
uv sync --group dev --group gamepad

# 3. Launch the GUI
copy .env.sample .env
uv run --env-file .env src/zzz_lv/gui/app.py

# 4. Run tests (no game or models needed)
uv run --env-file .env pytest -m "not requires_models"
```

If not started as administrator, a UAC prompt appears and the app relaunches elevated. The game runs as administrator, and mouse/keyboard input from a non-elevated process is blocked by Windows, so elevation is required.

On first launch from source you will be prompted to download the OCR, polychrome and Lost Void detection models (from the upstream [OneDragon-Env](https://github.com/OneDragon-Anything/OneDragon-Env) releases).

See [docs/develop/README.md](docs/develop/README.md) and [AGENTS.md](AGENTS.md) for development notes (Chinese).

## Disclaimer

- For learning and exchange only. You use this tool at your own risk.
- No individual, seller or media account is authorized to sell this software. If you paid for it, beware of scams.
- Any problem caused by paid boosting services that use this software is unrelated to this project.
- The developers provide no after-sales support.

## Origin and license

Split from [OneDragon-Anything/ZenlessZoneZero-OneDragon](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon) (upstream commit `9012d3e7`). The generic framework (`one_dragon` / `one_dragon_qt` / `onnxocr`) is kept, only Lost Void and the Battle Assistant remain, and the business package `zzz_od` is renamed to `zzz_lv`. Other differences: the installer, launcher, auto-update and telemetry are removed, the portable package ships its own Python, and automated tests live in this repo's `tests/`.

As required by the upstream license, this project is released under [GPL-3.0](LICENSE); copyright belongs to the upstream authors and this project's contributors. `src/onnxocr/` comes from [OnnxOCR](https://github.com/jingsongliujing/OnnxOCR) under Apache-2.0; see [src/onnxocr/LICENSE](src/onnxocr/LICENSE).
