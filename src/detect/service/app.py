import time
import uuid
from contextlib import asynccontextmanager

import joblib
import pandas as pd
from scipy.sparse import hstack
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from detect import db
from detect.config import settings
from detect.service.text_utils import clean_text

class Features(BaseModel):
    model_config = {"extra": "forbid"}
    url: str
    title: str

class Prediction(BaseModel):
    label: int
    score: float
    request_id: str
    latency_ms: float
    model_version: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    bundle = joblib.load("./src/hw4_pipeline.pkl")
    app.state.word_vec = bundle["word_vec"]
    app.state.char_vec = bundle["char_vec"]
    app.state.model = bundle["model"]
    app.state.version = "hw4-v1"
    db.init()
    yield
    app.state.model = None

app = FastAPI(title="detect-service", version="1.0", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok", "model_version": getattr(app.state, "version", "unknown")}

@app.get("/ready")
def ready():
    if getattr(app.state, "model", None) is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ready"}

@app.post("/v1/predict")
def predict(x: Features, bg: BackgroundTasks) -> Prediction:
    t0 = time.perf_counter()
    request_id = str(uuid.uuid4())
    payload = x.model_dump()
    
    text = pd.Series([clean_text(payload["title"]) + " " + clean_text(payload["url"])])
    X_word = app.state.word_vec.transform(text)
    X_char = app.state.char_vec.transform(text)
    X = hstack([X_word, X_char])
    
    label = int(app.state.model.predict(X)[0])
    score = float(app.state.model.predict_proba(X)[0, 1])
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    
    bg.add_task(db.save_prediction, request_id, payload, score, app.state.version, latency_ms)
    
    return Prediction(
        label=label,
        score=score,
        model_version=app.state.version,
        request_id=request_id,
        latency_ms=latency_ms,
    )



class BatchFeatures(BaseModel):
    model_config = {"extra": "forbid"}
    rows: list[Features] = Field(..., min_length=1, max_length=1000)

class BatchPrediction(BaseModel):
    predictions: list[Prediction]
    total_latency_ms: float

@app.post("/v1/predict/batch")
def predict_batch(batch: BatchFeatures, bg: BackgroundTasks) -> BatchPrediction:
    t0 = time.perf_counter()
    
    texts = []
    payloads = []
    for x in batch.rows:
        payload = x.model_dump()
        payloads.append(payload)
        texts.append(clean_text(payload["title"]) + " " + clean_text(payload["url"]))
        
    text_series = pd.Series(texts)
    X_word = app.state.word_vec.transform(text_series)
    X_char = app.state.char_vec.transform(text_series)
    X = hstack([X_word, X_char])
    
    labels = app.state.model.predict(X)
    scores = app.state.model.predict_proba(X)[:, 1]
    
    results = []
    for i, payload in enumerate(payloads):
        req_id = str(uuid.uuid4())
        latency_ms = round((time.perf_counter() - t0) * 1000, 2) 
        
        bg.add_task(db.save_prediction, req_id, payload, float(scores[i]), app.state.version, latency_ms)
        results.append(Prediction(
            label=int(labels[i]),
            score=float(scores[i]),
            model_version=app.state.version,
            request_id=req_id,
            latency_ms=latency_ms
        ))
        
    total_latency = round((time.perf_counter() - t0) * 1000, 2)
    return BatchPrediction(predictions=results, total_latency_ms=total_latency)