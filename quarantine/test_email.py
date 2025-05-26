import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

def test_email():
    """Test email configuration by sending a test email"""
    try:
        load_dotenv()
        email_config = {
            'smtp_server': os.getenv('SMTP_SERVER'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'sender_email': os.getenv('SMTP_USER'),
            'sender_password': os.getenv('SMTP_PASSWORD'),
            'recipient': os.getenv('RECIPIENT_EMAIL')
        }

        msg = MIMEText("This is a test email from your Bird Tracker application.")
        msg['Subject'] = 'Bird Tracker Email Test'
        msg['From'] = email_config['sender_email']
        msg['To'] = email_config['recipient']
        
        print(f"Connecting to {email_config['smtp_server']}:{email_config['smtp_port']}")
        with smtplib.SMTP(email_config['smtp_server'], 
                         email_config['smtp_port']) as server:
            server.starttls()
            print("Logging in...")
            server.login(email_config['sender_email'], 
                        email_config['sender_password'])
            print("Sending email...")
            server.send_message(msg)
        
        print("Test email sent successfully!")
        return True
    except Exception as e:
        print(f"Error sending test email: {str(e)}")
        return False

if __name__ == "__main__":
    test_email() 