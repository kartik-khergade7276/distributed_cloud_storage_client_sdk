
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import time, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock Distributed Cloud Storage Server")
_STORAGE: Dict[str, Dict[str, bytes]] = {}


class PutObjectRequest(BaseModel):
    bucket: str
    object_name: str
    data: str


class GetObjectRequest(BaseModel):
    bucket: str
    object_name: str


@app.get("/health")
async def health():
    return {"status": "ok", "time": time.time()}


@app.get("/buckets", response_model=List[str])
async def list_buckets():
    return list(_STORAGE.keys())


@app.post("/buckets/{bucket_name}")
async def create_bucket(bucket_name: str):
    if bucket_name in _STORAGE:
        raise HTTPException(status_code=400, detail="Bucket already exists")
    _STORAGE[bucket_name] = {}
    logger.info("Created bucket %s", bucket_name)
    return {"bucket": bucket_name}


@app.get("/objects/{bucket_name}")
async def list_objects(bucket_name: str):
    if bucket_name not in _STORAGE:
        raise HTTPException(status_code=404, detail="Bucket not found")
    return {"bucket": bucket_name, "objects": list(_STORAGE[bucket_name].keys())}


@app.post("/objects")
async def put_object(req: PutObjectRequest):
    bucket = _STORAGE.setdefault(req.bucket, {})
    bucket[req.object_name] = req.data.encode()
    logger.info("Stored object %s/%s (%d bytes)", req.bucket, req.object_name, len(req.data))
    return {"bucket": req.bucket, "object": req.object_name, "size": len(req.data)}


@app.post("/objects/get")
async def get_object(req: GetObjectRequest):
    if req.bucket not in _STORAGE:
        raise HTTPException(status_code=404, detail="Bucket not found")
    bucket = _STORAGE[req.bucket]
    if req.object_name not in bucket:
        raise HTTPException(status_code=404, detail="Object not found")
    data = bucket[req.object_name].decode()
    logger.info("Read object %s/%s (%d bytes)", req.bucket, req.object_name, len(data))
    return {"bucket": req.bucket, "object": req.object_name, "data": data}
