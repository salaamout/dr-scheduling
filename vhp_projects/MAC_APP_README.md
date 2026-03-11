# Patient Database Mac App

> **⚠️ DEPRECATED** — This approach is deprecated. See `scripts/build_app.sh`
> for the recommended PyInstaller method, which produces a single
> `PatientDatabase.app` that can be copied to any Mac.

## Installation Complete! ✓

Your Patient Database is now available as a Mac application on your Desktop.

## How to Use

1. **Launch the App**: Double-click the "Patient Database" icon on your Desktop
2. **The app will**:
   - Start a local web server
   - Automatically open your default web browser
   - Display the Patient Database interface

## Features

- 🖥️ **Desktop App**: No need to open Terminal or run commands
- 🌐 **Web Interface**: Full-featured web interface in your browser
- 💾 **Local Database**: All data stored locally on your Mac
- 🔒 **Privacy**: No internet connection required

## Troubleshooting

### App doesn't open
- Make sure you have Python 3 installed
- Right-click the app and select "Open" if macOS blocks it
- Check that port 5001 is not already in use

### Browser doesn't open automatically
- Manually navigate to: `http://127.0.0.1:5001`

### To stop the server
- Press `Cmd + Q` or close the Terminal window that opens

## Updating the App

If you make changes to the source code:

1. Navigate to your project folder:
   ```bash
   cd /Users/kyleeaton/dr_projects/vhp_projects
   ```

2. Run the creation script again:
   ```bash
   ./scripts/create_mac_app.sh
   ```

This will rebuild the app on your Desktop with your latest changes.

## Files

- **Patient Database.app** — The Mac application (on your Desktop)
- **scripts/launch_app.py** — Python launcher script (deprecated)
- **scripts/create_mac_app.sh** — Script to build/rebuild the Mac app (deprecated)
- **scripts/create_icon.sh** — Script to create the app icon (deprecated)

## Uninstalling

To remove the app, simply drag "Patient Database.app" from your Desktop to the Trash.

---

**Note**: The application runs a local Flask server. Your data remains private and stored locally in the `instance/patients.db` file.
