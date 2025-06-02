
import time
import datetime
from datetime import datetime, timedelta
from services import *


def worker(task_id, page_id, access_token, tagging_name, since_date, until_date, signals):
    page_id = page_id.strip()
    access_token = access_token.strip()
    tagging_name = tagging_name.strip()

    # Keep first 5 and last 4 characters, mask the rest
    masked_taskid = f"{task_id[:5]}*****{task_id[-4:]}"

    page_id = get_page_id(access_token, page_id)
    if page_id is None:
        signals.log_signal.emit(f"❌[ERROR] [pid={task_id}] Invalid Page ID: {page_id}")
        return False
    
    # === Define time range (10 days ago to yesterday's end of day, in seconds) ===
    # Set the start and end of May 2024 in UTC
    start_datetime = datetime.strptime(f"{since_date} 00:00:00", "%Y-%m-%d %H:%M:%S")
    end_datetime = datetime.strptime(f"{until_date} 23:59:59", "%Y-%m-%d %H:%M:%S")

    since = int(start_datetime.timestamp())  # in seconds
    until = int(end_datetime.timestamp())    # in seconds


    tag_order_id, tag_id_to_add = get_tag_info(tagging_name, page_id, access_token)
    

    total=0
    successful_tags = 0
    last_convo_id = None

    try:
        if page_id:
            page_access_token = get_page_access_token(access_token, page_id)

            # get_convo_v2(page_id, access_token, tag_ids[1], since, until)

            if page_access_token:
                while True:
                    # Call the function to get conversations
                    data, new_last_convo_id = get_conversations(page_access_token, page_id, since, until, last_convo_id)
                    

                    # Check If data is not None and should be a list.
                    if isinstance(data, list):

                        # count the number of conversations in the data
                        total += len(data)
                        
                        for convo in data:
                        
                            if tagging_name in [tag.get("text") if tag else None  for tag in convo.get("tags")]:
                                continue
                            else:
                                res = tagging(convo["from"].get("id"), page_id, access_token, tag_id_to_add)
                                # print("tagging result =>", res)
                                if res:
                                    successful_tags += 1
                                signals.log_signal.emit(f"[INFO] [pid={masked_taskid}] Tagged conversation: {convo['id']} | Tagging result: {res}")
                            
                            signals.total_processed.emit(task_id, f"{successful_tags}/{total}")

                    

                    if data == "continue":
                        time.sleep(1)
                        continue
                    if last_convo_id == new_last_convo_id:
                        break
                    if data is None:
                        break
                    else:
                        last_convo_id = new_last_convo_id

                    
                        

            # print(f"Total conversations: {total}")
            signals.total_processed.emit(task_id, f"{successful_tags}/{total}")
            signals.log_signal.emit(f"[INFO] Total conversations tagged: {total}")
            return True

    except Exception as e:
        signals.log_signal.emit(f"❌[ERROR] [task id={task_id}] Error in worker: {str(e)}")
        return False
        

