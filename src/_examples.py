from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, ISA95Level, Intent, Entity, IntentISA95Link, EntityISA95Link, IntentMatch, EntityMatch, RelationType

# Setup database
engine = create_engine("mysql+pymysql://user:password@localhost:3306/organization_db", echo=True)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# =============================================================================
# ESEMPIO 1: Popolazione iniziale tabella ISA95
# =============================================================================
def populate_isa95_levels():
    """Inserisce i livelli ISA95 standard"""
    levels = ["DEFAULT", "PLC", "SCADA", "MES", "ERP"]
    
    for level_name in levels:
        # Controlla se già esiste
        existing = session.query(ISA95Level).filter_by(name=level_name).first()
        if not existing:
            level = ISA95Level(name=level_name)
            session.add(level)
    
    session.commit()
    print("✓ Livelli ISA95 creati")

# =============================================================================
# ESEMPIO 2: Creazione Intent con livelli ISA95
# =============================================================================
def create_intents_with_levels():
    """Crea intenti e li associa a livelli ISA95"""
    
    # Intent per avviare macchina (livello MES)
    intent_start = Intent(
        name="start_machine",
        description="Avvia una macchina di produzione"
    )
    session.add(intent_start)
    session.flush()  # Ottiene l'ID senza committare
    
    # Associa a livello MES
    mes_level = session.query(ISA95Level).filter_by(name="MES").first()
    link = IntentISA95Link(intent_id=intent_start.id, isa95_id=mes_level.id)
    session.add(link)
    
    # Intent per leggere sensore (livelli PLC e SCADA)
    intent_read = Intent(
        name="read_sensor",
        description="Legge valore da un sensore"
    )
    session.add(intent_read)
    session.flush()
    
    # Associa a PLC
    plc_level = session.query(ISA95Level).filter_by(name="PLC").first()
    session.add(IntentISA95Link(intent_id=intent_read.id, isa95_id=plc_level.id))
    
    # Associa anche a SCADA
    scada_level = session.query(ISA95Level).filter_by(name="SCADA").first()
    session.add(IntentISA95Link(intent_id=intent_read.id, isa95_id=scada_level.id))
    
    # Intent ERP per ordini
    intent_order = Intent(
        name="create_order",
        description="Crea un nuovo ordine di produzione"
    )
    session.add(intent_order)
    session.flush()
    
    erp_level = session.query(ISA95Level).filter_by(name="ERP").first()
    session.add(IntentISA95Link(intent_id=intent_order.id, isa95_id=erp_level.id))
    
    session.commit()
    print("✓ Intent creati e associati a livelli ISA95")

# =============================================================================
# ESEMPIO 3: Creazione Entity con livelli ISA95
# =============================================================================
def create_entities_with_levels():
    """Crea entità e le associa a livelli ISA95"""
    
    # Entità macchina (MES/SCADA)
    entity_machine = Entity(
        name="machine",
        description="Macchina di produzione generica"
    )
    session.add(entity_machine)
    session.flush()
    
    mes = session.query(ISA95Level).filter_by(name="MES").first()
    scada = session.query(ISA95Level).filter_by(name="SCADA").first()
    
    session.add(EntityISA95Link(entity_id=entity_machine.id, isa95_id=mes.id))
    session.add(EntityISA95Link(entity_id=entity_machine.id, isa95_id=scada.id))
    
    # Entità sensore (PLC/SCADA)
    entity_sensor = Entity(
        name="sensor",
        description="Sensore industriale"
    )
    session.add(entity_sensor)
    session.flush()
    
    plc = session.query(ISA95Level).filter_by(name="PLC").first()
    session.add(EntityISA95Link(entity_id=entity_sensor.id, isa95_id=plc.id))
    session.add(EntityISA95Link(entity_id=entity_sensor.id, isa95_id=scada.id))
    
    # Entità ordine (ERP)
    entity_order = Entity(
        name="production_order",
        description="Ordine di produzione"
    )
    session.add(entity_order)
    session.flush()
    
    erp = session.query(ISA95Level).filter_by(name="ERP").first()
    session.add(EntityISA95Link(entity_id=entity_order.id, isa95_id=erp.id))
    
    session.commit()
    print("✓ Entity create e associate a livelli ISA95")

# =============================================================================
# ESEMPIO 4: Creazione match tra Intent (equivalenze)
# =============================================================================
def create_intent_matches():
    """Crea relazioni di matching tra intenti"""
    
    # Scenario: azienda italiana e inglese con intenti equivalenti
    intent_it = Intent(name="avvia_macchina", description="Avvia macchina (IT)")
    intent_en = Intent(name="start_machine", description="Start machine (EN)")
    
    session.add_all([intent_it, intent_en])
    session.flush()
    
    # Match equivalente
    match1 = IntentMatch(
        intent_a_id=intent_it.id,
        intent_b_id=intent_en.id,
        relation_type=RelationType.EQUIVALENT,
        confidence=1.0
    )
    session.add(match1)
    
    # Intento più specifico
    intent_start_cnc = Intent(
        name="start_cnc_machine",
        description="Avvia macchina CNC specifica"
    )
    session.add(intent_start_cnc)
    session.flush()
    
    # Match narrower (più specifico)
    match2 = IntentMatch(
        intent_a_id=intent_en.id,
        intent_b_id=intent_start_cnc.id,
        relation_type=RelationType.BROADER,  # start_machine è più ampio
        confidence=0.9
    )
    session.add(match2)
    
    # Intento deprecato
    intent_old = Intent(name="machine_on", description="Vecchio nome intent")
    session.add(intent_old)
    session.flush()
    
    match3 = IntentMatch(
        intent_a_id=intent_old.id,
        intent_b_id=intent_en.id,
        relation_type=RelationType.DEPRECATED,
        confidence=1.0
    )
    session.add(match3)
    
    session.commit()
    print("✓ Match tra intent creati")

# =============================================================================
# ESEMPIO 5: Creazione match tra Entity
# =============================================================================
def create_entity_matches():
    """Crea relazioni di matching tra entità"""
    
    # Entità sinonimi
    entity_temp = Entity(name="temperature", description="Temperatura")
    entity_temp_sensor = Entity(name="temp_sensor", description="Sensore temperatura")
    
    session.add_all([entity_temp, entity_temp_sensor])
    session.flush()
    
    match = EntityMatch(
        entity_a_id=entity_temp.id,
        entity_b_id=entity_temp_sensor.id,
        relation_type=RelationType.EQUIVALENT,
        confidence=0.95
    )
    session.add(match)
    
    session.commit()
    print("✓ Match tra entity creati")

# =============================================================================
# ESEMPIO 6: Query - Trovare tutti gli intent di un livello ISA95
# =============================================================================
def query_intents_by_isa95_level(level_name):
    """Trova tutti gli intent associati a un livello ISA95"""
    
    level = session.query(ISA95Level).filter_by(name=level_name).first()
    
    if not level:
        print(f"Livello {level_name} non trovato")
        return
    
    intents = session.query(Intent)\
        .join(IntentISA95Link)\
        .filter(IntentISA95Link.isa95_id == level.id)\
        .all()
    
    print(f"\n📋 Intent per livello {level_name}:")
    for intent in intents:
        print(f"  - {intent.name}: {intent.description}")

# =============================================================================
# ESEMPIO 7: Query - Trovare i livelli ISA95 di un intent
# =============================================================================
def query_isa95_levels_by_intent(intent_name):
    """Trova tutti i livelli ISA95 di un intent"""
    
    intent = session.query(Intent).filter_by(name=intent_name).first()
    
    if not intent:
        print(f"Intent {intent_name} non trovato")
        return
    
    levels = session.query(ISA95Level)\
        .join(IntentISA95Link)\
        .filter(IntentISA95Link.intent_id == intent.id)\
        .all()
    
    print(f"\n📊 Livelli ISA95 per intent '{intent_name}':")
    for level in levels:
        print(f"  - {level.name}")

# =============================================================================
# ESEMPIO 8: Query - Trovare intent equivalenti (match)
# =============================================================================
def query_equivalent_intents(intent_name):
    """Trova tutti gli intent equivalenti a uno dato"""
    
    intent = session.query(Intent).filter_by(name=intent_name).first()
    
    if not intent:
        print(f"Intent {intent_name} non trovato")
        return
    
    # Trova match dove l'intent è intent_a
    matches_a = session.query(IntentMatch, Intent)\
        .join(Intent, IntentMatch.intent_b_id == Intent.id)\
        .filter(IntentMatch.intent_a_id == intent.id)\
        .all()
    
    # Trova match dove l'intent è intent_b
    matches_b = session.query(IntentMatch, Intent)\
        .join(Intent, IntentMatch.intent_a_id == Intent.id)\
        .filter(IntentMatch.intent_b_id == intent.id)\
        .all()
    
    print(f"\n🔗 Match per intent '{intent_name}':")
    for match, matched_intent in matches_a:
        print(f"  → {matched_intent.name} ({match.relation_type.value}, confidence: {match.confidence})")
    
    for match, matched_intent in matches_b:
        print(f"  ← {matched_intent.name} ({match.relation_type.value}, confidence: {match.confidence})")

# =============================================================================
# ESEMPIO 9: Query complessa - Intent con livelli e match
# =============================================================================
def query_intent_full_info(intent_name):
    """Mostra tutte le informazioni su un intent"""
    
    intent = session.query(Intent).filter_by(name=intent_name).first()
    
    if not intent:
        print(f"Intent {intent_name} non trovato")
        return
    
    print(f"\n🎯 Informazioni complete per '{intent.name}':")
    print(f"   Descrizione: {intent.description}")
    print(f"   Creato: {intent.created_at}")
    
    # Livelli ISA95
    print(f"\n   Livelli ISA95:")
    for link in intent.isa95_links:
        print(f"     - {link.isa95_level.name}")
    
    # Match
    print(f"\n   Match:")
    for match in intent.matches_as_a:
        print(f"     → {match.intent_b.name} ({match.relation_type.value})")
    for match in intent.matches_as_b:
        print(f"     ← {match.intent_a.name} ({match.relation_type.value})")

# =============================================================================
# ESEMPIO 10: Aggiornamento e eliminazione
# =============================================================================
def update_and_delete_examples():
    """Esempi di update e delete"""
    
    # UPDATE: Modifica descrizione intent
    intent = session.query(Intent).filter_by(name="start_machine").first()
    if intent:
        intent.description = "Avvia una macchina di produzione (aggiornato)"
        session.commit()
        print("✓ Intent aggiornato")
    
    # DELETE: Elimina un match (CASCADE automatico)
    match = session.query(IntentMatch).first()
    if match:
        session.delete(match)
        session.commit()
        print("✓ Match eliminato")
    
    # DELETE intent (CASCADE elimina anche link e match)
    intent = session.query(Intent).filter_by(name="machine_on").first()
    if intent:
        session.delete(intent)
        session.commit()
        print("✓ Intent eliminato (con CASCADE su link e match)")

# =============================================================================
# ESECUZIONE ESEMPI
# =============================================================================
if __name__ == "__main__":
    try:
        # Setup iniziale
        populate_isa95_levels()
        create_intents_with_levels()
        create_entities_with_levels()
        create_intent_matches()
        create_entity_matches()
        
        # Query
        query_intents_by_isa95_level("MES")
        query_isa95_levels_by_intent("read_sensor")
        query_equivalent_intents("start_machine")
        query_intent_full_info("start_machine")
        
        # Update e Delete
        update_and_delete_examples()
        
    except Exception as e:
        session.rollback()
        print(f"❌ Errore: {e}")
    finally:
        session.close()