from terminusdb_client.woqlschema import Document, WOQLSchema, LexicalKey, Enum
from typing import Optional, List

schema = WOQLSchema()

class OntologyPhase(Enum):
    _schema = schema
    Okra = "Okra"
    Kyinna = "Kyinna"
    Nnyini = "Nnyini"
    Ahodin = "Ahodin"
    Mogya = "Mogya"

class CapabilityAnchor(Document):
    """The static 4D Anchor for a capability or intent."""
    _schema = schema
    _key = LexicalKey(["intent_hash"])
    intent_hash: str
    content: str
    phase: OntologyPhase

class PhaseState(Document):
    """The immutable Event-Sourced node capturing a discrete thermodynamic state in time."""
    _schema = schema
    timestamp: str
    anchor: CapabilityAnchor
    accumulated_energy: float
    current_action: str
    
class PropagationEdge(Document):
    """The mathematical vector mapping energy from one anchor to another."""
    _schema = schema
    source: CapabilityAnchor
    target: CapabilityAnchor
    energy_transferred: float
    timestamp: str
