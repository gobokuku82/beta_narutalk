"""
File Upload API
파일 업로드 및 관리 엔드포인트
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import shutil
import uuid
import mimetypes
import logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Upload directory configuration
UPLOAD_DIR = Path("database/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed file types
ALLOWED_EXTENSIONS = {
    'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
    'spreadsheet': ['.xls', '.xlsx', '.csv'],
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
    'data': ['.json', '.xml', '.yaml']
}


class FileInfo(BaseModel):
    """파일 정보"""
    file_id: str
    original_name: str
    file_type: str
    file_size: int
    upload_date: str
    file_path: str
    metadata: Optional[Dict[str, Any]] = None


class UploadResponse(BaseModel):
    """업로드 응답"""
    success: bool
    file_id: str
    message: str
    file_info: FileInfo


# In-memory file registry (실제 환경에서는 DB 사용)
file_registry: Dict[str, FileInfo] = {}


def get_file_type(filename: str) -> str:
    """파일 타입 결정"""
    ext = Path(filename).suffix.lower()
    
    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    
    return 'unknown'


def is_allowed_file(filename: str) -> bool:
    """허용된 파일 타입 확인"""
    ext = Path(filename).suffix.lower()
    
    for extensions in ALLOWED_EXTENSIONS.values():
        if ext in extensions:
            return True
    
    return False


@router.post("/file", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None)
):
    """파일 업로드"""
    try:
        # Check file extension
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {list(ALLOWED_EXTENSIONS.keys())}"
            )
        
        # Check file size
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Generate unique file ID and path
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        safe_filename = f"{file_id}{file_ext}"
        file_path = UPLOAD_DIR / safe_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create file info
        file_info = FileInfo(
            file_id=file_id,
            original_name=file.filename,
            file_type=get_file_type(file.filename),
            file_size=file_size,
            upload_date=datetime.now().isoformat(),
            file_path=str(file_path),
            metadata={
                "description": description,
                "category": category,
                "content_type": file.content_type
            }
        )
        
        # Register file
        file_registry[file_id] = file_info
        
        logger.info(f"File uploaded: {file_id} - {file.filename}")
        
        return UploadResponse(
            success=True,
            file_id=file_id,
            message=f"File uploaded successfully: {file.filename}",
            file_info=file_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files", response_model=List[UploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    category: Optional[str] = Form(None)
):
    """여러 파일 업로드"""
    try:
        responses = []
        
        for file in files:
            # Check file extension
            if not is_allowed_file(file.filename):
                logger.warning(f"Skipping file {file.filename}: type not allowed")
                continue
            
            # Check file size
            contents = await file.read()
            file_size = len(contents)
            
            if file_size > MAX_FILE_SIZE:
                logger.warning(f"Skipping file {file.filename}: size too large")
                continue
            
            # Generate unique file ID and path
            file_id = str(uuid.uuid4())
            file_ext = Path(file.filename).suffix
            safe_filename = f"{file_id}{file_ext}"
            file_path = UPLOAD_DIR / safe_filename
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # Create file info
            file_info = FileInfo(
                file_id=file_id,
                original_name=file.filename,
                file_type=get_file_type(file.filename),
                file_size=file_size,
                upload_date=datetime.now().isoformat(),
                file_path=str(file_path),
                metadata={
                    "category": category,
                    "content_type": file.content_type
                }
            )
            
            # Register file
            file_registry[file_id] = file_info
            
            responses.append(UploadResponse(
                success=True,
                file_id=file_id,
                message=f"File uploaded: {file.filename}",
                file_info=file_info
            ))
            
            logger.info(f"File uploaded: {file_id} - {file.filename}")
        
        return responses
        
    except Exception as e:
        logger.error(f"Error uploading multiple files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file/{file_id}/info", response_model=FileInfo)
async def get_file_info(file_id: str):
    """파일 정보 조회"""
    try:
        if file_id not in file_registry:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        
        return file_registry[file_id]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file/{file_id}/download")
async def download_file(file_id: str):
    """파일 다운로드"""
    try:
        if file_id not in file_registry:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        
        file_info = file_registry[file_id]
        file_path = Path(file_info.file_path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Determine media type
        media_type = mimetypes.guess_type(file_info.original_name)[0] or "application/octet-stream"
        
        return FileResponse(
            path=file_path,
            filename=file_info.original_name,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/file/{file_id}")
async def delete_file(file_id: str):
    """파일 삭제"""
    try:
        if file_id not in file_registry:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        
        file_info = file_registry[file_id]
        file_path = Path(file_info.file_path)
        
        # Delete file from disk
        if file_path.exists():
            file_path.unlink()
        
        # Remove from registry
        del file_registry[file_id]
        
        logger.info(f"File deleted: {file_id}")
        
        return {
            "success": True,
            "message": f"File {file_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files")
async def list_files(
    file_type: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50
):
    """파일 목록 조회"""
    try:
        files = []
        
        for file_id, file_info in file_registry.items():
            # Filter by file type
            if file_type and file_info.file_type != file_type:
                continue
            
            # Filter by category
            if category and file_info.metadata.get("category") != category:
                continue
            
            files.append(file_info)
        
        # Sort by upload date (most recent first)
        files.sort(key=lambda x: x.upload_date, reverse=True)
        
        # Apply limit
        files = files[:limit]
        
        return {
            "files": files,
            "total_count": len(file_registry),
            "filtered_count": len(files)
        }
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/{file_id}")
async def analyze_file(file_id: str):
    """파일 분석 (Mock)"""
    try:
        if file_id not in file_registry:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        
        file_info = file_registry[file_id]
        
        # Mock analysis based on file type
        analysis = {
            "file_id": file_id,
            "original_name": file_info.original_name,
            "file_type": file_info.file_type,
            "analysis_date": datetime.now().isoformat()
        }
        
        if file_info.file_type == "document":
            analysis["results"] = {
                "word_count": 1234,
                "page_count": 5,
                "language": "Korean",
                "summary": "This is a pharmaceutical document containing drug information."
            }
        elif file_info.file_type == "spreadsheet":
            analysis["results"] = {
                "row_count": 150,
                "column_count": 12,
                "sheets": ["Sheet1", "Sheet2"],
                "data_types": ["numeric", "text", "date"]
            }
        elif file_info.file_type == "image":
            analysis["results"] = {
                "dimensions": "1920x1080",
                "format": "PNG",
                "size_kb": file_info.file_size / 1024,
                "detected_objects": ["chart", "text", "logo"]
            }
        else:
            analysis["results"] = {
                "message": "Analysis not available for this file type"
            }
        
        logger.info(f"File analyzed: {file_id}")
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_upload_stats():
    """업로드 통계"""
    try:
        stats = {
            "total_files": len(file_registry),
            "total_size": sum(f.file_size for f in file_registry.values()),
            "by_type": {},
            "recent_uploads": []
        }
        
        # Count by type
        for file_info in file_registry.values():
            file_type = file_info.file_type
            if file_type not in stats["by_type"]:
                stats["by_type"][file_type] = 0
            stats["by_type"][file_type] += 1
        
        # Get recent uploads
        recent = sorted(
            file_registry.values(),
            key=lambda x: x.upload_date,
            reverse=True
        )[:5]
        
        stats["recent_uploads"] = [
            {
                "file_id": f.file_id,
                "name": f.original_name,
                "date": f.upload_date
            }
            for f in recent
        ]
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting upload stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check
@router.get("/health")
async def upload_health():
    """업로드 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "file_upload",
        "upload_dir": str(UPLOAD_DIR),
        "file_count": len(file_registry)
    }