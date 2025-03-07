from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import *
from app.scripts.txgnn_query import *
import logging

logging.basicConfig(level=logging.DEBUG)

async def get_user(db: AsyncSession, user_id: int):

    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, name: str, email: str, password: str):

    new_user = User(name=name, email=email, password=password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def save_txgnn(db: AsyncSession, response: DiseaseResponse):
    # Check if the disease already exists
    query = select(DiseaseDrugScore).filter(DiseaseDrugScore.disease_name == response.disease_name)
    result = await db.execute(query)
    existing_disease = result.scalars().first()

    if existing_disease:
        logging.debug(f"Disease {response.disease_name} already exists with ID {existing_disease.id}")
        return existing_disease.id  # Return existing disease ID

    # If disease doesn't exist, create a new disease record
    disease_record = DiseaseDrugScore(disease_name=response.disease_name)
    db.add(disease_record)
    
    try:
        await db.commit()  # Commit to get the disease id
        await db.refresh(disease_record)  # Refresh to get the id populated
        logging.debug(f"New disease {response.disease_name} added with ID {disease_record.id}")
    except Exception as e:
        logging.error(f"Error committing disease: {e}")
        return None

    # Add the drugs with the newly created disease_id
    for drug_info in response.drugs:
        drug_record = DrugInformation(drug=drug_info.drug, score=drug_info.score, disease_id=disease_record.id)
        db.add(drug_record)

    try:
        await db.commit()  # Commit the drugs to the database
        logging.debug(f"Drugs for disease {response.disease_name} committed successfully.")
    except Exception as e:
        logging.error(f"Error committing drugs: {e}")
        return None

    return disease_record.id