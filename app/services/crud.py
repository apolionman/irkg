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
    print('TESTING!!!!', response.disease_name)

    # Check if disease already exists
    query = select(DiseaseDrugScore).filter(DiseaseDrugScore.disease_name == response.disease_name)
    result = await db.execute(query)
    existing_disease = result.scalars().first()

    if existing_disease:
        return existing_disease.id

    # Create the disease record
    disease_record = DiseaseDrugScore(disease_name=response.disease_name)
    db.add(disease_record)
    await db.commit()
    await db.refresh(disease_record)

    # Add each drug information
    for drug_info in response.drugs:
        drug_record = DrugInformation(
            drug=drug_info.drug, 
            score=drug_info.score,
            rank=drug_info.rank, 
            disease_id=disease_record.id  # Ensure the drug is linked to the disease
        )
        # This adds the drug record to the database session
        db.add(drug_record)

    try:
        # Commit the drug records to the database
        await db.commit()
        # Refresh to get the latest values
        await db.refresh(disease_record)
        print(f"Drugs for {response.disease_name} saved successfully.")
    except Exception as e:
        await db.rollback()  # Rollback if there is an error
        print(f"Error saving drugs: {e}")
        raise

    # Return the disease record with associated drugs
    drugs = [DrugInfo(drug=drug.drug, score=drug.score, rank=drug.rank) for drug in disease_record.drugs]
    return DiseaseResponse(disease_name=disease_record.disease_name, drugs=drugs)