import pickle
import os
from typing import List, Dict
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from txgnn import TxData, TxGNN, TxEval
import json
from app.schemas.schemas import *
from sqlalchemy.orm import Session
from app.models.models import *
from sqlalchemy.ext.asyncio import AsyncSession

def get_node_id_by_name(input_name):
    df = pd.read_csv('/home/dgx/dgx_irkg_be/TxGNN/data/disease_sorted_nodes.csv', delimiter='\t', dtype=str)
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    df['id'] = pd.to_numeric(df['id'], errors='coerce')  # This turns invalid values into NaN
    df['id'] = df['id'].fillna(0)
    df['id'] = df['id'].astype(float)
    
    match = df[df['node_name'] == input_name]
    
    if not match.empty:
        # Return all node_ids in a list if there are multiple matches
        return match['id'].tolist()
    
    # If no exact match, use fuzzy matching
    node_names = df['node_name'].tolist()
    best_match = process.extractOne(input_name, node_names, scorer=fuzz.ratio)
    
    if best_match and best_match[1] >= 80:
        matched_name = best_match[0]
        # Return all node_ids for the best matched name
        node_ids = df[df['node_name'] == matched_name]['id'].tolist()
        # print('this is the node ids', node_ids)
        return node_ids
    return None

def get_drug_name(node_id):
    df = pd.read_csv('/home/dgx/dgx_irkg_be/TxGNN/data/drug_nodes.csv')
    result = df[df['node_id'] == node_id]
    if not result.empty:
        return result['node_name'].iloc[0]
    else:
        return None

def get_drug_id(node_name):
    df = pd.read_csv('/home/dgx/dgx_irkg_be/TxGNN/data/drug_nodes.csv')
    result = df[df['node_name'] == node_name]
    if not result.empty:
        return result['node_id'].iloc[0]
    else:
        return None
    
TxD = TxData(data_folder_path='/home/dgx/dgx_irkg_be/TxGNN/data')
TxD.prepare_split(split='complex_disease', seed=42)

TxG = TxGNN(data=TxD, 
                weight_bias_track=False,
                proj_name='TxGNN',
                exp_name='TxGNN',
                device='cpu'
                )
# TxG.load_pretrained_graphmask('/home/dgx/dgx_irkg_be/TxGNN/graphmask_model_ckpt')
# TxG.load_pretrained('/home/dgx/dgx_irkg_be/TxGNN/New_model')
# TxE = TxEval(model=TxG)

def txgnn_query(
        selectModel: str,
        disease_name: List[str], 
        relation: str, 
        _range: int) -> DiseaseResponse:
    disease_idx = get_node_id_by_name(disease_name)
    # if relation != 'auto':
    # save_path = '/home/dgx/dgx_irkg_be/TxGNN/disease_centric_eval.pkl'
    if selectModel == 'new_model':
        TxG.load_pretrained(f'/home/dgx/dgx_irkg_be/TxGNN/New_model')
        TxE = TxEval(model=TxG)
    elif selectModel == 'rare_model':
        TxG.load_pretrained_graphmask('/home/dgx/dgx_irkg_be/TxGNN/data/rare_disease_model_ckpt')
        TxE = TxEval(model=TxG)
    results = TxE.eval_disease_centric(disease_idxs=disease_idx, 
                                relation=relation,
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
        model=selectModel
    )
    return response