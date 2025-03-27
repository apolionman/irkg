from app.schemas.schemas import *
from sqlalchemy.orm import Session
from app.models.models import *
from app.services.crud import process_csv_and_store_variants
from app.core.database import async_session_maker
import asyncio
from app.scripts.txgnn_query import get_node_id_by_name, get_drug_id

CSV_FILE_PATH = "/home/dgx/dgx_irkg_be/app/input/gene_list.csv"

async def main():
    async with async_session_maker() as db: 
        process_csv_and_store_variants('/home/dgx/dgx_irkg_be/app/input/gene_list.csv', db)

if __name__ == "__main__":
    asyncio.run(main())

