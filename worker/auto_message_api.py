"""
Optimized Worker module for API functions with improved rate limiting
"""

import requests
import json
from typing import Optional, List, Dict
import re
import time
import pytz
from datetime import datetime
# Removed async imports - not needed for current implementation
import threading

PHONE_REGEX = re.compile(r"\b(\+?63\d{10}|09\d{9})\b")
PH_TZ = pytz.timezone('Asia/Manila')

class RateLimiter:
    """Thread-safe rate limiter to prevent API overload"""
    def __init__(self, max_calls_per_minute=50):
        self.max_calls = max_calls_per_minute
        self.calls = []
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        with self.lock:
            now = time.time()
            # Remove calls older than 1 minute
            self.calls = [call_time for call_time in self.calls if now - call_time < 60]
            
            if len(self.calls) >= self.max_calls:
                sleep_time = 60 - (now - self.calls[0]) + 1
                print(f"⏳ Rate limit reached, waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
                # Clean up old calls after waiting
                now = time.time()
                self.calls = [call_time for call_time in self.calls if now - call_time < 60]
            
            self.calls.append(now)

# Global rate limiter instance
rate_limiter = RateLimiter(max_calls_per_minute=45)  # Conservative limit

def normalize_phone(phone_str):
    phone = phone_str.strip()
    phone = re.sub(r"[^\d+]", "", phone)
    return phone

def find_phones_in_obj(obj, regex):
    found = []
    if isinstance(obj, dict):
        for v in obj.values():
            found.extend(find_phones_in_obj(v, regex))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(find_phones_in_obj(item, regex))
    elif isinstance(obj, str):
        found.extend(regex.findall(obj))
    return found

def extract_text_from_message(msg):
    candidates = [
        msg.get("text", ""),
        msg.get("message", ""),
        msg.get("content", ""),
        msg.get("body", ""),
        msg.get("original_message", "")
    ]
    combined = " ".join([c for c in candidates if c]).strip()
    return combined

def convert_to_unix_timestamps(since_input, until_input):
    since_dt_ph = PH_TZ.localize(datetime.strptime(since_input, "%Y-%m-%d %H:%M:%S"))
    until_dt_ph = PH_TZ.localize(datetime.strptime(until_input, "%Y-%m-%d %H:%M:%S"))
    since_dt_utc = since_dt_ph.astimezone(pytz.utc)
    until_dt_utc = until_dt_ph.astimezone(pytz.utc)
    return int(since_dt_utc.timestamp()), int(until_dt_utc.timestamp())

def extract_messages_optimized(page_id, conversation_id, customer_uuid, customer_fb_id, access_token, max_messages=None):
    """
    Optimized message extraction with better error handling
    """
    url = f"https://pages.fm/api/public_api/v1/pages/{page_id}/conversations/{conversation_id}/messages"
    
    customer_messages = []
    customer_phones_found = set()
    current_count = 0
    max_retries = 2
    retry_delay = 3
    
    # Create session for connection reuse
    session = requests.Session()
    session.headers.update({
        'Connection': 'keep-alive',
        'Accept': 'application/json'
    })
    
    if max_messages:
        print(f"🔍 Fetching up to {max_messages} messages for convo {conversation_id}...")
    else:
        print(f"🔍 Fetching ALL messages for convo {conversation_id}...")
    
    while True:
        # Stop if we've reached the message limit (only if limit is set)
        if max_messages and current_count >= max_messages:
            break
        # Rate limiting
        rate_limiter.wait_if_needed()
        
        params = {
            "customer_id": customer_uuid,
            "page_access_token": access_token,
            "current_count": current_count
        }
        
        # Add limit parameter only if max_messages is set
        if max_messages:
            params["limit"] = min(20, max_messages - current_count)

        for retry in range(max_retries):
            try:
                response = session.get(url, params=params, timeout=15)
                
                if response.status_code == 429:
                    wait_time = int(response.headers.get('Retry-After', 30))
                    print(f"⚠️ Rate limit hit, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()

                if not response.text.strip():
                    print(f"⚠️ Empty response for convo {conversation_id}")
                    break

                try:
                    data = response.json()
                    messages = data.get("messages", [])
                except json.JSONDecodeError:
                    print(f"⚠️ Invalid JSON response for convo {conversation_id}")
                    break

                if not messages:
                    print(f"✅ Finished fetching {current_count} messages")
                    break

                for msg in messages:
                    msg_from = msg.get("from", {})
                    sender_id = msg_from.get("id")
                    text = extract_text_from_message(msg)

                    if sender_id == customer_fb_id:
                        customer_messages.append(text)
                        
                        # Look for phone numbers in customer messages
                        found_phones_raw = find_phones_in_obj(msg, PHONE_REGEX)
                        if found_phones_raw:
                            for phone in found_phones_raw:
                                normalized_phone = normalize_phone(phone)
                                customer_phones_found.add(normalized_phone)

                current_count += len(messages)
                break

            except requests.exceptions.Timeout:
                print(f"⏰ Timeout for convo {conversation_id}, retrying with longer timeout...")
                try:
                    # Retry with much longer timeout
                    response = session.get(url, params=params, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    messages = data.get("messages", [])
                    if messages:
                        for msg in messages:
                            msg_from = msg.get("from", {})
                            sender_id = msg_from.get("id")
                            text = extract_text_from_message(msg)

                            if sender_id == customer_fb_id:
                                customer_messages.append(text)
                                
                                # Look for phone numbers in customer messages
                                found_phones_raw = find_phones_in_obj(msg, PHONE_REGEX)
                                if found_phones_raw:
                                    for phone in found_phones_raw:
                                        normalized_phone = normalize_phone(phone)
                                        customer_phones_found.add(normalized_phone)

                        current_count += len(messages)
                        print(f"📊 Retry successful! Fetched {current_count} messages so far...")
                    else:
                        break
                except Exception as retry_e:
                    print(f"❌ Retry failed for convo {conversation_id}: {retry_e}")
                    break
            except requests.exceptions.RequestException as e:
                print(f"❌ API error for convo {conversation_id}: {e}")
                if retry < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    break

        if not messages or (max_messages and current_count >= max_messages):
            break

    session.close()
    unique_phones = list(customer_phones_found)
    
    return {
        "messages": customer_messages, 
        "phone_numbers": unique_phones
    }

def get_page_access_token(access_token: str, page_id: str) -> Optional[str]:
    """Get page access token with rate limiting"""
    rate_limiter.wait_if_needed()
    
    url = "https://pages.fm/api/v1/pages"
    params = {"access_token": access_token}

    print(f"\n📤 Requesting pages from: {url}")

    try:
        response = requests.get(url, params=params, timeout=10)
        if response is None:
            print("❌ No response received from API")
            return None
            
        print(f"📥 Response Status: {response.status_code}")
        response.raise_for_status()

        data = response.json()
        print("✅ Pages response parsed successfully.")

        pages = data.get("categorized", {}).get("activated", [])
        for page in pages:
            if page_id == page["id"]:
                page_access_token = page.get("settings", {}).get("page_access_token")
                if page_access_token:
                    print(f"✅ PAGE ACCESS TOKEN found")
                    return page_access_token
                else:
                    print("❌ Found page but no access token in settings.")
                    return None

        print("❌ Page ID not found in activated pages.")
        return None

    except requests.exceptions.RequestException as err:
        print(f"❌ Error getting page token: {err}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None

def batch_process_conversations(conversations, page_id, page_access_token, access_token, normalized_target_phones, auto_reply_message, batch_size=5):
    """
    Process conversations in batches to reduce API load
    """
    customers_with_phones = []
    
    print(f"📊 Processing {len(conversations)} conversations in batches of {batch_size}...")
    
    for i in range(0, len(conversations), batch_size):
        batch = conversations[i:i + batch_size]
        print(f"🔄 Processing batch {i//batch_size + 1}/{(len(conversations) + batch_size - 1)//batch_size}")
        
        for convo in batch:
            customers = convo.get("customers", [])
            if customers:
                for cust in customers:
                    cust_name = cust.get('name')
                    cust_fb_id = cust.get('fb_id')
                    cust_id = cust.get('id')
                    saved_phone = cust.get('phone_number')
                    conversation_id = convo.get("id")

                    # Extract messages with NO limits (fetch all messages)
                    result = extract_messages_optimized(
                        page_id,
                        conversation_id,
                        cust_id,
                        cust_fb_id,
                        page_access_token
                    )

                    if result["phone_numbers"]:
                        customer_data = {
                            'customer_name': cust_name,
                            'customer_fb_id': cust_fb_id,
                            'saved_phone': saved_phone,
                            'phone_numbers': result["phone_numbers"],
                            'conversation_id': conversation_id,
                            'messages': result["messages"]  # Include messages in customer data
                        }
                        customers_with_phones.append(customer_data)

                        # Check for matching phones and print messages
                        if normalized_target_phones:
                            customer_phones = [normalize_phone(phone) for phone in result["phone_numbers"]]
                            matching_phones = set(customer_phones) & set(normalized_target_phones)
                            
                            if matching_phones:
                                print(f"🎯 MATCH FOUND! Customer {cust_name} has target phone number(s):")
                                for phone in matching_phones:
                                    print(f"   ✅ Matched: {phone}")
                                if auto_reply_message:
                                    print(f"🤖 AUTO-REPLY TRIGGERED for {cust_name}:")
                                    print(f"   📤 Would send: {auto_reply_message}")
                                    print(f"   🔄 Conversation ID: {conversation_id}")
                            else:
                                print(f"   ❌ No target phone match for {cust_name}")
                                customer_phones_str = ", ".join(customer_phones)
                                target_phones_str = ", ".join(normalized_target_phones)
                                print(f"   📱 Customer phones: {customer_phones_str}")
                                print(f"   🎯 Target phones: {target_phones_str}")
        
        # Small delay between batches
        if i + batch_size < len(conversations):
            time.sleep(2)
    
    return customers_with_phones

def get_page_conversations(page_id, page_access_token, access_token, last_conversation_id=None, since_input=None, until_input=None, target_phones=None, auto_reply_message=None):
    """
    Optimized conversation fetching with batch processing
    """
    url = f"https://pages.fm/api/public_api/v2/pages/{page_id}/conversations"
    
    all_conversations = []
    page_count = 0
    max_retries = 2
    retry_delay = 3

    # Create session for connection reuse
    session = requests.Session()
    session.headers.update({
        'Connection': 'keep-alive',
        'Accept': 'application/json'
    })

    # Convert date inputs
    since = None
    until = None
    if since_input and until_input:
        print(f"📅 Date Range: {since_input} to {until_input}")
        since, until = convert_to_unix_timestamps(since_input, until_input)

    # Normalize target phones
    normalized_target_phones = None
    if target_phones:
        normalized_target_phones = [normalize_phone(phone) for phone in target_phones]
        print(f"📱 Target Phone Numbers: {len(normalized_target_phones)} numbers")

    print(f"📝 Custom message available: {'Yes' if auto_reply_message else 'No'}")

    # Fetch all conversations first
    while True:
        page_count += 1
        rate_limiter.wait_if_needed()
        
        params = {"page_access_token": page_access_token}
        if last_conversation_id:
            params["last_conversation_id"] = last_conversation_id
        if since:
            params["since"] = since
        if until:
            params["until"] = until

        print(f"📤 Fetching conversations page {page_count}...")

        for retry in range(max_retries):
            try:
                response = session.get(url, params=params, timeout=15)
                if response is None:
                    print("❌ No response received from API")
                    continue
                    
                if response.status_code == 429:
                    wait_time = int(response.headers.get('Retry-After', 30))
                    print(f"⚠️ Rate limit hit, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                conversations = data.get("conversations", [])
                
                if not conversations:
                    if page_count == 1:
                        print("⚠️ No conversations found.")
                        session.close()
                        return all_conversations
                    else:
                        print(f"✅ Finished fetching {len(all_conversations)} conversations.")
                        break

                all_conversations.extend(conversations)
                last_conversation_id = conversations[-1].get("id")
                break

            except requests.exceptions.Timeout:
                print(f"⏰ Timeout fetching page {page_id}, retrying with longer timeout...")
                try:
                    # Retry with much longer timeout
                    response = session.get(url, params=params, timeout=30)
                    if response is None:
                        print("❌ No response received from API on retry")
                        continue
                        
                    response.raise_for_status()
                    data = response.json()
                    conversations = data.get("conversations", [])
                    if conversations:
                        all_conversations.extend(conversations)
                        print(f"📊 Retry successful! Fetched {len(all_conversations)} conversations so far...")
                        if len(conversations) < 60:
                            break
                        last_conversation_id = conversations[-1].get("id")
                    else:
                        break
                except Exception as retry_e:
                    print(f"❌ Retry failed for page {page_id}: {retry_e}")
                    break
            except requests.exceptions.RequestException as err:
                print(f"❌ Error fetching conversations: {err}")
                if retry < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    session.close()
                    return all_conversations
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
                if retry < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    session.close()
                    return all_conversations

        if not conversations:
            break

    session.close()

    # Process conversations in batches
    customers_with_phones = batch_process_conversations(
        all_conversations, 
        page_id, 
        page_access_token, 
        access_token,
        normalized_target_phones, 
        auto_reply_message
    )

    return all_conversations

def get_all_page_ids(access_token: str) -> List[Dict]:
    """Get all activated page IDs and their details with pagination support"""
    rate_limiter.wait_if_needed()
    
    url = "https://pages.fm/api/v1/pages"
    params = {"access_token": access_token}
    
    all_pages = []
    page_number = 1
    has_more_pages = True

    print(f"\n📤 Requesting pages from: {url}")

    while has_more_pages:
        try:
            # Add pagination parameters
            params["page"] = page_number
            params["per_page"] = 50  # Maximum pages per request
            
            print(f"\n📤 Requesting page {page_number}:")
            print(f"URL: {url}")
            print(f"Params: {params}")
            
            response = requests.get(url, params=params, timeout=10)
            print(f"📥 Response Status for page {page_number}: {response.status_code}")
            print(f"📥 Response Headers: {dict(response.headers)}")
            
            # Print raw response for debugging
            print(f"\n📥 Raw Response Text for page {page_number}:")
            print(response.text)
            
            response.raise_for_status()

            data = response.json()
            print(f"\n📥 Parsed JSON Response for page {page_number}:")
            print(json.dumps(data, indent=2))
            
            # Get pages from current response
            current_pages = data.get("categorized", {}).get("activated", [])
            if not current_pages:
                print(f"\n⚠️ No pages found in response for page {page_number}")
                print("Response structure:")
                print(f"- Has categorized: {bool(data.get('categorized'))}")
                print(f"- Categorized keys: {list(data.get('categorized', {}).keys())}")
                has_more_pages = False
                break
                
            all_pages.extend(current_pages)
            
            # Check if there are more pages
            total_pages = data.get("meta", {}).get("total_pages", 1)
            has_more_pages = page_number < total_pages
            
            if has_more_pages:
                print(f"📄 Found {len(current_pages)} pages on page {page_number}")
                page_number += 1
                # Add a small delay between page requests
                time.sleep(1)
            else:
                print(f"✅ Finished fetching all pages. Total pages found: {len(all_pages)}")

        except requests.exceptions.RequestException as err:
            print(f"\n❌ Error getting pages for page {page_number}:")
            print(f"Error type: {type(err).__name__}")
            print(f"Error message: {str(err)}")
            if hasattr(err, 'response'):
                print(f"Response status: {err.response.status_code}")
                print(f"Response text: {err.response.text}")
            break

    if all_pages:
        print(f"\n📋 Found {len(all_pages)} activated pages:")
        for page in all_pages:
            print(f"  - {page.get('name')} (ID: {page.get('id')})")
    else:
        print("\n❌ No activated pages found.")
        print("This could be due to:")
        print("1. Invalid access token")
        print("2. No pages available for the account")
        print("3. API response format changed")
        print("4. Rate limiting or other API restrictions")

    return all_pages

def check_page_limits(access_token: str) -> Dict:
    """Check the limits and pagination info for pages"""
    rate_limiter.wait_if_needed()
    
    url = "https://pages.fm/api/v1/pages"
    params = {
        "access_token": access_token,
        "page": 1,
        "per_page": 1  # Just get one page to check limits
    }

    print("\n🔍 Checking page limits...")
    print(f"URL: {url}")
    print(f"Params: {params}")

    try:
        # First, make a request without any pagination parameters to see the raw response
        print("\n🔍 Making initial request without pagination...")
        initial_response = requests.get(url, params={"access_token": access_token}, timeout=10)
        print(f"📥 Initial Response Status: {initial_response.status_code}")
        print(f"📥 Initial Response Headers: {dict(initial_response.headers)}")
        print("\n📥 Initial Raw Response Text:")
        print(initial_response.text)
        
        # Now make the paginated request
        print("\n🔍 Making paginated request...")
        response = requests.get(url, params=params, timeout=10)
        print(f"📥 Paginated Response Status: {response.status_code}")
        print(f"📥 Paginated Response Headers: {dict(response.headers)}")
        print("\n📥 Paginated Raw Response Text:")
        print(response.text)
        
        response.raise_for_status()
        
        data = response.json()
        print("\n📥 Parsed JSON Response:")
        print(json.dumps(data, indent=2))
        
        # Get activated pages from the response
        activated_pages = data.get("categorized", {}).get("activated", [])
        activated_page_ids = data.get("categorized", {}).get("activated_page_ids", [])
        
        print("\n🔍 Response Structure:")
        print(f"- Has categorized: {bool(data.get('categorized'))}")
        print(f"- Categorized keys: {list(data.get('categorized', {}).keys())}")
        print(f"- Activated pages count: {len(activated_pages)}")
        print(f"- Activated page IDs: {activated_page_ids}")
        
        # Check if we have any pages in the response
        print(f"\n🔍 Pages found in response: {len(activated_pages)}")
        if activated_pages:
            print("First page details:")
            print(json.dumps(activated_pages[0], indent=2))
        
        # Create limits based on actual page data
        limits = {
            "total_pages": len(activated_pages),
            "total_count": len(activated_pages),
            "per_page": 50,
            "current_page": 1,
            "page_ids": activated_page_ids
        }
        
        print("\n📊 Page Limits Information:")
        print(f"  - Total Pages Available: {limits['total_pages']}")
        print(f"  - Total Pages Count: {limits['total_count']}")
        print(f"  - Pages Per Request: {limits['per_page']}")
        print(f"  - Page IDs: {limits['page_ids']}")
        
        return limits
        
    except requests.exceptions.RequestException as err:
        print(f"\n❌ Error checking page limits:")
        print(f"Error type: {type(err).__name__}")
        print(f"Error message: {str(err)}")
        if hasattr(err, 'response'):
            print(f"Response status: {err.response.status_code}")
            print(f"Response text: {err.response.text}")
        return {
            "total_pages": 0,
            "total_count": 0,
            "per_page": 50,
            "current_page": 1,
            "page_ids": []
        }

def process_all_pages(access_token: str, target_phones: List[str] = None, auto_reply_message: str = None, 
                     since_input: str = None, until_input: str = None):
    """
    Process all activated pages with the given parameters
    """
    # First check page limits
    limits = check_page_limits(access_token)
    if limits["total_count"] == 0:
        print("❌ No pages available to process.")
        return

    # Get all pages with pagination
    pages = get_all_page_ids(access_token)
    if not pages:
        print("❌ No pages to process.")
        return

    print(f"\n🚀 Starting to process {len(pages)} pages...")
    print("=" * 60)

    for page in pages:
        page_id = page.get("id")
        page_name = page.get("name")
        
        print(f"\n📄 Processing Page: {page_name} (ID: {page_id})")
        print("-" * 50)

        # Get page access token
        page_access_token = get_page_access_token(access_token, page_id)
        if not page_access_token:
            print(f"❌ Skipping page {page_name} - Failed to get access token")
            continue

        # Process conversations for this page
        conversations = get_page_conversations(
            page_id,
            page_access_token,
            access_token,
            since_input=since_input,
            until_input=until_input,
            target_phones=target_phones,
            auto_reply_message=auto_reply_message
        )

        if conversations:
            print(f"✅ Processed {len(conversations)} conversations for {page_name}")
        else:
            print(f"ℹ️ No conversations found for {page_name}")

        # Add a small delay between pages to avoid rate limiting
        if page != pages[-1]:  # Don't wait after the last page
            print("⏳ Waiting 3 seconds before next page...")
            time.sleep(3)

    print("\n🎉 Finished processing all pages!")
