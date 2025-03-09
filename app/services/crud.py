from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import *
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

    print('TESTING!!!!',response.disease_name)

    query = select(DiseaseDrugScore).filter(DiseaseDrugScore.disease_name == response.disease_name)
    result = await db.execute(query)
    existing_disease = result.scalars().first()

    if existing_disease:
        return existing_disease.id

    disease_record = DiseaseDrugScore(disease_name=response.disease_name)
    db.add(disease_record)
    await db.commit(disease_record)
    await db.refresh(disease_record)

    for drug_info in response.drugs:
        drug_record = DrugInformation(drug=drug_info.drug, score=drug_info.score, disease_id=disease_record.id)
        db.add(drug_record)

    await db.commit(drug_record)
    await db.refresh(drug_record)

    return disease_record.id