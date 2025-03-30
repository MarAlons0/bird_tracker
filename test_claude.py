import anthropic
from configparser import ConfigParser

def test_claude():
    # Load config
    config = ConfigParser()
    config.read('/Users/Mario/Documents/bird_tracker/config.ini')
    
    # Get API key
    api_key = config['anthropic']['api_key']
    print(f"API Key found: {'Yes' if api_key else 'No'}")
    
    try:
        # Initialize Claude
        client = anthropic.Anthropic(api_key=api_key)
        
        # Simple test message
        print("Sending test message to Claude...")
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": "Please respond with 'Hello, I am working!'"
            }]
        )
        
        print("Response from Claude:")
        print(message.content)
        return True
        
    except Exception as e:
        print(f"Error testing Claude API: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    test_claude() 