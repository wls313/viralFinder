from crawling.new_youtube_data_abstraction import run_search
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class KeywordRequest(BaseModel):
    keyword: str

@app.post("/search")
async def search(req: KeywordRequest):
    result = run_search(req.keyword)

    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)