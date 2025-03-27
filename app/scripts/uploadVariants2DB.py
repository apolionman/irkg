from app.schemas.schemas import *
from app.models.models import *
from app.services.crud import process_csv_and_store_variants
from app.core.database import async_session_maker
import asyncio

CSV_FILE_PATH = "/home/dgx/dgx_irkg_be/app/input/gene_list.csv"

async def main():
    async with async_session_maker() as db: 
        process_csv_and_store_variants(CSV_FILE_PATH, db)

if __name__ == "__main__":
    asyncio.run(main())

