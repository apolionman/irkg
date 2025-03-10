from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import *
from app.scripts.txgnn_query import *
from app.schemas.schemas import *

async def get_user(db: AsyncSession, user_id: int):

    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, name: str, email: str, password: str):

    new_user = User(name=name, email=email, password=password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# Function to save disease record
async def save_disease_record(db: AsyncSession, disease_name: str):
    query = select(DiseaseDrugScore).filter(DiseaseDrugScore.disease_name == disease_name)
    result = await db.execute(query)
    existing_disease = result.scalars().first()

    if existing_disease:
        return existing_disease.id

    disease_record = DiseaseDrugScore(disease_name=disease_name)
    db.add(disease_record)
    
    await db.commit()  # Commit to save the disease record
    await db.refresh(disease_record)  # Refresh to get the ID

    return disease_record

# Function to save drug records
async def save_drug_records(db: AsyncSession, drugs: list, disease_id: int):
    for drug_info in drugs:
        drug_record = DrugInformation(
            drug=drug_info.drug,
            score=drug_info.score,
            rank=drug_info.rank,
            disease_id=disease_id  # Link drug to the disease record
        )
        db.add(drug_record)

    await db.commit()  # Commit to save all drug records

# Main function to orchestrate saving the disease and drug records
async def save_txgnn(db: AsyncSession, response: DiseaseResponse):
    # Save disease record first
    disease_record = await save_disease_record(db, response.disease_name)

    # Save drug records associated with the disease
    await save_drug_records(db, response.drugs, disease_record)

    return disease_record



   
