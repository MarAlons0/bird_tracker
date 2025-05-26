from bird_tracker import BirdSightingTracker

def main():
    print("Initializing Bird Tracker...")
    tracker = BirdSightingTracker()
    
    print("Generating daily report...")
    report = tracker.generate_daily_report()
    
    print("Report generation complete!")
    print(report)

if __name__ == "__main__":
    main() 