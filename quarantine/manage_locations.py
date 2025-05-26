from bird_tracker import BirdSightingTracker
import argparse

def main():
    parser = argparse.ArgumentParser(description='Manage bird tracking locations')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add location command
    add_parser = subparsers.add_parser('add', help='Add a new location')
    add_parser.add_argument('name', help='Location name')
    add_parser.add_argument('latitude', type=float, help='Latitude')
    add_parser.add_argument('longitude', type=float, help='Longitude')
    add_parser.add_argument('--radius', type=float, default=50, help='Search radius in miles')
    
    # Change location command
    change_parser = subparsers.add_parser('change', help='Change active location')
    change_parser.add_argument('name', help='Location name to activate')
    
    args = parser.parse_args()
    tracker = BirdSightingTracker()
    
    try:
        if args.command == 'add':
            result = tracker.add_location(args.name, args.latitude, args.longitude, args.radius)
            print(result)
        elif args.command == 'change':
            result = tracker.change_location(args.name)
            print(result)
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    main() 