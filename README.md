# Satellite Pass Tracker

Calculate satellite pass times and automatically add them to Google Calendar.

## Features

- Support for multiple TLE input methods:
  - NORAD ID (fetches from CelesTrak)
  - Direct TLE text
  - URL containing TLE data
- Calculates visible satellite passes for your location
- Automatically creates Google Calendar events
- Configurable minimum elevation and time range

## Setup

1. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Google Calendar API:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Calendar API
   - Create credentials (OAuth2 client ID)
   - Download credentials as `credentials.json`

## Usage

Make sure your virtual environment is activated:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Then run the script:
```bash
python satellite_pass_tracker.py <TLE_INPUT> --lat <LATITUDE> --lon <LONGITUDE>
```

### Examples

**Using NORAD ID (ISS):**
```bash
python satellite_pass_tracker.py 25544 --lat 37.7749 --lon -122.4194
```

**Using URL:**
```bash
python satellite_pass_tracker.py "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle" --lat 37.7749 --lon -122.4194
```

**Using TLE text:**
```bash
python satellite_pass_tracker.py "ISS (ZARYA)
1 25544U 98067A   23001.00000000  .00000000  00000-0  00000-0 0  9999
2 25544  51.6400   0.0000 0000000   0.0000   0.0000 15.50000000000000" --lat 37.7749 --lon -122.4194
```

**Delete existing events before adding new ones:**
```bash
python satellite_pass_tracker.py 25544 --lat 37.7749 --lon -122.4194 --delete-existing
```

**Delete all satellite pass events:**
```bash
python satellite_pass_tracker.py --delete-all --lat 37.7749 --lon -122.4194
```

### Options

- `--elevation`: Observer elevation in meters (default: 0)
- `--days`: Days ahead to calculate passes (default: 5)
- `--min-elevation`: Minimum elevation for visible passes (default: 10°)
- `--calendar-id`: Google Calendar ID (default: 'primary' - your main calendar)
  - Use 'primary' for your main calendar
  - Use specific calendar ID like 'abc123@group.calendar.google.com' for other calendars
  - Find calendar IDs in Google Calendar Settings > [Calendar Name] > Calendar ID
- `--credentials`: Path to Google API credentials file (default: 'credentials.json')
- `--delete-existing`: Delete existing satellite events before creating new ones
- `--delete-all`: Delete all satellite pass events and exit (no new events created)

## Authentication

On first run, the script will open a browser window for Google OAuth authentication. After successful authentication, a `token.json` file will be created for future use.