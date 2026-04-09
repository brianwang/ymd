from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Nomad Island API"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "ymd_user"
    POSTGRES_PASSWORD: str = "ymd_password"
    POSTGRES_DB: str = "ymd_db"
    POSTGRES_PORT: str = "5433"
    
    SECRET_KEY: str = "supersecretkey_please_change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    
    SIGN_IN_POINTS: int = 10
    INVITER_REWARD_POINTS: int = 20
    INVITEE_REWARD_POINTS: int = 10
    FIRST_POST_POINTS: int = 30
    POST_REWARD_POINTS: int = 5
    COMMENT_REWARD_POINTS: int = 2
    DAILY_POST_REWARD_LIMIT: int = 5
    DAILY_COMMENT_REWARD_LIMIT: int = 10
    SQL_ECHO: bool = False

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
