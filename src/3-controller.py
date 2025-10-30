from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_, and_

import json

from tables_definition import *

class Controller():
    def __init__(self, engine):
        Session = sessionmaker(bind=engine)
        self.session = Session()
            
    def _get_default_configuration(self):
        intents_path = r'C:\Users\f.cavaleri\Desktop\NLP_BREAKDOWN\IPCEI.NLPBreakdown\config\ontology\intents.json'
        entities_path = r'C:\Users\f.cavaleri\Desktop\NLP_BREAKDOWN\IPCEI.NLPBreakdown\config\ontology\entities.json'

        return {"intents" : self._get_json_data(intents_path),
                "entities" : self._get_json_data(entities_path)}

    def _get_json_data(self, path:str):
        '''
        used to get entities / intents from the json definition
        '''
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data

    def populate_default_db_configuration(self):
        '''
        used to populate che db with the initial configuration.
        the database must already exists
        '''
        default_configuration = self._get_default_configuration()

        self._populate_isa95_levels()
        self._populate_default_intents(default_configuration['intents'])
        self._populate_default_entities(default_configuration['entities'])

    def _populate_default_intents(self, intents_dict):
        '''
        it creates the structure for the create_intents_with_levels function

        keep this code clear!
        '''
        intents_dict = intents_dict['intents']
        intents_names = list(intents_dict.keys())
        intent_list=[]
        for name in intents_names:
            intent_description = intents_dict[name]['description'] + (' - function: '+intents_dict[name]['function'] 
                                                                      if 'function' in intents_dict[name].keys() 
                                                                      else '')
            intent_isa95_level = intents_dict[name]['domain']
            intent_list.append([name, intent_description, intent_isa95_level])
        
        self.create_intents_with_levels(intent_list)

    def _populate_default_entities(self, entities_dict):
        '''
        it creates the structure for the create_intents_with_levels function

        keep this code clear!
        '''
        entities_dict = entities_dict['entities']
        entities_names = list(entities_dict.keys())
        entities_list = []
        for name in entities_names:
            entity_description = entities_dict[name]['description']
            entity_isa95_level = entities_dict[name]['level']
            entities_list.append([name, entity_description, entity_isa95_level])
        
        self.create_entities_with_levels(entities_list)

    def create_intents_with_levels(self,
                                   intent_list):
        '''
        each element of the list must contain
        intent_name,
        intent_description,
        intent_isa95_level
        '''
        for intent in intent_list: 
            intent_name, intent_description, intent_isa95_levels = intent
            intent_obj = Intent(
                name=intent_name,
                description=intent_description
            )
            self.session.add(intent_obj)
            self.session.flush()  # Ottiene l'ID senza committare
            
            # Gestisce sia singolo livello che lista
            if isinstance(intent_isa95_levels, str):
                intent_isa95_levels = [intent_isa95_levels]
            
            # Associa ai livelli ISA95
            for level_name in intent_isa95_levels:
                level = self.session.query(ISA95Level).filter_by(name=level_name).first()
                
                if not level:
                    # Gestione errore: livello non trovato
                    self.session.rollback()
                    raise ValueError(f"Livello ISA95 '{level_name}' non trovato per intent '{intent_name}'")
                
                link = IntentISA95Link(intent_id=intent_obj.id, isa95_id=level.id)
                self.session.add(link)
        
        self.session.commit()
        
    def create_entities_with_levels(self,
                                   enity_list):
        '''
        each element of the list must contain
        entity_name,
        entity_description,
        entity_isa95_level
        '''
        for entity in enity_list: 
            entity_name, entity_description, entity_isa95_levels = entity
            entity_obj = Entity(
                name=entity_name,
                description=entity_description
            )
            self.session.add(entity_obj)
            self.session.flush()  # Ottiene l'ID senza committare
            
            # Gestisce sia singolo livello che lista
            if isinstance(entity_isa95_levels, str):
                entity_isa95_levels = [entity_isa95_levels]
            
            # Associa ai livelli ISA95
            for level_name in entity_isa95_levels:
                level = self.session.query(ISA95Level).filter_by(name=level_name).first()
                
                if not level:
                    # Gestione errore: livello non trovato
                    self.session.rollback()
                    raise ValueError(f"Livello ISA95 '{level_name}' non trovato per entity '{entity_name}'")
                
                link = EntityISA95Link(entity_id=entity_obj.id, isa95_id=level.id)
                self.session.add(link)
        
        self.session.commit()

    def _populate_isa95_levels(self):
        """Inserisce i livelli ISA95 standard"""
        levels = ["DEFAULT", "PLC", "SCADA", "MES", "ERP"]
        
        for level_name in levels:
            # Controlla se già esiste
            existing = self.session.query(ISA95Level).filter_by(name=level_name).first()
            if not existing:
                level = ISA95Level(name=level_name)
                self.session.add(level)
        
        self.session.commit()

    def define_intents_relation(self,
                                id_intent_a,
                                id_intent_b,
                                relation_type : RelationType,
                                confidence : float = 1.0):

        """
        Crea o aggiorna una relazione di matching tra due intenti.
        
        Args:
            intent_a: Nome del primo intent
            intent_b: Nome del secondo intent
            relation_type: Tipo di relazione (RelationType enum)
            confidence: Livello di confidenza [0.0-1.0]
        
        Raises:
            ValueError: Se intent non trovato o parametri invalidi
        
        Example:
            define_intents_relation("avvia_macchina", "start_machine", 
                                RelationType.EQUIVALENT, 1.0)
        """
        # Validazione confidence
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 e 1.0, got: {confidence}")
        
        # Trova gli intent
        intent_a_obj = self.session.query(Intent).filter_by(id=id_intent_a).first()
        intent_b_obj = self.session.query(Intent).filter_by(id=id_intent_b).first()
        
        # Validazione esistenza
        if not intent_a_obj:
            raise ValueError(f"Intent '{intent_a_obj.name}' non trovato nel database")
        if not intent_b_obj:
            raise ValueError(f"Intent '{intent_b_obj.name}' non trovato nel database")
        
        # Validazione self-reference
        if intent_a_obj.id == intent_b_obj.id:
            raise ValueError(f"Non è possibile creare una relazione di un intent con se stesso")
        
        # Controlla se la relazione già esiste (in entrambe le direzioni)
        existing_match = self.session.query(IntentMatch).filter(
            or_(
                and_(IntentMatch.intent_a_id == id_intent_a, IntentMatch.intent_b_id == id_intent_b),
                and_(IntentMatch.intent_a_id == id_intent_b, IntentMatch.intent_b_id == id_intent_a)
            )
        ).first()
        
        if existing_match:
            inverted_match = self.session.query(IntentMatch).filter(
                and_(IntentMatch.intent_a_id == id_intent_b, IntentMatch.intent_b_id == id_intent_a)
            ).first()
            if inverted_match:
                existing_match.intent_a_id = id_intent_a
                existing_match.intent_b_id = id_intent_b
            existing_match.relation_type = relation_type
            existing_match.confidence = confidence
            self.session.commit()
            print(f"Relation updated")
            return existing_match

        # Crea la nuova relazione
        match = IntentMatch(
            intent_a_id=intent_a_obj.id,
            intent_b_id=intent_b_obj.id,
            relation_type=relation_type,
            confidence=confidence
        )
        
        self.session.add(match)
        self.session.commit()
        
        print(f"relation created: {intent_a_obj.name} → {intent_b_obj.name} ({relation_type.value}, conf: {confidence})")
        return match

    def define_entities_relation(self,
                                id_entity_a,
                                id_entity_b,
                                relation_type : RelationType,
                                confidence : float = 1.0):

        """
        Crea o aggiorna una relazione di matching tra due entità.
        
        Args:
            id_entity_a: ID della prima entity
            id_entity_b: ID della seconda entity
            relation_type: Tipo di relazione (RelationType enum)
            confidence: Livello di confidenza [0.0-1.0]
        
        Raises:
            ValueError: Se entity non trovata o parametri invalidi
        
        Example:
            define_entities_relation(10, 11, RelationType.EQUIVALENT, 1.0)
        """
        # Validazione confidence
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 e 1.0, got: {confidence}")
        
        # Trova le entity
        entity_a_obj = self.session.query(Entity).filter_by(id=id_entity_a).first()
        entity_b_obj = self.session.query(Entity).filter_by(id=id_entity_b).first()
        
        # Validazione esistenza
        if not entity_a_obj:
            raise ValueError(f"Entity con ID {id_entity_a} not found")
        if not entity_b_obj:
            raise ValueError(f"Entity con ID {id_entity_b} not found")
        
        # Validazione self-reference
        if entity_a_obj.id == entity_b_obj.id:
            raise ValueError(f"Non è possibile creare una relazione di una entity con se stessa")
        
        # Controlla se la relazione già esiste (in entrambe le direzioni)
        existing_match = self.session.query(EntityMatch).filter(
            or_(
                and_(EntityMatch.entity_a_id == id_entity_a, EntityMatch.entity_b_id == id_entity_b),
                and_(EntityMatch.entity_a_id == id_entity_b, EntityMatch.entity_b_id == id_entity_a)
            )
        ).first()
        
        if existing_match:
            # Normalizza sempre nella direzione richiesta
            
            inverted_match = self.session.query(IntentMatch).filter(
                and_(EntityMatch.entity_a_id == id_entity_b, EntityMatch.entity_b_id == id_entity_a)
            ).first()
                
            if inverted_match:
                existing_match.entity_a_id = id_entity_a
                existing_match.entity_b_id = id_entity_b

            existing_match.relation_type = relation_type
            existing_match.confidence = confidence
            self.session.commit()
            print(f"Relation updated: {entity_a_obj.name} ↔ {entity_b_obj.name}")
            return existing_match
        
        # Crea la nuova relazione
        match = EntityMatch(
            entity_a_id=entity_a_obj.id,
            entity_b_id=entity_b_obj.id,
            relation_type=relation_type,
            confidence=confidence
        )
        
        self.session.add(match)
        self.session.commit()
        
        print(f"Relation created: {entity_a_obj.name} → {entity_b_obj.name} ({relation_type.value}, conf: {confidence})")
        return match

    def remove_intents_relation(self,  
                           id_intent_a: int = None,
                           id_intent_b: int = None,
                           match_id: int = None):
        """
        Rimuove relazioni tra intenti in base a diversi criteri.
        Args:
            id_intent_a: ID del primo intent (opzionale)
            id_intent_b: ID del secondo intent (opzionale)
            match_id: ID specifico della relazione (opzionale)
        
        Returns:
            int: Numero di relazioni rimosse
        
        Examples:
            # Rimuovi relazione specifica tra due intent
            remove_intents_relation(id_intent_a=180, id_intent_b=181)
            
            # Rimuovi relazione per ID
            remove_intents_relation(match_id=42)
            
            # Rimuovi tutte le relazioni BROADER tra due intent specifici
            remove_intents_relation(id_intent_a=180, id_intent_b=181, relation_type=RelationType.BROADER)
        """
        query = self.session.query(IntentMatch)
        # Validazione: almeno un parametro deve essere fornito
        if match_id is None and (id_intent_a is None or id_intent_b is None):
            raise ValueError("Devi fornire o 'match_id' oppure sia 'id_intent_a' che 'id_intent_b'")
    
        # Caso 1: Rimuovi per match_id specifico
        if match_id is not None:
            query = query.filter(IntentMatch.id == match_id)
        
        # Caso 2: Rimuovi per coppia di intent (bidirezionale)
        else: #  id_intent_a is not None and id_intent_b is not None:
            query = query.filter(
                and_(IntentMatch.intent_a_id == id_intent_a, IntentMatch.intent_b_id == id_intent_b)
            )
        
        # Esegui la query
        matches = query.all()
        count = len(matches)
        
        if count == 0:
            print("Nessuna relazione trovata con i criteri specificati")
            return 0
        
        # Elimina tutte le relazioni trovate
        for match in matches:
            self.session.delete(match)
        
        self.session.commit()
        
        print(f"{count} relazione/i rimossa/e")
        return count

    def remove_entities_relation(self,
                                 id_entity_a: int=None,
                                 id_entity_b: int=None,
                                 match_id:int = None):
        '''
        removes entity relations ...
        '''
        query = self.session.query(EntityMatch)
        # Validazione: almeno un parametro deve essere fornito
        if match_id is None and (id_entity_a is None or id_entity_b is None):
            raise ValueError("Devi fornire o 'match_id' oppure sia 'id_entity_a' che 'id_entity_b'")
    
        # Caso 1: Rimuovi per match_id specifico
        if match_id is not None:
            query = query.filter(EntityMatch.id == match_id)
        else:
            query = query.filter(
                # devi rimuovere esattamente la combinazione [id_entity_a, id_entity_b]
                # non il contrario, la direzione è importante
                and_(EntityMatch.entity_a_id == id_entity_a, EntityMatch.entity_b_id == id_entity_b)
            )

        # Esegui la query
        matches = query.all()
        count = len(matches)
        
        if count == 0:
            print("Nessuna relazione trovata con i criteri specificati")
            return 0
        
        # Elimina tutte le relazioni trovate
        for match in matches:
            self.session.delete(match)
        
        self.session.commit()
        
        print(f"{count} relazione/i rimossa/e")
        return count

        

    def query_intent_info(self):
        """Mostra tutte le informazioni su un intent"""

        pass

    def query_entity_info(self):
        """Mostra tutte le informazioni su una entità"""
    
        pass

    # modificare descrizione

    # modificare livello isa

    def remove_intents(self):


        pass

    def remove_entities(self):

        pass

    def get_intents_by_isa95_level(self):

        pass

    def get_entities_by_isa95_level(self):

        pass

import url

# Crea il motore SQLAlchemy
engine = create_engine(url.url, echo=True)

Base.metadata.create_all(engine)


controller = Controller(engine)
# controller.populate_default_db_configuration()
# controller.define_intents_relation(180, 181, RelationType.DEPRECATED)
# controller.define_intents_relation(181, 182, RelationType.DEPRECATED)
# controller.define_intents_relation(182, 183, RelationType.DEPRECATED)
# controller.define_intents_relation(180, 181, RelationType.BROADER)
# controller.define_entities_relation(74, 75, RelationType.EQUIVALENT)
# controller.remove_intents_relation(match_id=8)
# controller.remove_intents_relation(182, 183)
#
#  controller.define_entities_relation(75, 76, RelationType.DEPRECATED)
# controller.define_entities_relation(76, 77, RelationType.DEPRECATED)
# controller.define_entities_relation(78, 79, RelationType.DEPRECATED)
# controller.define_entities_relation(80, 82, RelationType.DEPRECATED)
controller.remove_entities_relation(match_id=4)