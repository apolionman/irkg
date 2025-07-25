from fastapi import APIRouter, Depends
from app.core.database import get_db
from typing import List, Dict
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from txgnn import TxData, TxGNN, TxEval
import json
from app.schemas.schemas import *
from sqlalchemy.orm import Session
from app.models.models import *
from app.services.crud import save_txgnn
from app.core.database import async_session_maker
import csv
import asyncio
from app.scripts.txgnn_query import get_node_id_by_name, get_drug_id

CSV_FILE_PATH = "/app/TxGNN/data/complete_disease_data.csv"
_range = 200

TxD = TxData(data_folder_path='/app/TxGNN/data')
TxD.prepare_split(split='full_graph', seed=42)
TxG = TxGNN(data=TxD, 
                weight_bias_track=False,
                proj_name='TxGNN',
                exp_name='TxGNN',
                device='cpu'
                )


TxG.load_pretrained('/app/TxGNN/New_model')
TxE = TxEval(model=TxG)

def txgnn_get(disease) -> DiseaseResponse:
    disease_idx = get_node_id_by_name(disease)
    results = TxE.eval_disease_centric(disease_idxs=disease_idx, 
                                relation='indication',
                                show_plot=False, 
                                verbose=False,
                                save_result=False,
                                return_raw=False,
                                # save_name=save_path
                                )

    limited_result = results.iloc[0]['Prediction'].copy()
    ranked_result = results.iloc[0]['Ranked List'].copy()
    max_score = max(limited_result.items(), key=lambda x: x[1])[1]
    min_score = min(limited_result.items(), key=lambda x: x[1])[1]
    threshold = 47
    if float(max_score) == float(min_score):
        # Avoid division by zero: assign a default value or skip normalization
        normalized_predictions = {
            drug: 0.0 for drug in limited_result
        }
    else:
        normalized_predictions = {
            drug: (float(score) - float(min_score)) / (float(max_score) - float(min_score))
            for drug, score in limited_result.items()
        }
    ranked_range = ranked_result[:_range]

    drugs_info = []
    for drug in ranked_range:
        score = normalized_predictions.get(get_drug_id(drug), None)
        # Append drug with the rank and score
        drugs_info.append(DrugInfo(drug=drug, score=score, rank=0))  # Temporary 'None' for rank

    # Sort drugs by score in descending order and assign ranks
    sorted_drugs_info = sorted(drugs_info, key=lambda x: x.score, reverse=True)
    for i, drug in enumerate(sorted_drugs_info):
        drug.rank = i + 1  # Rank starts from 1

    # Prepare the response object with the disease name and the list of drugs with scores and ranks
    response = DiseaseResponse(
        disease_name=results.iloc[0]['Name'] if isinstance(results.iloc[0]['Name'], list) else results.iloc[0]['Name'],
        drugs=sorted_drugs_info,
        model='complex_disease_model'
    )
    return response

async def main():
    async with async_session_maker() as db: 
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)  # Read as a dictionary
            for row in reader:
                results = txgnn_get(row['node_name'])
                await save_txgnn(db, results)
                print('Disease and drug score saved for disease:', row['node_name'])

if __name__ == "__main__":
    asyncio.run(main())

