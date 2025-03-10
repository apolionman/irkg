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
    async with db.begin():  # Start the transaction
        # Query to check if the disease already exists
        query = select(DiseaseDrugScore).filter(DiseaseDrugScore.disease_name == response.disease_name)
        result = await db.execute(query)
        existing_disease = result.scalars().first()

        if existing_disease:
            return existing_disease.id  # Return the existing disease ID if found

        # Create a new disease record if not found
        disease_record = DiseaseDrugScore(disease_name=response.disease_name)
        db.add(disease_record)

        # Commit the transaction to save the disease record
        await db.commit()  # Commit here, as the record is now added
        await db.refresh(disease_record)  # Refresh to get the ID

        # Add the drug records associated with this disease
        for drug_info in response.drugs:
            print('Drug Name:==>', drug_info)
            drug_record = DrugInformation(
                drug=drug_info.drug,
                score=drug_info.score,
                rank=drug_info.rank,
                disease_id=disease_record.id
            )
            print(drug_record)
            db.add(drug_record)

        # Commit the transaction for drugs as well
        await db.commit()  # Commit here for the drug records

    return disease_record.id  # Return the ID of the newly created disease
