from fastapi import FastAPI
from server.progress_state import progress
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from server.crawling.new_youtube_data_abstraction import (
    run_search,
    get_keyword_id
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class KeywordRequest(BaseModel):
    keyword: str

@app.post("/search")
async def search(req: KeywordRequest):

    keyword_id = get_keyword_id(req.keyword)

    result = run_search(
        req.keyword,
        keyword_id
    )

    return result

@app.get("/progress")
async def get_progress():
    return progress

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)