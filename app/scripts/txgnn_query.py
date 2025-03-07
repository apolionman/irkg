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
        print('this is the node ids', node_ids)
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
TxD.prepare_split(split='full_graph', seed=42)

TxG = TxGNN(data=TxD, 
                weight_bias_track=False,
                proj_name='TxGNN',
                exp_name='TxGNN',
                device='cpu'
                )
# TxG.load_pretrained_graphmask('/home/dgx/dgx_irkg_be/TxGNN/graphmask_model_ckpt')
TxG.load_pretrained('/home/dgx/dgx_irkg_be/TxGNN/New_model')
TxE = TxEval(model=TxG)

def txgnn_query(disease_name: List[str], relation: str, _range: int) -> DiseaseResponse:
    disease_idx = get_node_id_by_name(disease_name)
    if relation != 'auto':
        save_path = '/home/dgx/dgx_irkg_be/TxGNN/disease_centric_eval.pkl'
        results = TxE.eval_disease_centric(disease_idxs=disease_idx, 
                                    relation=relation,
                                    show_plot=False, 
                                    verbose=False,
                                    save_result=False,
                                    return_raw=False,
                                    # save_name=save_path
                                    )

        # Load saved results
        # with open(save_path, 'rb') as f:
        #     data = pickle.load(f)

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
            # print(get_drug_id(drug))
            score = normalized_predictions.get(get_drug_id(drug), None)
            # print(score)
            drugs_info.append(DrugInfo(drug=drug, score=score))

        # Prepare the response object with the disease name and the list of drugs with scores
        response = DiseaseResponse(
            disease_name=results.iloc[0]['Name'] if isinstance(results.iloc[0]['Name'], list) else results.iloc[0]['Name'],
            drugs=drugs_info
        )
    else:
        relation = ['indication', 'contraindication', 'off-label use']

        save_paths = {
            'indication': '/home/dgx/dgx_irkg_be/TxGNN/disease_centric_eval_indi.pkl',
            'contraindication': '/home/dgx/dgx_irkg_be/TxGNN/disease_centric_eval_contrindi.pkl',
            'off-label use': '/home/dgx/dgx_irkg_be/TxGNN/disease_centric_eval_offlabel.pkl'
        }

        drugs_info_dict = {}

        for r in relation:
            TxE.eval_disease_centric(
                disease_idxs=disease_idx, 
                relation=r,
                show_plot=False, 
                verbose=True, 
                save_result=True,
                return_raw=False,
                save_name=save_paths[r]
            )

        for r in relation:
            with open(save_paths[r], 'rb') as f:
                data = pickle.load(f)

            limited_result = data.iloc[0]['Prediction'].copy()
            sorted_predictions = sorted(limited_result.items(), key=lambda x: x[1], reverse=True)
            top_100_predictions = sorted_predictions[:_range]
            max_score = max([score for drug, score in top_100_predictions])

            drugs_info = []
            for drug, score in top_100_predictions:
                percentage = (score / max_score) * 100
                drugs_info.append(DrugInfo(drug=get_drug_name(drug), score=percentage))
            
            drugs_info_dict[r] = drugs_info

        # Combine indication and off-label use, then remove contraindications
        combined_drugs = {d.drug: d for d in drugs_info_dict['indication']}
        for d in drugs_info_dict['off-label use']:
            if d.drug not in combined_drugs:
                combined_drugs[d.drug] = d

        # Remove drugs found in contraindication
        contraindicated_drugs = {d.drug for d in drugs_info_dict['contraindication']}
        final_drugs = [d for d in combined_drugs.values() if d.drug not in contraindicated_drugs]

        response = DiseaseResponse(
            disease_name=disease_name[0] if isinstance(disease_name, list) else disease_name,
            drugs=final_drugs
        )
    print(response.disease_name)
    print(response.drugs)
    # disease_id = save_to_db(response, db_session)
    # Return the dictionary representation of the response
    return response