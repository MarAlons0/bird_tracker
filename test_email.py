from bird_tracker import BirdSightingTracker

def main():
    try:
        tracker = BirdSightingTracker()
        print("Testing email configuration...")
        success = tracker.test_email_configuration()
        
        if success:
            print("\nEmail test successful!")
            print(f"Check {tracker.email_config['recipient']} for the test email.")
        else:
            print("\nEmail test failed.")
            
    except Exception as e:
        print(f"Error during test: {str(e)}")

if __name__ == "__main__":
    main() 