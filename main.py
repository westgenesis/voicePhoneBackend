import os
import sqlite3
import uuid
import shutil
import time
import json
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

DATABASE_FILE = "survey.db"

def create_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS survey (
            uid TEXT PRIMARY KEY,
            age INTEGER,
            gender TEXT,
            region TEXT
        )
    ''')
    # Add new table for tracking uploads
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sentence TEXT NOT NULL,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

create_database()


@app.get("/")
async def redirect_to_index():
    return FileResponse("index.html")

@app.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    info: str = Form(...)
):
    try:
        info_data = json.loads(info)
        uid = info_data.get("uid")
        sentence = info_data.get("text")  # Get the sentence text from info

        if not uid:
            raise HTTPException(
                status_code=400,
                detail="UID is required"
            )

        # Save file to disk (existing code)
        save_path = f"/var/data/sound/{uid}"
        object_name = f"{int(time.time())}_{file.filename}"
        file_path = os.path.join(save_path, object_name)
        os.makedirs(save_path, exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Record the upload in database
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO uploads (sentence)
            VALUES (?)
        ''', (sentence,))
        conn.commit()
        conn.close()

        return {
            "filename": file.filename,
            "uid": uid,
            "message": "File uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )

from fastapi.responses import JSONResponse
VALID_ACCOUNTS = {
    "English": "password1",
    "Russian": "password2",
    "Spanish": "password3",
    "Arabic": "password4",
    "Persian": "password5",
    "BrazilianPortuguese": "password6",
    "EuropeanPortuguese": "password7",
    "Thai": "password8",
    "Indosian": "password9",
    "German": "password10",
    "French": "password11",
    "Italian": "password12",
    "Turkish": "password13",
    "Hebrew": "password14",
    "Dutch": "password15",
    "Swedish": "password16",
    "Polish": "password17",
    "Kazakh": "password18",
    "Malay": "password19",
    "Danish": "password20",
    "Norwegian": "password21",
}
@app.post("/login/")
async def login(
    username: str = Body(..., embed=True),  # 账号
    password: str = Body(..., embed=True)   # 密码
):
    if username not in VALID_ACCOUNTS:
        raise HTTPException(
            status_code=400,
            detail="Username not found"
        )

    if VALID_ACCOUNTS[username] != password:
        raise HTTPException(
            status_code=400,
            detail="Incorrect password"
        )

    return JSONResponse(
        status_code=200,
        content={"message": "Login successful", "username": username, "status": 0}
    )

@app.post("/submit-survey/")
async def submit_survey(
    age: int = Body(..., embed=True),
    gender: str = Body(..., embed=True),
    region: str = Body(..., embed=True)
):
    # 生成唯一UID
    uid = str(uuid.uuid4())

    # 插入数据到SQLite数据库
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO survey (uid, age, gender, region)
            VALUES (?, ?, ?, ?)
        ''', (uid, age, gender, region))
        conn.commit()
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    finally:
        conn.close()

    # 返回生成的UID
    return {"uid": uid}

@app.get("/get_upload_list")
async def get_upload_list():
    """
    Returns a list of all uploaded sentences from all users
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Get distinct sentences to avoid duplicates
        cursor.execute('''
            SELECT DISTINCT sentence FROM uploads
        ''')
        
        sentences = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return JSONResponse(
            status_code=200,
            content={"data": sentences}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving upload list: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)