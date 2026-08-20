from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str
    fred_s3_bucket: str
    aws_region: str = "ap-east-1"
    aws_profile: str = ""
    local_data_dir: str = "./data/fred_snapshots"

    port: int = 8000
    internal_port: int = 8080
    log_level: str = "INFO"


settings = Settings()
