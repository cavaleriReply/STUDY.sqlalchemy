from sqlalchemy import Column, Integer, String, TIMESTAMP, Float, Enum, ForeignKey, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

# Enum per i livelli ISA95
class ISA95LevelEnum(enum.Enum):
    DEFAULT = "DEFAULT"
    LEVEL_0 = "PLC" # per ora consideriamo il livello 0 plc al posto di sensors
    LEVEL_1 = "PLC"
    LEVEL_2 = "SCADA"
    LEVEL_3 = "MES"
    LEVEL_4 = "ERP"

# Enum per le relazioni di matching
class RelationType(enum.Enum):
    EQUIVALENT = "equivalent"
    BROADER = "broader"
    NARROWER = "narrower"
    DEPRECATED = "deprecated"

# Tabella ISA95
class ISA95Level(Base):
    __tablename__ = "isa95_level"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    
    # Relationships
    intents = relationship("IntentISA95Link", back_populates="isa95_level")
    entities = relationship("EntityISA95Link", back_populates="isa95_level")

# Tabella Intent
class Intent(Base):
    __tablename__ = "intent"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))  # Aumentato per più flessibilità
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    isa95_links = relationship("IntentISA95Link", back_populates="intent", cascade="all, delete-orphan")
    matches_as_a = relationship("IntentMatch", foreign_keys="IntentMatch.intent_a_id", back_populates="intent_a", cascade="all, delete-orphan")
    matches_as_b = relationship("IntentMatch", foreign_keys="IntentMatch.intent_b_id", back_populates="intent_b", cascade="all, delete-orphan")

# Tabella Entity
class Entity(Base):
    __tablename__ = "entity"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    isa95_links = relationship("EntityISA95Link", back_populates="entity", cascade="all, delete-orphan")
    matches_as_a = relationship("EntityMatch", foreign_keys="EntityMatch.entity_a_id", back_populates="entity_a", cascade="all, delete-orphan")
    matches_as_b = relationship("EntityMatch", foreign_keys="EntityMatch.entity_b_id", back_populates="entity_b", cascade="all, delete-orphan")

# Tabella di associazione Intent-ISA95 (Many-to-Many)
class IntentISA95Link(Base):
    __tablename__ = "intent_isa95_link"
    
    intent_id = Column(Integer, ForeignKey("intent.id", ondelete="CASCADE"), nullable=False)
    isa95_id = Column(Integer, ForeignKey("isa95_level.id", ondelete="CASCADE"), nullable=False)
    
    # Chiave primaria composita
    __table_args__ = (
        PrimaryKeyConstraint('intent_id', 'isa95_id'),
    )
    
    # Relationships
    intent = relationship("Intent", back_populates="isa95_links")
    isa95_level = relationship("ISA95Level", back_populates="intents")

# Tabella di associazione Entity-ISA95 (Many-to-Many)
class EntityISA95Link(Base):
    __tablename__ = "entity_isa95_link"
    
    entity_id = Column(Integer, ForeignKey("entity.id", ondelete="CASCADE"), nullable=False)
    isa95_id = Column(Integer, ForeignKey("isa95_level.id", ondelete="CASCADE"), nullable=False)
    
    # Chiave primaria composita
    __table_args__ = (
        PrimaryKeyConstraint('entity_id', 'isa95_id'),
    )
    
    # Relationships
    entity = relationship("Entity", back_populates="isa95_links")
    isa95_level = relationship("ISA95Level", back_populates="entities")

# Tabella Intent Match (equivalenze tra intenti)
class IntentMatch(Base):
    __tablename__ = "intent_match"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    intent_a_id = Column(Integer, ForeignKey("intent.id", ondelete="CASCADE"), nullable=False)
    intent_b_id = Column(Integer, ForeignKey("intent.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(Enum(RelationType), default=RelationType.EQUIVALENT, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    
    # Constraint per evitare duplicati e self-reference
    __table_args__ = (
        UniqueConstraint('intent_a_id', 'intent_b_id', name='unique_intent_match'),
    )
    
    # Relationships
    intent_a = relationship("Intent", foreign_keys=[intent_a_id], back_populates="matches_as_a")
    intent_b = relationship("Intent", foreign_keys=[intent_b_id], back_populates="matches_as_b")

# Tabella Entity Match (equivalenze tra entità)
class EntityMatch(Base):
    __tablename__ = "entity_match"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_a_id = Column(Integer, ForeignKey("entity.id", ondelete="CASCADE"), nullable=False)
    entity_b_id = Column(Integer, ForeignKey("entity.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(Enum(RelationType), default=RelationType.EQUIVALENT, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    
    # Constraint per evitare duplicati e self-reference
    __table_args__ = (
        UniqueConstraint('entity_a_id', 'entity_b_id', name='unique_entity_match'),
    )
    
    # Relationships
    entity_a = relationship("Entity", foreign_keys=[entity_a_id], back_populates="matches_as_a")
    entity_b = relationship("Entity", foreign_keys=[entity_b_id], back_populates="matches_as_b")
