from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import User
from app.scripts.txgnn_query import *

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
    print(DiseaseResponse)
    # Check if the disease_name already exists in the database
    query = select(DiseaseDrugScore).filter(DiseaseDrugScore.disease_name == response.disease_name)
    result = await db.execute(query)
    existing_disease = result.scalars().first()

    print(result)

    # If the disease exists, we can either skip or update it.
    if existing_disease:
        return existing_disease.id  # Return the existing disease ID

    # If not, create a new disease record
    disease_record = DiseaseDrugScore(disease_name=response.disease_name)
    db.add(disease_record)
    await db.commit()

    # Add the related drugs
    for drug_info in response.drugs:
        drug_record = DrugInformation(drug=drug_info.drug, score=drug_info.score, disease_id=disease_record.id)
        db.add(drug_record)

    await db.commit()

    return disease_record.id