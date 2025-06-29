#!/usr/bin/env python3
"""
Batch satellite pass tracker - Processes multiple satellites from config file
"""

import sys
import yaml
import logging
from datetime import datetime
from satellite_pass_tracker import SatellitePassTracker

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_file='config.yaml'):
    """Load configuration from YAML file"""
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config file: {e}")
        sys.exit(1)


def process_satellites(config):
    """Process all satellites from configuration"""
    # Extract settings
    observer = config['observer']
    tracking = config['tracking']
    calendar = config['calendar']
    satellites = config['satellites']
    
    # Create tracker instance
    tracker = SatellitePassTracker(
        observer_lat=observer['latitude'],
        observer_lon=observer['longitude'],
        observer_elevation=observer.get('elevation', 0),
        calendar_id=calendar.get('calendar_id', 'primary'),
        credentials_file='credentials.json'
    )
    
    # Statistics
    total_events = 0
    successful_satellites = 0
    failed_satellites = []
    
    logger.info(f"Starting satellite pass tracking for {len(satellites)} satellites")
    logger.info(f"Observer location: {observer['latitude']}, {observer['longitude']}")
    logger.info(f"Tracking {tracking['days_ahead']} days ahead with min elevation {tracking['min_elevation']}°")
    
    # Process each satellite
    for satellite in satellites:
        name = satellite['name']
        url = satellite['url']
        
        try:
            logger.info(f"Processing {name}...")
            
            # Track satellite
            event_links = tracker.track_satellite(
                tle_input=url,
                days_ahead=tracking['days_ahead'],
                min_elevation=tracking['min_elevation'],
                delete_existing=tracking.get('delete_existing', False)
            )
            
            logger.info(f"Created {len(event_links)} events for {name}")
            total_events += len(event_links)
            successful_satellites += 1
            
        except Exception as e:
            logger.error(f"Failed to process {name}: {e}")
            failed_satellites.append((name, str(e)))
    
    # Summary
    logger.info("="*60)
    logger.info("SUMMARY:")
    logger.info(f"Processed {successful_satellites}/{len(satellites)} satellites successfully")
    logger.info(f"Total events created: {total_events}")
    
    if failed_satellites:
        logger.warning(f"Failed satellites ({len(failed_satellites)}):")
        for name, error in failed_satellites:
            logger.warning(f"  - {name}: {error}")
    
    # Exit with error code if any satellites failed
    return 0 if not failed_satellites else 1


def main():
    """Main entry point"""
    try:
        # Check if credential files exist and are valid JSON
        import json
        import os
        
        if os.path.exists('credentials.json'):
            logger.info("credentials.json found")
            try:
                with open('credentials.json', 'r') as f:
                    json.load(f)
                logger.info("credentials.json is valid JSON")
            except json.JSONDecodeError as e:
                logger.error(f"credentials.json is invalid JSON: {e}")
                sys.exit(1)
        else:
            logger.error("credentials.json not found")
            sys.exit(1)
            
        if os.path.exists('token.json'):
            logger.info("token.json found")
            try:
                with open('token.json', 'r') as f:
                    json.load(f)
                logger.info("token.json is valid JSON")
            except json.JSONDecodeError as e:
                logger.error(f"token.json is invalid JSON: {e}")
                sys.exit(1)
        else:
            logger.error("token.json not found")
            sys.exit(1)
        
        config = load_config()
        exit_code = process_satellites(config)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()