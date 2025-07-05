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
- **GitHub Actions automation** for daily tracking
- **Batch processing** of multiple satellites from configuration

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

## Batch Processing

For tracking multiple satellites automatically, use the batch processor:

```bash
python satellite_batch_tracker.py
```

This requires a `config.yaml` file with your configuration:

```yaml
# Observer location
observer:
  latitude: 37.7749
  longitude: -122.4194
  elevation: 0

# Tracking settings
tracking:
  days_ahead: 10
  min_elevation: 10.0
  delete_existing: true

# Google Calendar settings
calendar:
  calendar_id: "primary"
  
# List of satellites to track
satellites:
  - name: "ISS"
    url: "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle"
  - name: "NOAA-18"
    url: "https://celestrak.org/NORAD/elements/gp.php?CATNR=28654&FORMAT=tle"
```

## GitHub Actions Automation

For automated daily tracking, see the `GITHUB_SETUP.md` guide. This sets up:
- Daily automated runs
- Secure credential storage via GitHub Secrets
- Custom configuration via GitHub Secrets
- Error logging and monitoring

## Authentication

The script supports two authentication methods:

### Service Account (Recommended for automation)
- Download service account JSON from Google Cloud Console
- Share your calendar with the service account email
- Use with `--credentials service-account.json`
- No expiration, perfect for GitHub Actions

### OAuth2 (For interactive use)
- On first run, opens browser for authentication
- Creates `token.json` for future use
- May require periodic re-authentication

## Local Testing

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Test with service account
python satellite_pass_tracker.py 25544 --lat 37.7749 --lon -122.4194 --credentials service-account.json

# Test batch processing
python satellite_batch_tracker.py

# Delete test events
python satellite_pass_tracker.py --delete-all --lat 37.7749 --lon -122.4194
```