from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

class DiseaseDrugScore(Base):
    __tablename__ = "disease_drug_score"

    id = Column(Integer, primary_key=True, index=True)
    disease_name = Column(String, index=True)

    # Define a relationship with DrugInfo
    drugs = relationship("DrugInformation", back_populates="disease", cascade="all, delete-orphan")

class DrugInformation(Base):
    __tablename__ = "drug_info"

    id = Column(Integer, primary_key=True, index=True)
    drug = Column(String, index=True)
    score = Column(Float)

    disease_id = Column(Integer, ForeignKey("disease_drug_score.id"))
    disease = relationship("DiseaseDrugScore", back_populates="drugs")

# class GeneProtein(Base):
#     __tablename__ = "gene_protein"

#     id = Column(Integer, primary_key=True, index=True)
#     gene_name = Column(String, index=True)

#     # Define a relationship with DrugInfo
#     drugs = relationship("DrugInformation", back_populates="disease", cascade="all, delete-orphan")