from http.client import HTTPException
from typing import Optional, List
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient

# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
import databases
import sqlalchemy

import requests

from datetime import date, datetime, timezone, timedelta


try:
    conn = MongoClient()
    print("Connected successfully!!!")
except:  
    print("Could not connect to MongoDB")

client = MongoClient("mongodb://localhost:27017/")

mydatabase = client['test_db']
mycollection = mydatabase['user']
# print(client.list_database_names())
# print(mydatabase.list_collection_names())
# if "user" in mydatabase.list_collection_names():
#       print("The collection exists.")

# dictionary to be added in the database
# record={
#     "title": 'MongoDB and Python', 
#     "description": 'MongoDB is no SQL database', 
#     "tags": ['mongodb', 'database', 'NoSQL'], 
#     "viewers": 104 
# }
  
# # inserting the data in the database
# rec = mydatabase.mycollection.insert(record)

# DATABASE_URL = "sqlite:///./test.db"

# database = databases.Database(DATABASE_URL)

# metadata = sqlalchemy.MetaData()

# members = sqlalchemy.Table(
#     "members",
#     metadata,
#     sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
#     sqlalchemy.Column("name", sqlalchemy.String),
#     sqlalchemy.Column("department", sqlalchemy.String),
# )

# engine = sqlalchemy.create_engine(
#     DATABASE_URL, connect_args={"check_same_thread": False}
# )
# metadata.create_all(engine)



my_headers = {'Authorization' : 'pk_48796740_GV9HQ8884RMWUTR624SBDMDNDSCQWWV4'}

class response_query(BaseModel):
    name: str
    members: list
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    time_used: Optional[int] = None    

class Create_member(BaseModel):
    name: str
    department: str

class Member(BaseModel):
    id: int
    name: str
    department: str

app = FastAPI()

def time_calcualte(start_date, end_date):
    date_used = end_date - start_date
    return (date_used/(1000*60*60*24)+1)*8

@app.get("/")
def root():
    return "Hello World"

# @app.on_event("startup")
# async def startup():
#     await database.connect()


# @app.on_event("shutdown")
# async def shutdown():
#     await database.disconnect()

# @app.get("/members/", response_model=List[Member])
# async def read_members():
#     query = members.select()
#     return await database.fetch_all(query)

# @app.post("/members/", response_model=Member)
# async def create_member(member: Create_member):
#     query = members.insert().values(name=member.name, department=member.department)
#     last_record_id = await database.execute(query)
#     return {**member.dict(), "id": last_record_id}



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

        # check null on start date and due date
        if ( (task["start_date"] is None ) and (task["due_date"] is None) ):            # both start and due date is null
            time_used = None
            start_date = None
            due_date = None
        elif ((task["start_date"] is not None) and (task["due_date"] is None)):         # only start date is not null       
            start_date = datetime.fromtimestamp(int(task["start_date"])/1000)
            due_date = None
            time_used = None
        elif ((task["start_date"] is None) and (task["due_date"] is not None)):         # only due date is not null
            start_date = None
            due_date = datetime.fromtimestamp(int(task["due_date"])/1000)     
            time_used = None
        else:                                                                           # both start and due date is not null
            time_used = time_calcualte(int(task["start_date"]), int(task["due_date"]))
            start_date = datetime.fromtimestamp(int(task["start_date"])/1000)
            due_date = datetime.fromtimestamp(int(task["due_date"])/1000)            

        member=[]
        for assignee in task["assignees"]:
            member.append({"username": assignee["username"], "start_date":start_date, "due_date":due_date, "time_used":time_used})
        
        tag_name =[]
        for tag in task["tags"]:
            tag_name.append(tag["name"])

        # check the same task name
        for t in result:
            if t["name"] == task["name"]:
                same_task = True
                # add member
                t["members"]+=member
                # add tag
                for tag in tag_name:
                    if tag in t["tags"]:
                        continue
                    t["tags"].append(tag)
                # compare start date and due date
                if (start_date is not None and t["start_date"] is not None):
                    if t["start_date"] > start_date:
                        t["start_date"] = start_date
                if (due_date is not None and t["due_date"] is not None):
                    if t["due_date"] < due_date:
                        t["due_date"] = due_date

        if not same_task:
            temp_dict["members"] = member
            temp_dict["start_date"] = start_date
            temp_dict["due_date"] = due_date
            # if (task["start_date"] is not None):
            #     temp_dict["start_date"] = start_date
            # if ( task["due_date"] is not None):
            #     temp_dict["due_date"] = due_date
                
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
    if result is not None:
        return result
    raise HTTPException(status_code=404, detail=f"Student {id} not found")
# print(response.json())
# print(response.headers)


@app.post('/task/{task_id}/')
def add_time_use(task_id, time):
    
    return 



@app.post('/webhook')
def webhook():
    return 

