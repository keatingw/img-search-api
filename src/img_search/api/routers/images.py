"""Router for image endpoints."""

from typing import Annotated

import aiosqlite
from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import FileResponse
from img_search.api.utils import get_db_conn
from img_search.settings import api_settings
from img_search.types import ImageMetadata, ImageUploadMetadata

router = APIRouter(
    prefix="/images",
    tags=["images"],
)


@router.get("/list")
async def list_images(
    db: Annotated[aiosqlite.Connection, Depends(get_db_conn)],
) -> list[ImageMetadata]:
    """Lists all images in the data."""
    db.row_factory = aiosqlite.Row
    async with db.execute(
        """
        SELECT id, content_type, caption
        FROM images
        """
    ) as cur:
        image_rows = await cur.fetchall()

    async with db.execute(
        """
        SELECT image_id, tag
        FROM image_tags
        """
    ) as cur:
        image_tag_rows = await cur.fetchall()

    return [
        ImageMetadata(
            **img, tags=[t["tag"] for t in image_tag_rows if t["image_id"] == img["id"]]
        )
        for img in image_rows
    ]


@router.post("/upload")
async def upload_image(
    file: UploadFile,
    metadata: ImageUploadMetadata,
    db: Annotated[aiosqlite.Connection, Depends(get_db_conn)],
) -> ImageMetadata:
    """Uploads new image to the database."""
    return await ImageMetadata.ingest_upload(file, metadata, db)


@router.get("/img/{image_id}")
async def get_image(
    image_id: int,
    db: Annotated[aiosqlite.Connection, Depends(get_db_conn)],
) -> FileResponse:
    """Gets an image file by ID.

    Small placeholder for CDN use, just loads from local filesystem.
    """
    img_meta = await ImageMetadata.load_from_db(image_id, db)
    return FileResponse(api_settings.image_path / img_meta.filepath)
