# BloxFishing Bot

Automation bot for fishing in Blox Fruits.

## Features
- Automatic casting (hold 1s).
- Detection of exclamation mark for bites.
- Automated minigame:
  - Keeps the green rectangle on the fish (blue).
  - Prioritizes treasures (yellow) when they appear.
- Automatic collection and restart.

## Installation
1. Install Python 3.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Run `python main.py`.
2. Press **F6** to start/stop the bot.
3. Press **F7** for emergency stop.

## Configuration
The bot assumes a standard layout. If the detection area for the minigame or exclamation mark is incorrect, adjust the coordinates in `main.py`.
- `EXCLAMATION_IMAGE`: Path to the exclamation mark template.
- `MINIGAME_IMAGE`: Path to a reference image of the minigame.
