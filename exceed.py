students = {
    "1234": {
        "name": "Boom",
        "age": 20
    }
}

@app.get("/all/student")
def all_student():
    return {
        "students": students
    }

@app.get("/find_name/student/{student_id}")
def find_name_by_id(student_id: str):
    return {
        "name": students[student_id]["name"]
    }

@app.get("/find_age/student/{student_id}")
def find_name_by_id(student_id: str):
    return {
        "age": students[student_id]["age"]
    }

@app.post("/add/student/{student_id}/{name}")
def add_student(student_id: str, name: str, age: Optional[int] = None):
    students[student_id] = {
        "name": name,
        "age": age
    }
    return {
        "result": "OK",
        "student_id": student_id,
        "name": name,
        "age": age
    }