from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
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
    disease_record = DiseaseDrugScore(disease_name=disease_name)
    db.add(disease_record)
    
    await db.commit()  # Commit to save the disease record
    return disease_record.id

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
    query = select(DiseaseDrugScore).filter(DiseaseDrugScore.disease_name == response.disease_name)
    result = await db.execute(query)
    existing_disease = result.scalars().first()
    if existing_disease:
        return existing_disease.id

    disease_record = await save_disease_record(db, response.disease_name)
    await save_drug_records(db, response.drugs, disease_record)
    return disease_record

async def create_variant(db: AsyncSession, variation_data: dict):
    variant_info = VariantInfo(
        variationTitle=variation_data['VariationTitle'],
        NucleotideID=variation_data['NucleotideID'],
        VariationID=variation_data['VariationID'],
        ProteinChange=variation_data['ProteinChange'],
        Type=variation_data['Type'],
        Condition=variation_data['Condition'],
        Classification=variation_data['Classification'],
        ReviewStatus=variation_data['ReviewStatus'],
    )
    
    db.add(variant_info)
    await db.commit()
    await db.refresh(variant_info)
    
    for gene_symbol in variation_data['Gene']['GeneSymbol']:
        result = await db.execute(select(Gene).filter(Gene.GeneSymbol == gene_symbol))
        gene = result.scalars().first()
        if not gene:
            gene = Gene(GeneSymbol=gene_symbol)
            db.add(gene)
            await db.commit()
            await db.refresh(gene)

        variant_info.genes.append(gene)

    for consequence in variation_data['Consequence']:
        cons = Consequence(consequence=consequence, variant_id=variant_info.id)
        db.add(cons)

    await db.commit()
    await db.refresh(variant_info)

    return variant_info

async def get_variants_by_gene(db: AsyncSession, gene_name: str):
    result = await db.execute(
        select(VariantInfo)
        .join(variant_gene_association)
        .join(Gene)
        .filter(Gene.GeneSymbol == gene_name)
        .options(selectinload(VariantInfo.genes), selectinload(VariantInfo.consequences))
    )
    return result.scalars().all()