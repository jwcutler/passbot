#!/usr/bin/env python3
"""
Satellite Pass Tracker - Calculate satellite pass times and add to Google Calendar
"""

import os
import re
import requests
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Union
from dataclasses import dataclass

from skyfield.api import load, Topos, EarthSatellite
from skyfield.timelib import Time

import google.auth
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


@dataclass
class SatellitePass:
    """Represents a single satellite pass"""
    rise_time: datetime
    culmination_time: datetime
    set_time: datetime
    max_elevation: float
    satellite_name: str


class TLEHandler:
    """Handle TLE data from various sources"""
    
    @staticmethod
    def parse_tle_text(tle_text: str) -> Tuple[str, str, str]:
        """Parse TLE text and extract name and two lines"""
        lines = [line.strip() for line in tle_text.strip().split('\n') if line.strip()]
        
        if len(lines) < 2:
            raise ValueError("TLE must contain at least 2 lines")
        
        # If 3 lines, first is name
        if len(lines) >= 3 and not lines[0].startswith('1 '):
            name = lines[0]
            line1 = lines[1]
            line2 = lines[2]
        else:
            # Extract name from line 1 if available
            name = "Unknown Satellite"
            line1 = lines[0]
            line2 = lines[1]
            
        return name, line1, line2
    
    @staticmethod
    def fetch_tle_from_url(url: str) -> Tuple[str, str, str]:
        """Fetch TLE data from a URL"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return TLEHandler.parse_tle_text(response.text)
        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch TLE from URL: {e}")
    
    @staticmethod
    def fetch_tle_from_norad_id(norad_id: int) -> Tuple[str, str, str]:
        """Fetch TLE data using NORAD ID from CelesTrak"""
        url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={norad_id}&FORMAT=tle"
        return TLEHandler.fetch_tle_from_url(url)


class SatellitePassCalculator:
    """Calculate satellite passes for a given observer location"""
    
    def __init__(self, observer_lat: float, observer_lon: float, observer_elevation: float = 0):
        self.ts = load.timescale()
        self.observer = Topos(latitude_degrees=observer_lat, 
                            longitude_degrees=observer_lon,
                            elevation_m=observer_elevation)
    
    def calculate_passes(self, satellite_name: str, line1: str, line2: str, 
                        days_ahead: int = 5, min_elevation: float = 10.0) -> List[SatellitePass]:
        """Calculate visible passes for the given satellite"""
        satellite = EarthSatellite(line1, line2, satellite_name, self.ts)
        
        # Time range for calculations
        t0 = self.ts.now()
        t1 = self.ts.utc(t0.utc_datetime() + timedelta(days=days_ahead))
        
        # Find passes
        t, events = satellite.find_events(self.observer, t0, t1, altitude_degrees=min_elevation)
        
        passes = []
        current_pass = {}
        
        for ti, event in zip(t, events):
            dt = ti.utc_datetime()
            
            if event == 0:  # Rise
                current_pass = {'rise_time': dt}
            elif event == 1:  # Culmination
                if 'rise_time' in current_pass:
                    topocentric = (satellite - self.observer).at(ti)
                    alt, az, distance = topocentric.altaz()
                    current_pass['culmination_time'] = dt
                    current_pass['max_elevation'] = alt.degrees
            elif event == 2:  # Set
                if 'rise_time' in current_pass and 'culmination_time' in current_pass:
                    current_pass['set_time'] = dt
                    current_pass['satellite_name'] = satellite_name
                    
                    passes.append(SatellitePass(**current_pass))
                    current_pass = {}
        
        return passes


class GoogleCalendarIntegration:
    """Handle Google Calendar API integration"""
    
    def __init__(self, credentials_file: str = 'credentials.json', calendar_id: str = 'primary'):
        self.calendar_id = calendar_id
        self.service = self._authenticate(credentials_file)
    
    def _authenticate(self, credentials_file: str):
        """Authenticate with Google Calendar API"""
        creds = None
        token_file = 'token.json'
        
        # Load existing token
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                from google_auth_oauthlib.flow import InstalledAppFlow
                SCOPES = ['https://www.googleapis.com/auth/calendar']
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        return build('calendar', 'v3', credentials=creds)
    
    def create_pass_event(self, satellite_pass: SatellitePass) -> str:
        """Create a calendar event for a satellite pass"""
        event = {
            'summary': f'{satellite_pass.satellite_name} Pass',
            'description': f'Max elevation: {satellite_pass.max_elevation:.1f}°\nCreated by Satellite Pass Tracker',
            'start': {
                'dateTime': satellite_pass.rise_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': satellite_pass.set_time.isoformat(),
                'timeZone': 'UTC',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        
        event_result = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
        return event_result.get('htmlLink')
    
    def delete_satellite_events(self, satellite_name: str = None, days_ahead: int = 30) -> int:
        """Delete existing satellite pass events"""
        now = datetime.utcnow()
        time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
        time_min = (now - timedelta(days=7)).isoformat() + 'Z'  # Look back 7 days for existing events
        
        # Search for events
        events_result = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        deleted_count = 0
        
        for event in events:
            summary = event.get('summary', '')
            description = event.get('description', '')
            
            # Check if this is a satellite pass event
            is_satellite_event = (
                'Pass' in summary and 
                'Created by Satellite Pass Tracker' in description
            )
            
            # If satellite_name specified, only delete events for that satellite
            if satellite_name:
                is_satellite_event = is_satellite_event and satellite_name in summary
            
            if is_satellite_event:
                try:
                    self.service.events().delete(
                        calendarId=self.calendar_id,
                        eventId=event['id']
                    ).execute()
                    deleted_count += 1
                except Exception as e:
                    print(f"Warning: Could not delete event {event.get('summary', 'Unknown')}: {e}")
        
        return deleted_count


class SatellitePassTracker:
    """Main class coordinating satellite pass tracking and calendar integration"""
    
    def __init__(self, observer_lat: float, observer_lon: float, observer_elevation: float = 0,
                 calendar_id: str = 'primary', credentials_file: str = 'credentials.json'):
        self.calculator = SatellitePassCalculator(observer_lat, observer_lon, observer_elevation)
        self.calendar = GoogleCalendarIntegration(credentials_file, calendar_id)
        self.tle_handler = TLEHandler()
    
    def track_satellite(self, tle_input: Union[str, int], days_ahead: int = 5, 
                       min_elevation: float = 10.0, delete_existing: bool = False) -> List[str]:
        """Track satellite and add passes to calendar"""
        
        # Determine input type and get TLE data
        if isinstance(tle_input, int):
            # NORAD ID
            name, line1, line2 = self.tle_handler.fetch_tle_from_norad_id(tle_input)
        elif tle_input.startswith('http'):
            # URL
            name, line1, line2 = self.tle_handler.fetch_tle_from_url(tle_input)
        else:
            # TLE text
            name, line1, line2 = self.tle_handler.parse_tle_text(tle_input)
        
        # Delete existing events if requested
        if delete_existing:
            deleted_count = self.calendar.delete_satellite_events(name, days_ahead)
            print(f"Deleted {deleted_count} existing {name} events")
        
        # Calculate passes
        passes = self.calculator.calculate_passes(name, line1, line2, days_ahead, min_elevation)
        
        # Add to calendar
        event_links = []
        for sat_pass in passes:
            link = self.calendar.create_pass_event(sat_pass)
            event_links.append(link)
        
        return event_links
    
    def delete_all_satellite_events(self, days_ahead: int = 30) -> int:
        """Delete all satellite pass events created by this script"""
        return self.calendar.delete_satellite_events(None, days_ahead)


if __name__ == "__main__":
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='Track satellite passes and add to Google Calendar')
    parser.add_argument('tle_input', nargs='?', help='TLE text, NORAD ID, or URL containing TLE data')
    parser.add_argument('--lat', type=float, help='Observer latitude')
    parser.add_argument('--lon', type=float, help='Observer longitude')
    parser.add_argument('--elevation', type=float, default=0, help='Observer elevation in meters')
    parser.add_argument('--days', type=int, default=5, help='Days ahead to calculate passes')
    parser.add_argument('--min-elevation', type=float, default=10.0, help='Minimum elevation for passes')
    parser.add_argument('--calendar-id', default='primary', help='Google Calendar ID')
    parser.add_argument('--credentials', default='credentials.json', help='Google API credentials file')
    parser.add_argument('--delete-existing', action='store_true', help='Delete existing satellite events before creating new ones')
    parser.add_argument('--delete-all', action='store_true', help='Delete all satellite pass events and exit')
    
    args = parser.parse_args()
    
    # Handle delete-all mode
    if args.delete_all:
        if not args.lat or not args.lon:
            print("Error: --lat and --lon are required for calendar operations")
            exit(1)
        
        tracker = SatellitePassTracker(
            observer_lat=args.lat,
            observer_lon=args.lon,
            observer_elevation=args.elevation,
            calendar_id=args.calendar_id,
            credentials_file=args.credentials
        )
        
        try:
            deleted_count = tracker.delete_all_satellite_events(args.days)
            print(f"Deleted {deleted_count} satellite pass events")
        except Exception as e:
            print(f"Error: {e}")
        exit(0)
    
    # Check required arguments for normal operation
    if not args.tle_input:
        print("Error: tle_input is required (unless using --delete-all)")
        exit(1)
    if not args.lat or not args.lon:
        print("Error: --lat and --lon are required")
        exit(1)
    
    # Convert NORAD ID if it's a number
    tle_input = args.tle_input
    try:
        tle_input = int(tle_input)
    except ValueError:
        pass
    
    tracker = SatellitePassTracker(
        observer_lat=args.lat,
        observer_lon=args.lon,
        observer_elevation=args.elevation,
        calendar_id=args.calendar_id,
        credentials_file=args.credentials
    )
    
    try:
        event_links = tracker.track_satellite(tle_input, args.days, args.min_elevation, args.delete_existing)
        print(f"Created {len(event_links)} calendar events")
        for link in event_links:
            print(f"Event: {link}")
    except Exception as e:
        print(f"Error: {e}")