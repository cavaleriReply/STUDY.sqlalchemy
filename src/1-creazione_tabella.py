from sqlalchemy import create_engine, text
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

import url

# Crea il motore SQLAlchemy
engine = create_engine(url.url, echo=True)

Base = declarative_base()
'''
Base non è una semplice classe, ma utilizza un metaclass che intercetta la creazione di tutte le sue sottoclassi.
'''

# Modello (tabella)
class Entity(Base):
    '''
    Nel momento in cui Python esegue questa dichiarazione, il metaclass:
    - Registra automaticamente Entity in un registro interno (Base.metadata)
    - Analizza tutti gli attributi Column
    - Costruisce una rappresentazione della struttura della tabella
    '''
    __tablename__ = "entity"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(200))
    isa95_level_id = Column(Integer)

# Creazione fisica delle tabelle nel DB
Base.metadata.create_all(engine)

# Inserimento di prova
Session = sessionmaker(bind=engine)
session = Session()
session.add(Entity(name="città", description="luogo", isa95_level="m35"))
session.commit()

print("Tabelle create in MySQL e record inserito")