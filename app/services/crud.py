from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from app.models.models import *
from app.scripts.txgnn_query import *
from app.schemas.schemas import *
from app.scripts.clinvar_query_v1 import fetch_clinvar_variations

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

# Main function to orchestrate saving the disease and drug records old
# async def save_txgnn(db: AsyncSession, response: DiseaseResponse):
#     query = select(DiseaseDrugScore).filter(DiseaseDrugScore.disease_name == response.disease_name)
#     result = await db.execute(query)
#     existing_disease = result.scalars().first()
#     if existing_disease:
#         return existing_disease.id

#     disease_record = await save_disease_record(db, response.disease_name)
#     await save_drug_records(db, response.drugs, disease_record)
#     return disease_record

async def save_txgnn(db: AsyncSession, response: DiseaseResponse):
    # Fetch model record
    model_query = select(setModelWeight).filter(setModelWeight.model_name == response.model)
    model_result = await db.execute(model_query)
    model_record = model_result.scalars().first()

    if not model_record:
        # Create new model if it doesn't exist
        model_record = setModelWeight(model_name=response.model)
        db.add(model_record)
        await db.commit()
        await db.refresh(model_record)

    # Ensure model_id is not None
    if not model_record.id:
        raise ValueError("Model ID could not be retrieved or created")

    # Check if disease already exists with the same model
    query = (
        select(DiseaseDrugScore)
        .filter(
            DiseaseDrugScore.disease_name == response.disease_name,
            DiseaseDrugScore.model_id == model_record.id  # Ensure filtering by model_id
        )
        .options(joinedload(DiseaseDrugScore.drugs))
    )

    result = await db.execute(query)
    existing_disease = result.scalars().first()

    if existing_disease:
        # Update existing drug records
        for drug in response.drugs:
            existing_drug = next((d for d in existing_disease.drugs if d.drug == drug.drug), None)
            if existing_drug:
                existing_drug.score = drug.score
                existing_drug.rank = drug.rank
            else:
                new_drug = DrugInformation(
                    drug=drug.drug,
                    score=drug.score,
                    rank=drug.rank,
                    disease_id=existing_disease.id
                )
                db.add(new_drug)
        await db.commit()
        return existing_disease.id

    # Create new disease record with model_id
    disease_record = DiseaseDrugScore(disease_name=response.disease_name, model_id=model_record.id)
    db.add(disease_record)
    await db.commit()
    await db.refresh(disease_record)

    # Save drug records
    for drug in response.drugs:
        new_drug = DrugInformation(
            drug=drug.drug,
            score=drug.score,
            rank=drug.rank,
            disease_id=disease_record.id
        )
        db.add(new_drug)

    await db.commit()
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

    # Explicitly initialize genes relationship before modifying
    await db.refresh(variant_info, attribute_names=['genes'])

    for gene_symbol in variation_data['Gene']['GeneSymbol']:
        result = await db.execute(select(Gene).filter(Gene.GeneSymbol == gene_symbol))
        gene = result.scalars().first()
        if not gene:
            gene = Gene(GeneSymbol=gene_symbol)
            db.add(gene)
            await db.commit()
            await db.refresh(gene)

        variant_info.genes.append(gene)

    # Similarly for consequences
    for consequence in variation_data['Consequence']:
        cons = Consequence(consequence=consequence, variant_id=variant_info.id)
        db.add(cons)

    await db.commit()
    await db.refresh(variant_info)

    return variant_info

async def process_csv_and_store_variants(csv_path: str, db: AsyncSession):
    # Read CSV
    df = pd.read_csv(csv_path)

    # Iterate over each gene_name
    for gene_name in df['node_name']:
        print('Fetching Gene:', gene_name)
        try:
            # Fetch ClinVar variations for each gene
            response = await fetch_clinvar_variations(gene_name)
            
            # Check if variations exist in response
            if 'ClinVarSet' in response:
                for variation_entry in response['ClinVarSet']['ReferenceClinVarAssertion']:
                    variation_data = variation_entry['Variation']
                    # Store variation data in the database
                    print('Saving clinvar data for GENE:', gene_name)
                    await create_variant(db, variation_data)
            else:
                print(f"No variations found for gene {gene_name}")
        except Exception as e:
            print(f"Error processing gene {gene_name}: {str(e)}")