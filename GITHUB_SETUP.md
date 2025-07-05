# GitHub Actions Setup Guide

This guide walks you through setting up automated satellite pass tracking using GitHub Actions.

## Prerequisites

1. A GitHub account
2. A Google Cloud Project with Calendar API enabled
3. Google API credentials (OAuth2)

## Step 1: Fork/Create Repository

1. Fork this repository or create a new one with these files
2. Push your code to GitHub

## Step 2: Prepare Your Configuration

**Note:** The workflow now uses a custom configuration stored as a GitHub Secret instead of the `config.yaml` file in the repository. This keeps your location and satellite list private.

You'll need to prepare your configuration YAML content for Step 4. Here's the format:

```yaml
# Observer location
observer:
  latitude: YOUR_LATITUDE
  longitude: YOUR_LONGITUDE
  elevation: YOUR_ELEVATION_METERS

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
  - name: "Your Satellite"
    url: "https://example.com/your-tle-url"
```

## Step 3: Set Up Google API Credentials

### Create Service Account (Recommended for GitHub Actions)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API
4. Go to "IAM & Admin" → "Service Accounts"
5. Click "Create Service Account"
   - Name: "Satellite Pass Tracker"
   - Description: "Automated satellite pass tracking"
6. Click "Create and Continue"
7. Skip the optional steps and click "Done"
8. Click on the newly created service account
9. Go to "Keys" tab → "Add Key" → "Create new key"
10. Choose JSON format and download the file

### Share Your Calendar

1. Open the downloaded service account JSON file
2. Find the `client_email` field (looks like `name@project.iam.gserviceaccount.com`)
3. In Google Calendar:
   - Go to Settings → Settings for my calendars
   - Select your calendar
   - Under "Share with specific people", add the service account email
   - Set permission to "Make changes to events"
   - Click "Send"

## Step 4: Add GitHub Secrets

1. Go to your GitHub repository
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Add these repository secrets:

### GOOGLE_CREDENTIALS
- Copy the entire contents of your service account JSON file
- Paste it as the value for `GOOGLE_CREDENTIALS`
- This is the only authentication secret needed (no token required!)

### CUSTOM_CONFIG
- Copy your custom configuration YAML content (from Step 2)
- This replaces the need for `config.yaml` in your repository
- Example value:
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

## Step 5: Test the Workflow

1. Go to "Actions" tab in your repository
2. Click "Track Satellite Passes"
3. Click "Run workflow" to test manually
4. Check the logs to ensure it works

## Step 6: Customize Schedule

Edit `.github/workflows/track-satellites.yml` to change the schedule:

```yaml
on:
  schedule:
    # Run daily at 6 AM UTC
    - cron: '0 6 * * *'
```

Use [crontab.guru](https://crontab.guru/) to help create cron expressions.

## Troubleshooting

### Common Issues

1. **Authentication Errors**: 
   - Ensure your `GOOGLE_CREDENTIALS` secret contains the service account JSON
   - Verify the service account email has access to your calendar
2. **TLE Download Fails**: Check that your satellite URLs are valid
3. **Calendar Permission Denied**: Make sure the Calendar API is enabled and your OAuth consent screen is configured

### Checking Logs

1. Go to "Actions" tab
2. Click on a workflow run
3. Click "track-passes" job to see detailed logs

### Manual Testing

Test locally before committing:

#### Using Service Account (Recommended)
```bash
# 1. Download your service account JSON from Google Cloud Console
# 2. Save it as service-account.json in the project directory
# 3. Make sure your calendar is shared with the service account email

# Test single satellite
python satellite_pass_tracker.py 25544 --lat YOUR_LAT --lon YOUR_LON --credentials service-account.json

# Test batch processing
python satellite_batch_tracker.py
```

#### Using OAuth2 (Interactive)
```bash
# For first-time setup or local testing without service account
python satellite_pass_tracker.py 25544 --lat YOUR_LAT --lon YOUR_LON

# This will open a browser for authentication and create token.json
```

#### Test Configuration
```bash
# Create a test config.yaml
cat > config.yaml << EOF
observer:
  latitude: 37.7749
  longitude: -122.4194
  elevation: 0

tracking:
  days_ahead: 10
  min_elevation: 10.0
  delete_existing: true

calendar:
  calendar_id: "primary"
  
satellites:
  - name: "ISS"
    url: "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle"
EOF

# Run batch tracker
python satellite_batch_tracker.py
```

## Security Notes

- Never commit `credentials.json` or `token.json` to your repository
- Use GitHub Secrets for all sensitive data
- The workflow runs on public GitHub infrastructure, so avoid sensitive data in logs

## Advanced Configuration

### Different Calendars

To use a specific calendar instead of your primary calendar:

1. Find the Calendar ID in Google Calendar Settings
2. Update your `CUSTOM_CONFIG` secret:
   ```yaml
   calendar:
     calendar_id: "abc123@group.calendar.google.com"
   ```

### Custom Notification

Add Slack/Discord notifications by modifying the workflow:

```yaml
- name: Notify on completion
  if: always()
  # Add your notification step here
```

## Monitoring

- Check the Actions tab regularly for failed runs
- Review logs for any errors
- Monitor your Google API quota in the Cloud Console