# app/config.py
from pydantic_settings import BaseSettings
import os 
from dotenv import load_dotenv


load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.getenv("ALGORITHM", "HS256")



class Settings(BaseSettings):
    app_name: str = "Task Manager API"
    debug: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()