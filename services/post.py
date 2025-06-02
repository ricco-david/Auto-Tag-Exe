import requests
from datetime import datetime, timedelta

# Generate a page access token
# def generate_page_access_token(access_token, page_id):
#   url = f"https://pages.fm/api/v1/pages/{page_id}/generate_page_access_token"

#   headers = {
#       "Content-Type": "application/json"
#   }

#   params = {
#       "access_token": access_token
#   }

#   try:
#       response = requests.post(url, headers=headers, params=params)
#       response.raise_for_status()  # Raises error for bad status codes
#       data = response.json()
#     #   print("✅ Page Access Token Generated:")
#       return data.get("page_access_token",None)

#   except requests.exceptions.HTTPError as errh:
#       print("❌ HTTP Error:", errh)
#       print("Response:", response.text)
#   except Exception as e:
#       print("⚠️ Error:", str(e))
#   return None




def tagging(from_id, page_id, access_token, tag_id_to_add):
  conversation_id = f"{page_id}_{from_id}"

  toggle_tag_url = (
                    f"https://pages.fm/api/v1/pages/{page_id}/conversations/"
                    f"{conversation_id}/toggle_tag?access_token={access_token}"
              )
  payload = {
      "tag_id": tag_id_to_add,
      "value": 1,
      "psid": from_id,
      "tag[id]": tag_id_to_add,
  }

  # Send POST request
  headers = {}
  try:
      response = requests.request("POST", toggle_tag_url, headers=headers, data=payload)

      # Check response status
      if response.status_code == 200:
          # Update progress bar value
          # progress_bar["value"] += 1
          return True # Return True for successful tagging
      else:
          return False # Return False for unsuccessful tagging
  except requests.exceptions.ReadTimeout:
      try: 
          response = requests.request("POST", toggle_tag_url, headers=headers, data=payload)

          # Check response status
          if response.status_code == 200:
              # Update progress bar value
              # progress_bar["value"] += 1
              return True # Return True for successful tagging
          else:
              return False # Return False for unsuccessful tagging
      except requests.exceptions.ReadTimeout:
          print("Connection Timeout", "Failed to connect to the server. Please check your internet connection or the page. Try again later.")
          return False




def tagging(from_id, page_id, access_token, tag_id_to_add):
  conversation_id = f"{page_id}_{from_id}"

  toggle_tag_url = (
                    f"https://pages.fm/api/v1/pages/{page_id}/conversations/"
                    f"{conversation_id}/toggle_tag?access_token={access_token}"
              )
  payload = {
      "tag_id": tag_id_to_add,
      "value": 1,
      "psid": from_id,
      "tag[id]": tag_id_to_add,
  }

  # Send POST request
  headers = {}
  try:
      response = requests.request("POST", toggle_tag_url, headers=headers, data=payload)

      # Check response status
      if response.status_code == 200:
          # Update progress bar value
          # progress_bar["value"] += 1
          return True # Return True for successful tagging
      else:
          return False # Return False for unsuccessful tagging
  except requests.exceptions.ReadTimeout:
      try: 
          response = requests.request("POST", toggle_tag_url, headers=headers, data=payload)

          # Check response status
          if response.status_code == 200:
              # Update progress bar value
              # progress_bar["value"] += 1
              return True # Return True for successful tagging
          else:
              return False # Return False for unsuccessful tagging
      except requests.exceptions.ReadTimeout:
          print("Connection Timeout", "Failed to connect to the server. Please check your internet connection or the page. Try again later.")
          return False