"""Types and object definitions."""

import json
import mimetypes
from pathlib import Path
from typing import Annotated, Any, Self

import aiosqlite
from fastapi import HTTPException, UploadFile
from img_search.settings import api_settings
from PIL import Image
from pydantic import BaseModel, Field, computed_field, model_validator

DDL = [
    """
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_type TEXT NOT NULL,
        caption TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS image_tags (
        image_id INTEGER NOT NULL,
        tag TEXT NOT NULL,
        FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
        UNIQUE(image_id, tag)
    );
    """,
]


class ImageUploadMetadata(BaseModel):
    """Metadata container for image uploads."""

    caption: str | None = None
    tags: Annotated[list[str], Field(default_factory=list)]

    @model_validator(mode="before")
    @classmethod
    def validate_json(cls, data: Any) -> Any:
        """Validator for string json data (as passed in multipart form request)."""
        if isinstance(data, str):
            return cls(**json.loads(data))
        return data


class ImageMetadata(BaseModel):
    """Container for data relating to an image."""

    id: int
    content_type: str
    caption: str | None
    tags: list[str]

    @staticmethod
    def make_url(image_id: int, file_ext: str) -> str:
        """Makes urls for our scheme."""
        return f"/images/img/{image_id}{file_ext}"

    @staticmethod
    def make_filepath(image_id: int, file_ext: str) -> Path:
        """Makes urls for our scheme."""
        return api_settings.image_path.joinpath(f"{image_id}{file_ext}").relative_to(
            api_settings.image_path
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def filepath(self) -> Path:
        """Path to file."""
        file_ext = mimetypes.guess_extension(self.content_type)
        if file_ext is None:
            msg = "Could not determine file_ext from content type."
            raise ValueError(msg)
        return self.make_filepath(self.id, file_ext)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        """URL for file in current scheme."""
        file_ext = mimetypes.guess_extension(self.content_type)
        if file_ext is None:
            msg = "Could not determine file_ext from content type."
            raise ValueError(msg)
        return self.make_url(self.id, file_ext)

    @classmethod
    async def ingest_upload(
        cls,
        image: UploadFile,
        metadata: ImageUploadMetadata,
        conn: aiosqlite.Connection,
    ) -> Self:
        """Creates new image from an upload."""
        # Validate the uploaded file is an image using Pillow
        try:
            img = Image.open(image.file)
            img.verify()
        except Image.UnidentifiedImageError as e:  # type: ignore[attr-defined]
            raise HTTPException(status_code=400, detail="Invalid image format") from e
        image.file.seek(0)

        content_type = (
            image.content_type
            if image.content_type is not None
            else mimetypes.guess_type(image.filename)[0]
            if image.filename is not None
            else None
        )
        if content_type is None:
            raise HTTPException(
                status_code=400,
                detail="No filename or content type to determine MIME type.",
            )

        file_ext = (
            Path(image.filename).suffix
            if image.filename is not None
            else mimetypes.guess_extension(content_type)
            if content_type is not None
            else None
        )
        if file_ext is None:
            raise HTTPException(
                status_code=400,
                detail="No filename or content type to determine file ext.",
            )

        cursor = await conn.execute(
            """
            INSERT INTO images (content_type, caption)
            VALUES (?, ?)
            RETURNING id""",
            (image.content_type, metadata.caption),
        )
        image_id_row = await cursor.fetchone()
        if image_id_row is None:
            raise HTTPException(status_code=500)
        image_id = image_id_row[0]
        await conn.commit()

        # Associate tags with the image
        await conn.executemany(
            "INSERT INTO image_tags (image_id, tag) VALUES (?, ?)",
            [(image_id, tag) for tag in metadata.tags],
        )
        await conn.commit()

        image_meta = cls(
            id=image_id,
            content_type=content_type,
            caption=metadata.caption,
            tags=metadata.tags,
        )

        api_settings.image_path.joinpath(image_meta.filepath).write_bytes(
            await image.read()
        )

        return image_meta

    @classmethod
    async def load_from_db(cls, image_id: int, conn: aiosqlite.Connection) -> Self:
        """Loads image metadata from the database by ID."""
        # Fetch image data
        cursor = await conn.execute(
            """
            SELECT id, content_type, caption
            FROM images
            WHERE id = ?
            """,
            (image_id,),
        )
        image_row = await cursor.fetchone()

        if image_row is None:
            raise HTTPException(status_code=404, detail="Image not found")

        image_id, content_type, caption = image_row

        # Fetch tags
        cursor = await conn.execute(
            """
            SELECT tag
            FROM image_tags
            WHERE image_id = ?
            """,
            (image_id,),
        )
        tags = [row[0] for row in await cursor.fetchall()]

        return cls(
            id=image_id,
            content_type=content_type,
            caption=caption,
            tags=tags,
        )
