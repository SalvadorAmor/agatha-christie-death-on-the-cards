from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Aplicacion
    DEBUG: bool = True

    # Base de datos
    DB_HOST: str = 'localhost'
    DB_USER: str = 'postgres'
    DB_PORT: int = 5432
    DB_NAME: str = 'takehome'
    DB_PASSWORD: str = "CHANGEME"

    @property
    def db_url(self):
        return f'postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

settings = Settings(_env_file='.env')