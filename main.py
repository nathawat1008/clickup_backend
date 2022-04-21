from tracemalloc import start
from typing import Any, Optional
from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, HttpUrl

import requests

from datetime import date, datetime, timezone, timedelta

task_callback_router = APIRouter()


# access_token = "pk_48796740_GV9HQ8884RMWUTR624SBDMDNDSCQWWV4"
my_headers = {'Authorization' : 'pk_48796740_GV9HQ8884RMWUTR624SBDMDNDSCQWWV4'}

app = FastAPI()

# response = requests.get("https://api.clickup.com/api/v2/list/174754433/task", headers=my_headers)

# @task_callback_router.get(
#     "https://api.clickup.com/api/v2/list/174754433/task"
# )
# def task_notification():
#     pass

tz = timezone(timedelta(hours = 7))

class response_query(BaseModel):
    name: str
    members: list
    start_date: datetime
    due_date: datetime
    time_used: int    

def time_calcualte(start_date, end_date):
    date_used = end_date - start_date
    return (date_used/(1000*60*60*24)+1)*8

@app.get('/task')
async def get_task():
    response = requests.get("https://api.clickup.com/api/v2/list/174754433/task", headers=my_headers)
    response_json = response.json()
    tasks_list = response_json["tasks"]
    result = []
    for task in tasks_list:
        same_task=False
        temp_dict = {}
        temp_dict["name"] = task["name"]
        member=[]
        for assignee in task["assignees"]:
            member.append({"username": assignee["username"], "time_used":time_calcualte(int(task["start_date"]), int(task["due_date"]))})
        
        tag_name =[]
        for tag in task["tags"]:
            tag_name.append(tag["name"])

        # check the same task
        for t in result:
            if t["name"] == task["name"]:
                same_task = True
                t["members"]+=member


        if not same_task:
            temp_dict["members"] = member
            temp_dict["start_date"] = datetime.fromtimestamp(int(task["start_date"])/1000)
            temp_dict["due_date"] = datetime.fromtimestamp(int(task["due_date"])/1000)
            # temp_dict["time_used"] = time_calcualte(int(task["start_date"], int(task["due_date"])))
            temp_dict["tags"] = tag_name
            result.append(temp_dict)

    return result

@app.get('/task/{task_id}', response_model=response_query)
async def get_task_ID(task_id):
    response = requests.get(f"https://api.clickup.com/api/v2/task/{task_id}/", headers=my_headers)
    response = response.json()
    member = []
    for i in response["assignees"]:
        member.append(i["username"])
    due_date_time = int(response["due_date"])
    start_date_time = int(response["start_date"])
    response["due_date"] = datetime.fromtimestamp(due_date_time/1000)
    response["start_date"] = datetime.fromtimestamp(start_date_time/1000)
    date_used = due_date_time - start_date_time
    hours_used = (date_used/(1000*60*60*24)+1)*8    # ตีความว่า 1 วัน ใช้เวลา 8 ชั่วโมง
    result = response_query(**response, members=member, time_used=hours_used)
    return result

# print(response.json())
# print(response.headers)
@app.post('/webhook')
def webhook():
    return 