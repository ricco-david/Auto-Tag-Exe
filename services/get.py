import requests
from datetime import datetime, timedelta

def get_page_id(access_token, page_id):
  url = "https://pages.fm/api/v1/pages"
  params = {
      "access_token": access_token
  }

  try:
      response = requests.get(url, params=params)
      response.raise_for_status()  # Raises error if not 2xx
      data = response.json()

      pages = data.get("categorized", {}).get("activated", [])
      for page in pages:  
        #   if page["name"].lower() == page_name.lower():
        #       page_id = page["id"]  # Set PAGE_ID value
        #       return page_id
          if page_id == page["id"]:
              return page_id

      return None
  except requests.exceptions.HTTPError as err:
      print("❌ HTTP error:", err)
      print("Response:", response.text)
  except Exception as e:
      print("⚠️ Other error:", str(e))
  return None




def get_page_access_token(access_token, page_id):
    url = "https://pages.fm/api/v1/pages"
    params = {
        "access_token": access_token
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises error if not 2xx
        data = response.json()

        pages = data.get("categorized", {}).get("activated", [])
        for page in pages:  
            if page_id == page["id"]:
                page_access_token = page.get("settings", {}).get("page_access_token")
                print(f"PAGE ACCESS TOKEN: {page_access_token}")
                return page_access_token

        return None
    except requests.exceptions.HTTPError as err:
        print("❌ HTTP error:", err)
        print("Response:", response.text)
    except Exception as e:
        print("⚠️ Other error:", str(e))
    return None


# Function to retrieve tag info based on tag name
def get_tag_info(tag_name, api_url):
    print("get_tag_info")
    try:
        # Make GET request to the API endpoint
        response = requests.get(api_url)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Check if 'settings' key is present in the response
            if 'settings' in data and 'tags' in data['settings']:
                # Iterate through the tags and find the matching tag_name
                for idx, tag in enumerate(data['settings']['tags']):
                    if tag.get('text', '').lower() == tag_name.lower():
                        return idx, tag.get('id')
                
                # If tag_name not found, return None
                return None, None
            else:
                return None, None
        else:
            return None, None
    except requests.exceptions.RequestException as e:
        if e:
            # progress_bar_label.config(text="Error")
            idx = "error"
            tag = "time_out"
            return idx, tag
        


def get_conversations(page_access_token, page_id, since, until, last_conversation_id):

  url = f"https://pages.fm/api/public_api/v2/pages/{page_id}/conversations"

  if last_conversation_id:
    params = {
        "page_access_token": page_access_token,
        "page_id": page_id,
        "since": since,
        "until": until,
        "type": ["INBOX",],
        # "tags": "70",
        "last_conversation_id":  last_conversation_id
    }
  else:
    params = {
        "page_access_token": page_access_token,
        "page_id": page_id,
        "since": since,
        "until": until,
        "type": ["INBOX",],
        # "tags": "70",
    }

  try:
      response = requests.get(url, params=params)
      response.raise_for_status()  # Raises error if not 2xx
      data = response.json()
      #print("Data:", len(data.get("conversations",[])))
      if len(data.get("conversations",[])) > 0:
        last_conversation = data["conversations"][-1]  # Get the last one
        # for conv in data.get("conversations",[]):
        #   print(" convo -->", conv)
        return data.get("conversations",[]), last_conversation.get("id")
      else:
        return None, None

  except requests.exceptions.HTTPError as err:
      print("❌ HTTP error:", err)
      print("Response:", response.text)
      return "continue", None
  except Exception as e:
      print("⚠️ Other error:", str(e))
  return None, None





# Function to retrieve tag info based on tag name
def get_tag_info(tag_name, page_id, access_token):
    # API URL to retrieve tag info
    api_url = f"https://pancake.ph/api/v1/pages/{page_id}/settings?access_token={access_token}"
    try:
        # Make GET request to the API endpoint
        response = requests.get(api_url)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Check if 'settings' key is present in the response
            if 'settings' in data and 'tags' in data['settings']:
                # Iterate through the tags and find the matching tag_name
                for idx, tag in enumerate(data['settings']['tags']):
                    if tag.get('text', '').lower() == tag_name.lower():
                        return idx, tag.get('id')
                
                # If tag_name not found, return None
                return None, None
            else:
                return None, None
        else:
            return None, None
    except requests.exceptions.RequestException as e:
        if e:
            # progress_bar_label.config(text="Error")
            idx = "error"
            tag = "time_out"
            return idx, tag



