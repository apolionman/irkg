import asyncio
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from uuid import uuid4
import shutil
import aiofiles
from ORFfinder import run_orffinder, parse_orf_result
from clinvar_query_v1 import fetch_clinvar_variations, fetch_fasta
from typing import Optional, List
from txgnn_query import txgnn_query
from schemas import *
import json


# Create FastAPI instance
app = FastAPI()

# origins = [
#     "http://localhost:5174" # front-end domain
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify ["http://yourfrontend.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.environ["PATH"] = os.path.expanduser("~") + "/edirect:" + os.environ["PATH"]

@app.post("/run_orffinder/")
async def run_orf(
    fasta_sequence: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    if not fasta_sequence and not file:
        raise HTTPException(status_code=400, detail="Either 'fasta_sequence' or 'file' is required")

    input_filename = f"input_{uuid4()}.fasta"
    output_filename = f"output_{uuid4()}.txt"

    if fasta_sequence:
        # Write FASTA sequence asynchronously
        async with aiofiles.open(input_filename, "w") as f:
            await f.write(fasta_sequence)

    elif file:
        # Save uploaded file asynchronously
        try:
            async with aiofiles.open(input_filename, "wb") as f:
                while chunk := await file.read(1024 * 1024):  # Read in chunks (1MB)
                    await f.write(chunk)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    # Run ORFfinder asynchronously using loop.run_in_executor for Python < 3.9
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, run_orffinder, input_filename, output_filename)

    if result is True:
        # Read the output file asynchronously
        async with aiofiles.open(output_filename, "r") as f:
            output = await f.read()

        # Cleanup files asynchronously
        await loop.run_in_executor(None, os.remove, input_filename)
        await loop.run_in_executor(None, os.remove, output_filename)

        return {"message": "ORF analysis complete", "result": parse_orf_result(output)}
    else:
        raise HTTPException(status_code=500, detail="Error running ORFfinder")


@app.post("/get_clinvar_data/")
async def get_clinvar_data(request: GeneRequest):
    gene_name = request.gene
    result = await fetch_clinvar_variations(gene_name)  # Await the coroutine here
    return result


@app.post("/nucleotide_fasta/")
async def nucleotide_fasta(request: NucleotideReq):
    nucleotide_name = request.nucleotide
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, fetch_fasta, nucleotide_name)
    return result


@app.get("/txgnn_query", response_model=DiseaseResponse)
async def get_txgnn_results(disease_name: str, relation: RelationReq, _range: int):
    """
    API endpoint to query TxGNN for drug scores based on disease name.
    """
    loop = asyncio.get_event_loop()
    try:
    # Convert single disease_name to a list for compatibility with txgnn_query
        results = await loop.run_in_executor(None, txgnn_query, disease_name, relation, _range)
    # print(json.dumps(results.model_dump(), indent=4))  # Debugging output
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
