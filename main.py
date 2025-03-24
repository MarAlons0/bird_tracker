from bird_tracker import BirdSightingTracker
import schedule
import time

def run_daily_report():
    tracker = BirdSightingTracker()
    
    # Get species list from config
    species_list = tracker.config['target_species']['species'].split('\n')
    species_list = [s.strip() for s in species_list if s.strip()]
    
    # Generate report
    report = tracker.generate_daily_report(species_list)
    
    # Save to file
    with open(f"reports/bird_report_{time.strftime('%Y%m%d')}.txt", 'w') as f:
        f.write(report)
    
    # Send email
    if tracker.send_email_report(report):
        print("Daily report generated and emailed successfully!")
    else:
        print("Daily report generated but email sending failed.")

if __name__ == "__main__":
    # Schedule the report to run daily at 6:00 AM
    schedule.every().day.at("06:00").do(run_daily_report)
    
    while True:
        schedule.run_pending()
        time.sleep(60) 