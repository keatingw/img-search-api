"""Settings for modules or API."""

from pathlib import Path

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """Settings for API methods."""

    img_sqlite_path: Path = (
        Path(__file__).parents[2].joinpath("data", "imagemetadata.sqlite").resolve()
    )
    image_path: Path = Path(__file__).parents[2].joinpath("data", "images").resolve()

    model_config = SettingsConfigDict(env_file=find_dotenv())


api_settings = APISettings()
