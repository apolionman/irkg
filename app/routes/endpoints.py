from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query, status
import os
import asyncio
from uuid import uuid4
import aiofiles
import random
import string
from typing import Optional, Dict
from jose import JWTError, jwt
from app.scripts.ORFfinder import run_orffinder, parse_orf_result
from app.scripts.clinvar_query_v1 import fetch_clinvar_variations, fetch_fasta
from app.scripts.txgnn_query import txgnn_query
from app.schemas.schemas import *
from app.core.config import SECRET_KEY, ALGORITHM, oauth2_scheme, fake_users_db
from app.core.utils import get_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.crud import *
from app.core.database import get_db
from app.services.lam_feedback_layer import *
from app.services.lam_exec_layer import *
from app.services.lam_decision_layer import *

router = APIRouter()

os.environ["PATH"] = os.path.expanduser("~") + "/edirect:" + os.environ["PATH"]

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    user = get_user(fake_users_db, username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# @router.get("/protected-route")
# def protected_route(username: str = Depends(get_current_user)):
#     return {"message": f"Hello, {username}! You're authorized."}

# @router.get("/users/me")
# async def read_users_me(current_user: dict = Depends(get_current_user)):
#     return current_user

@router.post("/run_orffinder/")
async def run_orf(
    fasta_sequence: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    if not fasta_sequence and not file:
        raise HTTPException(status_code=400, detail="Either 'fasta_sequence' or 'file' is required")

    input_filename = f"input_{uuid4()}.fasta"
    output_filename = f"output_{uuid4()}.txt"

    if fasta_sequence:
        async with aiofiles.open(input_filename, "w") as f:
            await f.write(fasta_sequence)
    elif file:
        try:
            async with aiofiles.open(input_filename, "wb") as f:
                while chunk := await file.read(1024 * 1024):
                    await f.write(chunk)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, run_orffinder, input_filename, output_filename)

    if result is True:
        async with aiofiles.open(output_filename, "r") as f:
            output = await f.read()

        await loop.run_in_executor(None, os.remove, input_filename)
        await loop.run_in_executor(None, os.remove, output_filename)

        return {"message": "ORF analysis complete", "result": parse_orf_result(output)}
    else:
        raise HTTPException(status_code=500, detail="Error running ORFfinder")

@router.get("/get_clinvar_data/")
async def get_clinvar_data(
    gene: str, 
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await fetch_clinvar_variations(gene)
    
    if result.get("ClinVarSet"):
        for variation in result["ClinVarSet"]["ReferenceClinVarAssertion"]:
            variation_data = variation["Variation"]
            await create_variant(db=db, variation_data=variation_data)

    return result

@router.post("/nucleotide_fasta/")
async def nucleotide_fasta(request: NucleotideReq, current_user: dict = Depends(get_current_user)):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, fetch_fasta, request.nucleotide)
    return result

@router.get("/txgnn_query", response_model=DiseaseResponse)
async def get_txgnn_results(
    disease_name: str, 
    relation: RelationReq, 
    _range: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        results = txgnn_query(disease_name, relation, _range)
        disease_id = await save_txgnn(db, results)  # Ensure this is awaited
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

running_tasks = {}

def generate_task_id(length=6):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

@router.post("/update-gene-variants-db/{task_id}")
async def run_csv_async(
        db: AsyncSession = Depends(get_db), 
        current_user: dict = Depends(get_current_user)
    ):
    """Updating Gene Variant Database in DGX."""
    task_id = generate_task_id()
    task = asyncio.create_task(
        process_csv_and_store_variants('/home/dgx/dgx_irkg_be/app/input/gene_list.csv', db)
    )
    running_tasks[task_id] = task
    return {"message": f"CSV processing started asynchronously", "task_id": task_id}

@router.post("/cancel-task/{task_id}")
async def cancel_task(
        task_id: str,
        current_user: dict = Depends(get_current_user)
    ):
    """Cancel process task."""
    task = running_tasks.get(task_id)
    
    if not task:
        return {"message": f"No task found with ID '{task_id}'."}
    
    task.cancel()
    
    try:
        await task
    except asyncio.CancelledError:
        running_tasks.pop(task_id, None)
        return {"message": f"Task '{task_id}' has been cancelled."}
    
    running_tasks.pop(task_id, None)
    return {"message": f"Task '{task_id}' cancelled successfully."}

@router.post("/lam/")
async def process_request(
    request: ProcessRequest = Depends(),  # Handles JSON input (query)
    files: Optional[List[UploadFile]] = File(None)  # Handles file uploads separately
):
    responses = {}

    # Handle file uploads first
    if files:
        file_responses = []
        for file in files:
            file_location = f"uploads/{file.filename}"
            with open(file_location, "wb") as f:
                f.write(await file.read())

            file_responses.append(store_file_in_faiss(file_location))

        responses["file_processing"] = file_responses

    # Handle user query
    if request.query:
        decision = await decision_making_layer(request.query)
        execution_result = await execution_layer(decision)  # Run the action

        responses["workflow_action"] = decision
        responses["execution_result"] = execution_result

    return responses