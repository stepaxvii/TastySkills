import os
from uuid import uuid4
from fastapi import UploadFile
from typing import Optional

class FileService:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save_upload(self, file: Optional[UploadFile]) -> Optional[str]:
        if file and file.filename:
            ext = os.path.splitext(file.filename)[1]
            unique_name = f"product_{uuid4().hex}{ext}"
            file_path = os.path.join(self.upload_dir, unique_name)
            with open(file_path, "wb") as f:
                f.write(await file.read())
            return unique_name
        return None 