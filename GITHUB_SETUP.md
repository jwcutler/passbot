# GitHub Actions Setup Guide

This guide walks you through setting up automated satellite pass tracking using GitHub Actions.

## Prerequisites

1. A GitHub account
2. A Google Cloud Project with Calendar API enabled
3. Google API credentials (OAuth2)

## Step 1: Fork/Create Repository

1. Fork this repository or create a new one with these files
2. Push your code to GitHub

## Step 2: Configure Your Location and Satellites

1. Edit `config.yaml` in your repository
2. Update the observer location:
   ```yaml
   observer:
     latitude: YOUR_LATITUDE
     longitude: YOUR_LONGITUDE
     elevation: YOUR_ELEVATION_METERS
   ```
3. Add your satellites:
   ```yaml
   satellites:
     - name: "ISS"
       url: "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle"
     - name: "Your Satellite"
       url: "https://example.com/your-tle-url"
   ```

## Step 3: Set Up Google API Credentials

### Create OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Choose "Desktop application"
6. Download the credentials JSON file

### Generate Initial Token

Run this locally to generate the initial token:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the script once to generate token.json
python satellite_pass_tracker.py 25544 --lat YOUR_LAT --lon YOUR_LON
```

This will open a browser window for OAuth consent. After authorization, you'll have a `token.json` file.

## Step 4: Add GitHub Secrets

1. Go to your GitHub repository
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Add these repository secrets:

### GOOGLE_CREDENTIALS
- Copy the entire contents of your `credentials.json` file
- Paste it as the value for `GOOGLE_CREDENTIALS`

### GOOGLE_TOKEN
- Copy the entire contents of your `token.json` file
- Paste it as the value for `GOOGLE_TOKEN`

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

1. **Authentication Errors**: Ensure your `GOOGLE_CREDENTIALS` and `GOOGLE_TOKEN` secrets are correct
2. **TLE Download Fails**: Check that your satellite URLs are valid
3. **Calendar Permission Denied**: Make sure the Calendar API is enabled and your OAuth consent screen is configured

### Checking Logs

1. Go to "Actions" tab
2. Click on a workflow run
3. Click "track-passes" job to see detailed logs

### Manual Testing

Test locally before committing:

```bash
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
2. Update `config.yaml`:
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