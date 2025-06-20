import requests
from datetime import datetime

# --- Function: Get Page Access Token ---
def get_page_access_token(access_token, page_id):
    """
    Returns the page access token for a specific page_id.
    """
    url = "https://pages.fm/api/v1/pages"
    params = {"access_token": access_token}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        activated_pages = data.get("categorized", {}).get("activated", [])
        for page in activated_pages:
            if page.get("id") == page_id:
                return page.get("settings", {}).get("page_access_token", None)
    except requests.exceptions.RequestException as err:
        print(f"Error fetching page access token: {err}")
    return None

# --- Function: Get Filtered Conversations and Send Replies ---
def get_page_conversations(page_id, page_access_token, access_token, since_input=None, until_input=None, target_phones=None, auto_reply_message=None):
    """
    Returns filtered conversations for a page and sends replies if needed.
    """
    url = f"https://pages.fm/api/public_api/v2/pages/{page_id}/conversations"
    params = {"page_access_token": page_access_token}
    since_dt = datetime.strptime(since_input, "%Y-%m-%d %H:%M:%S") if since_input else None
    until_dt = datetime.strptime(until_input, "%Y-%m-%d %H:%M:%S") if until_input else None
    if target_phones is None:
        target_phones = set()
    else:
        target_phones = set(target_phones)
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        conversations = response.json().get("conversations", [])
        matching_results = []
        for convo in conversations:
            updated_at_str = convo.get("updated_at")
            if not updated_at_str:
                continue
            try:
                updated_at = datetime.fromisoformat(updated_at_str)
            except ValueError:
                continue
            if (since_dt and updated_at < since_dt) or (until_dt and updated_at > until_dt):
                continue
            if convo.get("has_phone") and convo.get("recent_phone_numbers"):
                customer_name = convo.get("from", {}).get("name", "Unknown")
                conversation_id = convo.get("id", "N/A")
                for phone_obj in convo["recent_phone_numbers"]:
                    phone = phone_obj.get("phone_number")
                    if phone and phone in target_phones:
                        print(f"MATCH FOUND! {customer_name} - {phone} (Conversation ID: {conversation_id})")
                        # Send reply
                        if auto_reply_message:
                            reply_response = send_reply_message(
                                page_id=page_id,
                                conversation_id=conversation_id,
                                access_token=access_token,
                                message_text=auto_reply_message
                            )
                            print("Reply Sent Response:", reply_response)
                        matching_results.append({
                            "page_name": page_id,  # page_name not available here
                            "customer_name": customer_name,
                            "phone_number": phone,
                            "conversation_id": conversation_id
                        })
        return matching_results
    except requests.exceptions.RequestException as err:
        print(f"Error fetching conversations for page {page_id}: {err}")
        return []

# --- Function: Send Reply Message ---
def send_reply_message(page_id, conversation_id, access_token, message_text):
    url = f"https://pages.fm/api/v1/pages/{page_id}/conversations/{conversation_id}/messages"
    params = {"access_token": access_token}
    payload = {
        "action": "reply_inbox",
        "message": message_text
    }
    try:
        response = requests.post(url, params=params, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        print(f"Error sending message: {err}")
        return {"error": str(err)}

# --- Function: Process All Pages ---
def process_all_pages(access_token, target_phones, auto_reply_message, since_input, until_input):
    """
    Loops through all pages, calls get_page_conversations for each.
    """
    # Get all pages
    url = "https://pages.fm/api/v1/pages"
    params = {"access_token": access_token}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        activated_pages = data.get("categorized", {}).get("activated", [])
        for i, page in enumerate(activated_pages, start=1):
            page_id = page.get("id")
            page_name = page.get("name")
            page_access_token = page.get("settings", {}).get("page_access_token", None)
            if not page_access_token:
                print(f"[WARNING] No page access token for page {page_name} ({page_id})")
                continue
            print(f"Processing Page: {page_name} ({page_id})")
            matches = get_page_conversations(
                page_id=page_id,
                page_access_token=page_access_token,
                access_token=access_token,
                since_input=since_input,
                until_input=until_input,
                target_phones=target_phones,
                auto_reply_message=auto_reply_message
            )
            if matches:
                for m in matches:
                    print(f"Matched: {m['customer_name']} - {m['phone_number']} (Conversation ID: {m['conversation_id']})")
            else:
                print(f"No matches found for page {page_name}.")
    except requests.exceptions.RequestException as err:
        print(f"Error processing all pages: {err}")
