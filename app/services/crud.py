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

async def save_txgnn(db: AsyncSession, response: DiseaseResponse):
    async with db.begin():  # Start a transaction
        # Check if the disease already exists
        query = select(DiseaseDrugScore).filter(DiseaseDrugScore.disease_name == response.disease_name)
        result = await db.execute(query)
        existing_disease = result.scalars().first()

        if existing_disease:
            return existing_disease.id
        
        # Create and add the disease record
        disease_record = DiseaseDrugScore(disease_name=response.disease_name)
        db.add(disease_record)

        # Wait to commit until all operations are completed
        # Refresh to get the generated ID of the disease record
        await db.commit()  # Explicit commit for disease record
        await db.refresh(disease_record)  # Refresh the disease record to get the correct ID

        # Add the drug records, linking them to the newly created disease record
        for drug_info in response.drugs:
            drug_record = DrugInformation(
                drug=drug_info.drug,
                score=drug_info.score,
                rank=drug_info.rank,
                disease_id=disease_record.id  # Link drug record with disease_id
            )
            db.add(drug_record)

        # The commit is performed here to include drug records too
        await db.commit()

    # Return the disease ID after committing everything
    return disease_record.id


   
