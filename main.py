import uvicorn 
import json 
from fastapi import FastAPI
from utils.database import execute_query_json

app = FastAPI()

@app.get("/")
async def root():
    query= "select * from pokequeue.messages"
    result = await execute_query_json(query)
    result_dict = json.loads(result)
    return result_dict 

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)