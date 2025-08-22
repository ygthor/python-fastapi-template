from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8787
    DEBUG: bool = True
    LOG_LEVEL: str = "info"

    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_HOST: str = "http://localhost:11434"

    
    MYSQL_URL: str="mysql+mysqlconnector://name:dbpassword@localhost/db_name"


    JWT_SECRET: str="supersecretjwt"
    DEVELOPER_TOKEN: str="dev-secret-token"
    EASY_OCR_CACHE_PATH: str="xxxxx"
    API_ROOT_PATH: str="/api"

    GOOGLE_APPLICATION_CREDENTIALS: str=""
    GOOGLE_PROJECT_NAME: str=""
    GOOGLE_PROJECT_LOCATION: str=""
    GOOGLE_GEMINI_MODEL: str=""
    

    class Config:
        env_file = ".env"

settings = Settings()
