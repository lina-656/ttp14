from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database

# URL подключения к базе данных
DATABASE_URL = "postgresql+asyncpg://lina:123d@localhost/todo_db"

# Создаем базовый класс для моделей
Base = declarative_base()

# Определяем модель данных Todo
class TodoModel(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    completed = Column(Boolean, default=False)

# Создаем экземпляр FastAPI
app = FastAPI()

# Создаем объект для работы с базой данных
database = Database(DATABASE_URL)

# Создаем класс для входных данных
class TodoCreate(BaseModel):
    title: str
    description: str

class TodoResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool

# Открываем соединение с базой данных:
@app.on_event("startup")
async def startup():
    await database.connect()

# Закрываем соединение с базой данных:
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/todos", response_model=TodoResponse, status_code=201)
async def create_todo(todo: TodoCreate):
    query = TodoModel.__table__.insert().values(
        title=todo.title, description=todo.description)
    todo_id = await database.execute(query)
    return {**todo.dict(), "id": todo_id, "completed": False}

@app.get("/todos/{todo_id}", response_model=TodoResponse)
async def read_todo(todo_id: int):
    query = TodoModel.__table__.select().where(TodoModel.id == todo_id)
    todo = await database.fetch_one(query)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.put("/todos/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int, todo: TodoCreate):
    query = TodoModel.__table__.select().where(TodoModel.id == todo_id)
    existing_todo = await database.fetch_one(query)
    if existing_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    update_query = TodoModel.__table__.update().where(TodoModel.id == todo_id).values(
        title=todo.title, description=todo.description)
    await database.execute(update_query)
    return {**existing_todo, **todo.dict()}

@app.delete("/todos/{todo_id}", status_code=204)
async def delete_todo(todo_id: int):
    query = TodoModel.__table__.select().where(TodoModel.id == todo_id)
    existing_todo = await database.fetch_one(query)
    if existing_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    delete_query = TodoModel.__table__.delete().where(TodoModel.id == todo_id)
    await database.execute(delete_query)
    return {"message": "Todo deleted successfully"}
 