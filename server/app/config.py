from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "RifaPay"
    database_url: str = "sqlite:///./rifapay_dev.db"
    jwt_secret: str = "cambiar-en-produccion"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    fernet_key: str = ""
    mp_client_id: str = ""
    mp_client_secret: str = ""
    mp_redirect_uri: str = "http://localhost:8000/api/mp/callback"
    mp_mock_mode: bool = True
    frontend_url: str = "http://localhost:5173"
    reservation_minutes: int = 30
    match_window_hours: int = 24
    expiry_check_seconds: int = 60
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
