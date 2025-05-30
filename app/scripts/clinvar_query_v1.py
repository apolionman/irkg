import asyncio
import subprocess
from fastapi import FastAPI, HTTPException
import xml.etree.ElementTree as ET
from app.schemas.schemas import *
import re
import os
import time
from dotenv import load_dotenv

load_dotenv('.env')

API_KEY = os.getenv('API_KEY')

os.environ["PATH"] = "/usr/bin:/bin:" + os.environ["PATH"]

async def fetch_clinvar_variations(gene_name: str) -> GeneRequest:

    try:
        esearch_command = (
        f'esearch -db clinvar -query "(({gene_name}[Gene Name]) AND mol cons missense[Filter]) OR (({gene_name}[Gene Name]) AND mol cons nonsense[Filter])" |'
        f'efetch -format xml&api_key={API_KEY}'
        )
        
        process = await asyncio.create_subprocess_shell(
            esearch_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
    
        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        # Debug: Check the actual output
        # print(f"Stdout: {stdout_str}") # activate only when debugging
        if stderr_str:
            print(f"Stderr: {stderr_str}")

        if stderr_str:
            raise HTTPException(status_code=500, detail=f"NCBI query error: {stderr_str}")
        
        try:
            tree = ET.ElementTree(ET.fromstring(stdout_str))
            variation_ids = [e.text for e in tree.getroot()]
        except ET.ParseError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse XML: {str(e)} - Output: {stdout_str}")

        if not variation_ids:
            return {"message": "No variations found for the given gene"}

        clinvar_data = []
        # Construct the efetch command to fetch detailed variation info
        efetch_command = (
                f'esearch -db clinvar -query "{variation_ids}" | esummary&api_key={API_KEY}'
            )

        process = await asyncio.create_subprocess_shell(
            efetch_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
    
        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()
        
        if stderr_str:
            raise HTTPException(status_code=500, detail=f"NCBI query error: {stderr_str}")

        try:
            tree = ET.ElementTree(ET.fromstring(stdout_str))
            var_root = tree.getroot()
        except ET.ParseError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse XML: {str(e)} - Output: {stdout_str}")

        for variation in var_root.findall(".//DocumentSummary"):
            variation_title = variation.find(".//title").text
            # Use regular expression to extract the ID part (NM_018024.3)
            match = re.match(r"([A-Za-z0-9_.]+)", variation_title)
            if match:
                nucleotide_id = match.group(1)
            gene = [gene_elem.text for gene_elem in variation.findall(".//gene/symbol")]
            var_id = variation.find(".//Id").text
            protein_change = variation.find(".//protein_change").text if variation.find(".//ProteinChange") is not None else "N/A"
            pre_consequence = variation.find(".//molecular_consequence_list")
            if pre_consequence is not None:
                consequence = [elem.text for elem in pre_consequence.findall("string")]
            variation_type = variation.find(".//obj_type").text
            condition = variation.find(".//trait_name").text
            classification = variation.find(".//description").text
            review_status = variation.find(".//review_status").text

            # Store the parsed information
            clinvar_data.append({
                "VariationTitle" : variation_title,
                "NucleotideID": nucleotide_id,
                "VariationID": var_id,
                "Gene": {"GeneSymbol": gene},
                "ProteinChange": protein_change,
                "Type": variation_type,
                "Consequence": consequence,
                "Condition": condition,
                "Classification": classification,
                "ReviewStatus": review_status
            })

        return {"ClinVarSet": {"ReferenceClinVarAssertion": [{"Variation": var} for var in clinvar_data]}}

    except subprocess.CalledProcessError as e:
        return {"message": f"Error occurred while fetching data: {e.stderr}"}


def fetch_fasta(nucleotide_name: str):
    esearch_command = (
        f'efetch -db nucleotide -id {nucleotide_name} -format fasta'
    )

    try:
        # Run the esearch command to get the variation IDs
        esearch_result = subprocess.run(esearch_command, capture_output=True, shell=True, check=True,
                text=True)
        output = esearch_result.stdout
        # print(output)
        fasta_sequence = "".join(output.split("\n")[1:])
        return {
            "fasta_sequence": fasta_sequence
        }
        return esearch_result
    except subprocess.CalledProcessError as e:
        return {"message": f"Error occurred while fetching data: {e.stderr}"}
