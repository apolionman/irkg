from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table, Enum as SQLAlchemyEnum
from sqlalchemy.orm import declarative_base, relationship
from app.schemas.schemas import *

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

class setModelWeight(Base):
    __tablename__ = "model_type_name"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True)

    disease = relationship("DiseaseDrugScore", back_populates="model", cascade="all, delete-orphan")

class DiseaseDrugScore(Base):
    __tablename__ = "disease_drug_score"

    id = Column(Integer, primary_key=True, index=True)
    disease_name = Column(String, index=True)

    model_id = Column(Integer, ForeignKey("model_type_name.id", ondelete="CASCADE"), nullable=False)
    model = relationship("setModelWeight", back_populates="disease")
    drugs = relationship("DrugInformation", back_populates="disease", cascade="all, delete-orphan")
    

class DrugInformation(Base):
    __tablename__ = "drug_info"

    id = Column(Integer, primary_key=True, index=True)
    drug = Column(String, index=True)
    score = Column(Float)
    rank = Column(Integer, index=True)

    disease_id = Column(Integer, ForeignKey("disease_drug_score.id"))
    disease = relationship("DiseaseDrugScore", back_populates="drugs")

# Association table for many-to-many relationship between VariantInfo and Gene
variant_gene_association = Table(
    "variant_gene_association",
    Base.metadata,
    Column("variant_id", Integer, ForeignKey("gene_variant.id"), primary_key=True),
    Column("gene_id", Integer, ForeignKey("gene.id"), primary_key=True),
)

class VariantInfo(Base):
    __tablename__ = "gene_variant"

    id = Column(Integer, primary_key=True, index=True)
    variationTitle = Column(String, index=True)
    NucleotideID = Column(String, index=True)
    VariationID = Column(String, index=True)
    ProteinChange = Column(String)
    Type = Column(String)
    Condition = Column(String)
    Classification = Column(String)
    ReviewStatus = Column(String)

    # Relationships
    genes = relationship("Gene", secondary=variant_gene_association, lazy='selectin')
    consequences = relationship("Consequence", lazy='selectin')


class Gene(Base):
    __tablename__ = "gene"

    id = Column(Integer, primary_key=True, index=True)
    GeneSymbol = Column(String, unique=True, index=True)

    # Relationship
    variants = relationship("VariantInfo", secondary=variant_gene_association, back_populates="genes")

class Consequence(Base):
    __tablename__ = "consequence"

    id = Column(Integer, primary_key=True, index=True)
    consequence = Column(String, index=True)
    variant_id = Column(Integer, ForeignKey("gene_variant.id"))

    # Relationship
    variant = relationship("VariantInfo", back_populates="consequences")

class ModelDB(Base):
    __tablename__ = "model_type"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    model_type = Column(SQLAlchemyEnum(ModelType, name="model_type_enum", create_constraint=True), nullable=False)