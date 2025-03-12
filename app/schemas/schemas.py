from pydantic import BaseModel
from enum import Enum
from typing import Optional, List
from fastapi import UploadFile


class SeqRequest(BaseModel):
    fasta_sequence: Optional[str] = None

class GeneRequest(BaseModel):
    gene: str

class NucleotideReq(BaseModel):
    nucleotide: str

class DrugInfo(BaseModel):
    drug: str
    score: float
    rank: int

class DrugRange(BaseModel):
    _range: int

class DiseaseResponse(BaseModel):
    disease_name: str
    drugs: List[DrugInfo]

class RelationReq(str, Enum):
    # auto = 'auto'
    indication = 'indication'
    contraindication = 'contraindication'
    off_label = 'off-label use'

class ModeEnum(str, Enum):
    indication = "indication"
    contradiction = "contradiction"

class VariantSchema(BaseModel):
    id: int
    variationTitle: str
    ProteinChange: str
    Type: str
    Condition: str
    Classification: str
    ReviewStatus: str

    class Config:
        orm_mode = True

class ProcessRequest(BaseModel):
    query: Optional[str] = None