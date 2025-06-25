![Mark Cover](https://github.com/user-attachments/assets/4f93f077-055f-46a3-95e1-cf4cd9ec6888)

# Mark

Mark is a customizable Discord status manager that automatically updates your status based on the apps you're currently using, your idle time, and other configurable conditions.

## Features

- **Automatic Status Updates**: Changes your Discord status based on your currently active application
- **Idle Detection**: Updates status when you're away from your computer
- **Plugin System**: Extensible architecture allows for custom status triggers
- **Customizable Settings**: Configure how and when your status updates
- **Graceful Shutdown**: Properly resets your status when exiting or shutting down your computer
- **Colorblind Mode**: Alternative status indicators for colorblind users

## Requirements

- Python 3.12+
- Discord Token (see installation instructions)

### Platform Support

- **macOS**: Full support including all features
- **Linux/Windows**: Not supported, but implementations are welcome

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/DomBom16/mark.git
   cd mark
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root directory with your Discord token:
   ```
   DISCORD_TOKEN=your_token_here
   ```

   To get your Discord token, see the [Token Guide](#discord-token-guide) below.

4. (Optional) Customize the `settings.jsonc` file to match your preferences

5. Make the script executable:
   ```bash
   chmod +x mark.py
   ```

## Usage

### Installation

Run the script initially with:

```bash
./mark.py install --name mark
```

Or with Python directly:

```bash
python3 mark.py install --name mark
```

Go through the installation process.

### Command Line Options

- `--fast` or `-f`: Skip the startup screen and launch immediately
- `--verbose`: Enable verbose logging for debugging
- `--getbundle` or `--gb`: Get the app bundle of any focused app
- `--version` or `-v`: Get the current version of Mark

### Exiting

Press `Ctrl+C` to exit. Mark will gracefully reset your status before closing.

## Configuration

### Settings File

Mark uses a `settings.jsonc` file for configuration. This file supports JSON with comments, allowing you to document your settings.

Key settings include:

- `update_interval`: Minimum time (in seconds) between status updates
- `retry_interval`: How often to check for status changes
- `colorblind`: Enable colorblind mode for status indicators
- `statuses`: Configure default and application-specific statuses

### Discord Token Guide

**Important**: Your Discord token gives access to your account. Never share it publicly.

To obtain your Discord token:

1. Open Discord in your web browser or as a desktop application
2. Press `Cmd+Option+I` to open Developer Tools
3. Go to the Network tab
4. In Discord, perform any action like changing channels
5. Look for a request in the Network tab
6. Find the request headers and look for "Authorization" - that's your token

## Plugin System

Mark supports custom plugins for more advanced status management. Plugins can be added to the `plugins` directory and enabled in the settings file.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Created by [@dombom](https://github.com/DomBom16)
