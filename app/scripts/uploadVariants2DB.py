from app.schemas.schemas import *
from app.models.models import *
from app.scripts.clinvar_query_v1 import *
from app.services.crud import process_csv_and_store_variants, create_variant
from app.core.database import async_session_maker
import csv
import asyncio

CSV_FILE_PATH = "/home/dgx/dgx_irkg_be/app/input/gene_list.csv"

async def process_csv_and_store_variants(gene)  -> VariantSchema:
    try:
        # Fetch ClinVar variations for each gene
        response = fetch_clinvar_variations(gene)
        
        # Check if variations exist in response
        if 'ClinVarSet' in response:
            for variation_entry in response['ClinVarSet']['ReferenceClinVarAssertion']:
                variation_data = variation_entry['Variation']
                # Store variation data in the database
                print('Saving clinvar data for GENE:', gene)
                return await variation_data
        else:
            print(f"No variations found for gene {gene}")
            return None 
    except Exception as e:
        print(f"Error processing gene {gene}: {str(e)}")

async def main():
    async with async_session_maker() as db:
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)  # Read as a dictionary
            for gene in reader:
                response = process_csv_and_store_variants(gene['node_name'])
                if response:
                    await create_variant(db, response)

if __name__ == "__main__":
    asyncio.run(main())