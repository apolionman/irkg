import asyncio
import subprocess
from fastapi import FastAPI, HTTPException
import xml.etree.ElementTree as ET
import re
import time

API_KEY = "314d1e57cb7a1f3a8e4f6d7a7ec6634e8709"  # Replace with your actual NCBI API key

async def fetch_clinvar_variations(gene_name: str):

    try:
        esearch_command = (
        f'esearch -db clinvar -query "(({gene_name}[Gene Name]) AND mol cons missense[Filter]) OR (({gene_name}[Gene Name]) AND mol cons nonsense[Filter])" |'
        # f'esearch -db clinvar -query "{gene_name}[Gene] AND Homo sapiens[Organism]" |'
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
        
        
        try:
            tree = ET.ElementTree(ET.fromstring(stdout_str))
            variation_ids = [e.text for e in tree.getroot()]
        except ET.ParseError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse XML: {str(e)} - Output: {stdout_str}")

        # print("Variation IDs:", [e.text for e in root])

        # If no variations are found
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
            gene = variation.find(".//symbol").text
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
