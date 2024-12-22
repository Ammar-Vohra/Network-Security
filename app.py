import os
import sys
import certifi
import pymongo
import pandas as pd

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.pipeline.training_pipeline import TrainingPipeline
from networksecurity.utils.main_utils.utils import load_object
from networksecurity.constants.training_pipeline import DATA_INGESTION_DATABASE_NAME, DATA_INGESTION_COLLECTION_NAME
from networksecurity.utils.ml_utils.model.estimator import NetworkModel


from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, Request
from uvicorn import run as app_run
from fastapi.responses import Response
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="./templates")

from dotenv import load_dotenv
load_dotenv()

# MongoDB Configuration
mongo_db_url = os.getenv("MONGO_DB_URL")
print(mongo_db_url)

ca = certifi.where()
client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)
database = client[DATA_INGESTION_DATABASE_NAME]
collection = database[DATA_INGESTION_COLLECTION_NAME]

# FastAPI Application
app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/", tags=["authentication"])
async def index():
    return RedirectResponse(url="/docs")

@app.get("/train")
async def train():
    try:
        training_pipeline = TrainingPipeline()
        training_pipeline.run_pipeline()
        return Response("Training successful..")
    except Exception as e:
        raise NetworkSecurityException(e, sys)
    

@app.post("/predict")
async def predict(request:Request, file:UploadFile=File(...)):
    try:
        df = pd.read_csv(file.file)

        preprocessor = load_object("final_models/preprocessor.pkl")
        model = load_object("final_models/model.pkl")

        network_model = NetworkModel(preprocessor=preprocessor, model=model)
        print(df.iloc[0])

        y_pred = network_model.predict(df)
        print(y_pred)

        df["predicted_column"] = y_pred
        print(df["predicted_column"])
        df.to_csv("predicted_output/output.csv")

        table_html = df.to_html(classes="table table-striped")

        return templates.TemplateResponse("table.html", {"request": request, "table": table_html} )



    except Exception as e:
        raise NetworkSecurityException(e,sys)




if __name__ == "__main__":
    app_run(app, host="127.0.0.1", port=8000)
