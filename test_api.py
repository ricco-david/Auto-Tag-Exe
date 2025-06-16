from worker.auto_message_api import get_page_access_token, get_page_conversations
from datetime import datetime, timedelta

def get_date_range(start_date_str, end_date_str):
    """
    Convert date strings to datetime objects and format them for the API
    start_date_str and end_date_str should be in format "YYYY-MM-DD"
    """
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    # Set time to start of day for start date and end of day for end date
    start_date = start_date.replace(hour=0, minute=0, second=0)
    end_date = end_date.replace(hour=23, minute=59, second=59)
    
    return start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")

def test_api_functions():
    # Replace these with your actual values
    # ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiTWFyaWEgTWljYSBTYXJhYmlhIiwiZXhwIjoxNzU2Njg1MjM4LCJhcHBsaWNhdGlvbiI6MSwidWlkIjoiNmEwZjEzNGQtN2Q5Yy00MmNkLWE4NWUtMDhmOWE3ZDQ2NDZkIiwic2Vzc2lvbl9pZCI6InpnY2N3bVo5OGtjU25BTStWa3Y4WHFHT0VPQ3hUbFhoenowUEJWVysrMVUiLCJpYXQiOjE3NDg5MDkyMzgsImZiX2lkIjoiMTIyMTA2NzY0MzAwMDkzMTIyIiwibG9naW5fc2Vzc2lvbiI6bnVsbCwiZmJfbmFtZSI6Ik1hcmlhIE1pY2EgU2FyYWJpYSJ9.9OUUGmafxpnWYnslGZ_Ghe4ZYlSbiA0il8jOlwMwdNY"
    # PAGE_ID = "665336649996069"

    ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiRGVjYSBYY3MiLCJleHAiOjE3NTU3NDIwNTksImFwcGxpY2F0aW9uIjoxLCJ1aWQiOiI5OWMwMDAxYy1hYmQ0LTQ0NjQtOWFmZC0yM2RmYjhlNWI2ZTIiLCJzZXNzaW9uX2lkIjoibjJ1TktYQXFDNnVVcGlkOHhjL0J4UnNXR0F5YW1CUEk3c3UrdUFnc1JjQSIsImlhdCI6MTc0Nzk2NjA1OSwiZmJfaWQiOiIxMDg4NTEzNTQzMTExMDcwIiwibG9naW5fc2Vzc2lvbiI6bnVsbCwiZmJfbmFtZSI6IkRlY2EgWGNzIn0.zpkAwXN65vNNx20gsCSHMThUM9UBZKgU1mDRVRJpGbE"
    PAGE_ID = "725224423996883"

    # Configure your date range here
    START_DATE = "2025-06-01"  # Format: YYYY-MM-DD
    END_DATE = "2025-06-30"    # Format: YYYY-MM-DD

    # Configure target phone numbers and auto-reply message
    TARGET_PHONES = [
        "639194808420",  # Example phone number to match
        "09987654321"   # Another example phone number
    ]
    
    AUTO_REPLY_MESSAGE = """
Hello! Thank you for your message. 
We have received your contact information and will get back to you shortly.
Best regards,
Your Business Name
    """.strip()

    print("🔍 Testing API Functions...")
    print("-" * 50)

    # Test getting page access token
    print("\n1️⃣ Testing get_page_access_token:")
    page_access_token = get_page_access_token(ACCESS_TOKEN, PAGE_ID)
    
    if page_access_token:
        print(f"✅ Successfully got page access token: {page_access_token[:10]}...")
        
        # Get formatted date range
        SINCE_DATE, UNTIL_DATE = get_date_range(START_DATE, END_DATE)
        
        # Test getting conversations with specific date range and auto-reply
        print("\n2️⃣ Testing get_page_conversations with auto-reply:")
        print(f"📅 Date range: {SINCE_DATE} to {UNTIL_DATE}")
        print("\n📱 Target Phone Numbers:")
        for phone in TARGET_PHONES:
            print(f"  - {phone}")
        
        conversations = get_page_conversations(
            PAGE_ID, 
            page_access_token,
            ACCESS_TOKEN,
            since_input=SINCE_DATE,
            until_input=UNTIL_DATE,
            target_phones=TARGET_PHONES,
            auto_reply_message=AUTO_REPLY_MESSAGE
        )
        
        if conversations:
            print(f"\n📊 Total conversations fetched: {len(conversations)}")
        else:
            print("\n❌ No conversations found in the specified date range.")
    else:
        print("❌ Failed to get page access token")

if __name__ == "__main__":
    test_api_functions() 