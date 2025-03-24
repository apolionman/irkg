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

class SetModelWeightSchema(str, Enum):
    rare_model_533 = "Rare Disease Model 533"
    complex_disease_model = "Complex Disease Model"

class DrugInfo(BaseModel):
    drug: str
    score: float
    rank: int

class DrugRange(BaseModel):
    _range: int

class DiseaseResponse(BaseModel):
    disease_name: str
    model: str
    drugs: List[DrugInfo]

class RelationReq(str, Enum):
    # auto = 'auto'
    indication = 'indication'
    contraindication = 'contraindication'
    off_label = 'off-label use'

class SplitName(BaseModel):
    id: int
    split_name: str

class ModelType(Enum):
    new_model = "New Model"
    full_graph = "Full Graph Model"
    pre_trained = "Pre-trained Model"

    def __str__(self):
        return self.value

class ModelSelection(str, Enum):
    new_model = 'TxGNN Explorer Model'
    rare_model = 'Rare Diasease Model'

class ModelSchema(BaseModel):
    id: int
    name: str
    model_type: ModelType

    class Config:
        from_attributes = True

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