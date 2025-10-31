from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_, and_

import json

from tables_definition import *

# RepositoryLayer
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

    # modificare descrizione

    def modify_intent_description(self):
        """Mostra tutte le informazioni su un intent"""

        pass

    def modify_entity_description(self):
        """Mostra tutte le informazioni su una entità"""
    
        pass

    # modificare livello isa
    def replace_intent_isa_levels(self, 
                                intent_id: int = None,
                                intent_name: str = None,
                                levels: ISA95LevelEnum = None):
        """
        Sostituisce completamente i livelli ISA95 di un intent.
        
        Args:
            intent_id: ID dell'intent (opzionale)
            intent_name: Nome dell'intent (opzionale)
            levels: Lista di nuovi livelli ISA95
        
        Returns:
            Intent: L'intent modificato
        
        Raises:
            ValueError: Se intent non trovato o parametri invalidi
        
        Example:
            replace_intent_isa_levels(intent_id=180, levels=["MES", "ERP"])
        """
        # Validazione
        if intent_id is None and intent_name is None:
            raise ValueError("Devi fornire 'intent_id' o 'intent_name'")
        
        if not levels:
            raise ValueError("Devi fornire almeno un livello")
        
        # Normalizza a lista
        if not isinstance(levels, list):
            levels = [levels]
        
        # Trova l'intent
        if intent_id is not None:
            intent = self.session.query(Intent).filter_by(id=intent_id).first()
        else:
            intent = self.session.query(Intent).filter_by(name=intent_name).first()
        
        if not intent:
            identifier = intent_id if intent_id else intent_name
            raise ValueError(f"Intent '{identifier}' non trovato nel database")
        
        # Rimuovi tutti i link esistenti
        self.session.query(IntentISA95Link)\
            .filter(IntentISA95Link.intent_id == intent.id)\
            .delete()
        
        # Aggiungi i nuovi livelli
        for level_obj in levels:
            level = self.session.query(ISA95Level).filter_by(name=level_obj.value).first()
            if not level:
                self.session.rollback()
                raise ValueError(f"Livello ISA95 '{level_obj.value}' non trovato")
            
            link = IntentISA95Link(intent_id=intent.id, isa95_id=level.id)
            self.session.add(link)
        
        self.session.commit()
        
        print(f"Livelli sostituiti per intent '{intent.name}': {', '.join(level.value for level in levels)}")
        return intent

    def add_intent_isa_levels(self, 
                            intent_id: int = None,
                            intent_name: str = None,
                            # levels: list[str] = None):
                            levels: ISA95LevelEnum = None):
        """
        Aggiunge livelli ISA95 a un intent (mantiene i livelli esistenti).
        
        Args:
            intent_id: ID dell'intent (opzionale)
            intent_name: Nome dell'intent (opzionale)
            levels: Lista di livelli da aggiungere
        
        Returns:
            Intent: L'intent modificato
        
        Raises:
            ValueError: Se intent non trovato o parametri invalidi
        
        Example:
            add_intent_isa_levels(intent_name="start_machine", levels=["SCADA", "MES"])
        """
        # Validazione
        if intent_id is None and intent_name is None:
            raise ValueError("Devi fornire 'intent_id' o 'intent_name'")
        
        if not levels:
            raise ValueError("Devi fornire almeno un livello")
        
        # Normalizza a lista
        if not isinstance(levels, list):
            levels = [levels]
        
        # Trova l'intent
        if intent_id is not None:
            intent = self.session.query(Intent).filter_by(id=intent_id).first()
        else:
            intent = self.session.query(Intent).filter_by(name=intent_name).first()
        
        if not intent:
            identifier = intent_id if intent_id else intent_name
            raise ValueError(f"Intent '{identifier}' non trovato nel database")
        
        # Aggiungi livelli
        added_count = 0
        skipped = []
        
        for level_obj in levels:
            level = self.session.query(ISA95Level).filter_by(name=level_obj.value).first()
            if not level:
                self.session.rollback()
                raise ValueError(f"Livello ISA95 '{level_obj.value}' non trovato")
            
            # Controlla se il link già esiste
            existing = self.session.query(IntentISA95Link).filter_by(
                intent_id=intent.id,
                isa95_id=level.id
            ).first()
            
            if not existing:
                link = IntentISA95Link(intent_id=intent.id, isa95_id=level.id)
                self.session.add(link)
                added_count += 1
            else:
                skipped.append(level_obj.value)
        
        self.session.commit()
        
        # Messaggi
        if added_count > 0:
            print(f"{added_count} livello/i aggiunto/i per intent '{intent.name}'")
        if skipped:
            print(f"Livelli già associati (skip): {', '.join(skipped)}")
        
        # Mostra livelli correnti
        current_levels = [link.isa95_level.name for link in intent.isa95_links]
        print(f"Livelli correnti: {', '.join(current_levels)}")
        
        return intent

    def remove_intent_isa_levels(self, 
                                intent_id: int = None,
                                intent_name: str = None,
                                levels: ISA95LevelEnum = None):
        """
        Rimuove livelli ISA95 da un intent.
        
        Args:
            intent_id: ID dell'intent (opzionale)
            intent_name: Nome dell'intent (opzionale)
            levels: Lista di livelli da rimuovere
        
        Returns:
            Intent: L'intent modificato
        
        Raises:
            ValueError: Se intent non trovato o parametri invalidi
        
        Example:
            remove_intent_isa_levels(intent_id=180, levels=["PLC", "DEFAULT"])
        """
        # Validazione
        if intent_id is None and intent_name is None:
            raise ValueError("Devi fornire 'intent_id' o 'intent_name'")
        
        if not levels:
            raise ValueError("Devi fornire almeno un livello")
        
        # Normalizza a lista
        if not isinstance(levels, list):
            levels = [levels]
        
        # Trova l'intent
        if intent_id is not None:
            intent = self.session.query(Intent).filter_by(id=intent_id).first()
        else:
            intent = self.session.query(Intent).filter_by(name=intent_name).first()
        
        if not intent:
            identifier = intent_id if intent_id else intent_name
            raise ValueError(f"Intent '{identifier}' non trovato nel database")
        
        # Rimuovi livelli
        removed_count = 0
        not_found = []
        
        for level_obj in levels:
            level = self.session.query(ISA95Level).filter_by(name=level_obj.value).first()
            if not level:
                not_found.append(level_obj.value)
                continue
            
            # Rimuovi il link
            deleted = self.session.query(IntentISA95Link).filter_by(
                intent_id=intent.id,
                isa95_id=level.id
            ).delete()
            
            removed_count += deleted
        
        self.session.commit()
        
        # Messaggi
        if removed_count > 0:
            print(f"{removed_count} livello/i rimosso/i per intent '{intent.name}'")
        else:
            print(f"Nessun livello rimosso (non erano associati)")
        
        if not_found:
            print(f"Livelli non trovati nel DB: {', '.join(not_found)}")
        
        # Mostra livelli correnti
        current_levels = [link.isa95_level.name for link in intent.isa95_links]
        if current_levels:
            print(f"Livelli correnti: {', '.join(current_levels)}")
        else:
            print(f"Intent '{intent.name}' non ha più livelli ISA95 associati")
        
        return intent

    def replace_entity_isa_levels(self, 
                             entity_id: int = None,
                             entity_name: str = None,
                             levels: ISA95LevelEnum = None):
        """
        Sostituisce completamente i livelli ISA95 di un'entità.
        
        Args:
            entity_id: ID dell'entity (opzionale)
            entity_name: Nome dell'entity (opzionale)
            levels: Lista di nuovi livelli ISA95
        
        Returns:
            Entity: L'entity modificata
        
        Raises:
            ValueError: Se entity non trovata o parametri invalidi
        
        Example:
            replace_entity_isa_levels(entity_id=42, levels=[ISA95LevelEnum.LEVEL_3, ISA95LevelEnum.LEVEL_4])
        """
        # Validazione
        if entity_id is None and entity_name is None:
            raise ValueError("Devi fornire 'entity_id' o 'entity_name'")
        
        if not levels:
            raise ValueError("Devi fornire almeno un livello")
        
        # Normalizza a lista
        if not isinstance(levels, list):
            levels = [levels]
        
        # Trova l'entity
        if entity_id is not None:
            entity = self.session.query(Entity).filter_by(id=entity_id).first()
        else:
            entity = self.session.query(Entity).filter_by(name=entity_name).first()
        
        if not entity:
            identifier = entity_id if entity_id else entity_name
            raise ValueError(f"Entity '{identifier}' non trovata nel database")
        
        # Rimuovi tutti i link esistenti
        self.session.query(EntityISA95Link)\
            .filter(EntityISA95Link.entity_id == entity.id)\
            .delete()
        
        # Aggiungi i nuovi livelli
        for level_obj in levels:
            level = self.session.query(ISA95Level).filter_by(name=level_obj.value).first()
            if not level:
                self.session.rollback()
                raise ValueError(f"Livello ISA95 '{level_obj.value}' non trovato")
            
            link = EntityISA95Link(entity_id=entity.id, isa95_id=level.id)
            self.session.add(link)
        
        self.session.commit()
        
        print(f"Livelli sostituiti per entity '{entity.name}': {', '.join(level.value for level in levels)}")
        return entity

    def add_entity_isa_levels(self, 
                            entity_id: int = None,
                            entity_name: str = None,
                            levels: ISA95LevelEnum = None):
        """
        Aggiunge livelli ISA95 a un'entità (mantiene i livelli esistenti).
        
        Args:
            entity_id: ID dell'entity (opzionale)
            entity_name: Nome dell'entity (opzionale)
            levels: Lista di livelli da aggiungere
        
        Returns:
            Entity: L'entity modificata
        
        Raises:
            ValueError: Se entity non trovata o parametri invalidi
        
        Example:
            add_entity_isa_levels(entity_name="sensor", levels=[ISA95LevelEnum.LEVEL_2])
        """
        # Validazione
        if entity_id is None and entity_name is None:
            raise ValueError("Devi fornire 'entity_id' o 'entity_name'")
        
        if not levels:
            raise ValueError("Devi fornire almeno un livello")
        
        # Normalizza a lista
        if not isinstance(levels, list):
            levels = [levels]
        
        # Trova l'entity
        if entity_id is not None:
            entity = self.session.query(Entity).filter_by(id=entity_id).first()
        else:
            entity = self.session.query(Entity).filter_by(name=entity_name).first()
        
        if not entity:
            identifier = entity_id if entity_id else entity_name
            raise ValueError(f"Entity '{identifier}' non trovata nel database")
        
        # Aggiungi livelli
        added_count = 0
        skipped = []
        
        for level_obj in levels:
            level = self.session.query(ISA95Level).filter_by(name=level_obj.value).first()
            if not level:
                self.session.rollback()
                raise ValueError(f"Livello ISA95 '{level_obj.value}' non trovato")
            
            # Controlla se il link già esiste
            existing = self.session.query(EntityISA95Link).filter_by(
                entity_id=entity.id,
                isa95_id=level.id
            ).first()
            
            if not existing:
                link = EntityISA95Link(entity_id=entity.id, isa95_id=level.id)
                self.session.add(link)
                added_count += 1
            else:
                skipped.append(level_obj.value)
        
        self.session.commit()
        
        # Messaggi
        if added_count > 0:
            print(f"{added_count} livello/i aggiunto/i per entity '{entity.name}'")
        if skipped:
            print(f"Livelli già associati (skip): {', '.join(skipped)}")
        
        # Mostra livelli correnti
        current_levels = [link.isa95_level.name for link in entity.isa95_links]
        print(f"Livelli correnti: {', '.join(current_levels)}")
        
        return entity

    def remove_entity_isa_levels(self, 
                                entity_id: int = None,
                                entity_name: str = None,
                                levels: ISA95LevelEnum = None):
        """
        Rimuove livelli ISA95 da un'entità.
        
        Args:
            entity_id: ID dell'entity (opzionale)
            entity_name: Nome dell'entity (opzionale)
            levels: Lista di livelli da rimuovere
        
        Returns:
            Entity: L'entity modificata
        
        Raises:
            ValueError: Se entity non trovata o parametri invalidi
        
        Example:
            remove_entity_isa_levels(entity_id=42, levels=[ISA95LevelEnum.LEVEL_0, ISA95LevelEnum.DEFAULT])
        """
        # Validazione
        if entity_id is None and entity_name is None:
            raise ValueError("Devi fornire 'entity_id' o 'entity_name'")
        
        if not levels:
            raise ValueError("Devi fornire almeno un livello")
        
        # Normalizza a lista
        if not isinstance(levels, list):
            levels = [levels]
        
        # Trova l'entity
        if entity_id is not None:
            entity = self.session.query(Entity).filter_by(id=entity_id).first()
        else:
            entity = self.session.query(Entity).filter_by(name=entity_name).first()
        
        if not entity:
            identifier = entity_id if entity_id else entity_name
            raise ValueError(f"Entity '{identifier}' non trovata nel database")
        
        # Rimuovi livelli
        removed_count = 0
        not_found = []
        
        for level_obj in levels:
            level = self.session.query(ISA95Level).filter_by(name=level_obj.value).first()
            if not level:
                not_found.append(level_obj.value)
                continue
            
            # Rimuovi il link
            deleted = self.session.query(EntityISA95Link).filter_by(
                entity_id=entity.id,
                isa95_id=level.id
            ).delete()
            
            removed_count += deleted
        
        self.session.commit()
        
        # Messaggi
        if removed_count > 0:
            print(f"{removed_count} livello/i rimosso/i per entity '{entity.name}'")
        else:
            print(f"Nessun livello rimosso (non erano associati)")
        
        if not_found:
            print(f"Livelli non trovati nel DB: {', '.join(not_found)}")
        
        # Mostra livelli correnti
        current_levels = [link.isa95_level.name for link in entity.isa95_links]
        if current_levels:
            print(f"Livelli correnti: {', '.join(current_levels)}")
        else:
            print(f"Entity '{entity.name}' non ha più livelli ISA95 associati")
        
        return entity
   

    def modify_entity_isa_level(self, 
                    entity_id: int = None,
                    entity_name: str = None):
        
        pass
        
    def remove_intents(self, 
                    intent_ids: list[int] = None,
                    intent_names: list[str] = None):
        """
        Rimuove uno o più intenti dal database.
        Grazie al CASCADE, elimina automaticamente anche:
        - Link con livelli ISA95
        - Relazioni di matching con altri intenti
        
        Args:
            intent_ids: Lista di ID degli intenti da rimuovere (opzionale)
            intent_names: Lista di nomi degli intenti da rimuovere (opzionale)
        
        Returns:
            int: Numero di intenti rimossi
        
        Examples:
            # Rimuovi per ID
            remove_intents(intent_ids=[180, 181, 182])
            
            # Rimuovi per nome
            remove_intents(intent_names=["start_machine", "stop_machine"])
            
            # Rimuovi singolo intent
            remove_intents(intent_ids=[180])
        """
        
        # Validazione: almeno un parametro deve essere fornito
        if intent_ids is None and intent_names is None:
            raise ValueError("Devi fornire 'intent_ids' o 'intent_names'")
        
        # Se entrambi sono forniti, usa solo gli ID
        if intent_ids is not None and intent_names is not None:
            print("Entrambi intent_ids e intent_names forniti, uso solo intent_ids")
            intent_names = None
        
        query = self.session.query(Intent)
        
        # Filtra per ID
        if intent_ids is not None:
            if not isinstance(intent_ids, list):
                intent_ids = [intent_ids]
            query = query.filter(Intent.id.in_(intent_ids))
        
        # Filtra per nome
        elif intent_names is not None:
            if not isinstance(intent_names, list):
                intent_names = [intent_names]
            query = query.filter(Intent.name.in_(intent_names))
        
        # Trova gli intenti
        intents = query.all()
        count = len(intents)
        
        if count == 0:
            print("Nessun intent trovato con i criteri specificati")
            return 0
        
        # Elimina tutti gli intenti trovati (CASCADE elimina link e match)
        for intent in intents:
            self.session.delete(intent)
        
        self.session.commit()
        
        print(f"{count} intent/i eliminato/i")
        return count

    def remove_entities(self,
                        entity_ids: list[int]=None,
                        entity_names: list[str]=None):
        """
        Rimuove uno o più entità dal database.
        Grazie al CASCADE, elimina automaticamente anche:
        - Link con livelli ISA95
        - Relazioni di matching con altre entità
        
        Args:
            entity_ids: Lista di ID delle entità da rimuovere (opzionale)
            entity_names: Lista di nomi delle entità da rimuovere (opzionale)
        
        Returns:
            int: Numero di entità rimosse
        
        """        
        # Validazione: almeno un parametro deve essere fornito
        if entity_ids is None and entity_names is None:
            raise ValueError("Devi fornire 'intent_ids' o 'intent_names'")
        
        # Se entrambi sono forniti, usa solo gli ID
        if entity_ids is not None and entity_names is not None:
            print("Entrambi intent_ids e intent_names forniti, uso solo intent_ids")
            entity_names = None
        
        query = self.session.query(Entity)
    
        # Filtra per ID
        if entity_ids is not None:
            if not isinstance(entity_ids, list):
                entity_ids = [entity_ids]
            query = query.filter(Entity.id.in_(entity_ids))
        
        # Filtra per nome
        elif entity_names is not None:
            if not isinstance(entity_names, list):
                entity_names = [entity_names]
            query = query.filter(Entity.name.in_(entity_names))
        
        # Trova gli intenti
        entities = query.all()
        count = len(entities)
        
        if count == 0:
            print("Nessun intent trovato con i criteri specificati")
            return 0
        
        # Elimina tutti gli intenti trovati (CASCADE elimina link e match)
        for entity in entities:
            self.session.delete(entity)
        
        self.session.commit()
        
        print(f"{count} entities eliminati")
        return count

    def get_intents_by_isa95_level(self, level: ISA95LevelEnum):
        """
        Recupera tutti gli intenti associati a un livello ISA95 specifico.
        
        Args:
            level_name: Nome del livello ISA95 (es. "MES", "SCADA", "PLC", "ERP"), classe ISA95Level
        
        Returns:
            list[Intent]: Lista di intenti associati al livello
        
        Raises:
            ValueError: Se il livello ISA95 non esiste
        
        Example:
            intents = get_intents_by_isa95_level(ISA95Level.MES)
            for intent in intents:
                print(f"{intent.name}: {intent.description}")
        """
        # Trova il livello ISA95
        level = self.session.query(ISA95Level).filter_by(name=level.value).first()
        
        if not level:
            raise ValueError(f"Livello ISA95 '{level.name}' non trovato. "
                            f"Livelli disponibili: DEFAULT, PLC, SCADA, MES, ERP")
        
        # Query per trovare gli intenti associati
        intents = self.session.query(Intent)\
            .join(IntentISA95Link)\
            .filter(IntentISA95Link.isa95_id == level.id)\
            .all()
        
        print(f"Trovati {len(intents)} intent/i per livello '{level.name}'")
        
        return intents

    def get_entities_by_isa95_level(self, level: ISA95LevelEnum):
        """
        Recupera tutte le entità associati a un livello ISA95 specifico.
        
        Args:
            level_name: Nome del livello ISA95 (es. "MES", "SCADA", "PLC", "ERP"), classe ISA95Level
        
        Returns:
            list[Intent]: Lista di entità associate al livello
        
        Raises:
            ValueError: Se il livello ISA95 non esiste
        
        Example:
            entities = get_entities_by_isa95_level(ISA95Level.MES)
            for entity in entities:
                print(f"{entity.name}: {entity.description}")
        """
        # Trova il livello ISA95
        level = self.session.query(ISA95Level).filter_by(name=level.value).first()
        
        if not level:
            raise ValueError(f"Livello ISA95 '{level.name}' non trovato. "
                            f"Livelli disponibili: DEFAULT, PLC, SCADA, MES, ERP")
        
        # Query per trovare gli intenti associati
        entities = self.session.query(Entity)\
            .join(EntityISA95Link)\
            .filter(EntityISA95Link.isa95_id == level.id)\
            .all()
        
        print(f"Trovati {len(entities)} intent/i per livello '{level.name}'")
        
        return entities

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
# controller.define_entities_relation(75, 90, RelationType.DEPRECATED)
# controller.define_entities_relation(90, 77, RelationType.DEPRECATED)
# controller.define_entities_relation(78, 79, RelationType.DEPRECATED)
# controller.define_entities_relation(80, 82, RelationType.DEPRECATED)
# controller.remove_entities_relation(match_id=4)
# controller.define_intents_relation(181, 182, RelationType.EQUIVALENT)
# controller.remove_intents(intent_ids=[181, 182])
# controller.remove_entities(entity_ids=[75, 78])
# controller.remove_entities(entity_names=['logical_entity', 'failure_mode'])


# out = controller.get_intents_by_isa95_level(ISA95LevelEnum.LEVEL_2)
# print([elem.id for elem in out])
# out = controller.get_entities_by_isa95_level(ISA95LevelEnum.LEVEL_2)
# print([elem.id for elem in out])

# controller.add_intent_isa_levels(183, levels= ISA95LevelEnum.LEVEL_0)
# controller.remove_intent_isa_levels(183, levels= ISA95LevelEnum.LEVEL_0)
# controller.replace_intent_isa_levels(183, levels= [ISA95LevelEnum.LEVEL_0,ISA95LevelEnum.LEVEL_4,ISA95LevelEnum.LEVEL_3])


# controller.add_entity_isa_levels(77, levels=[ISA95LevelEnum.LEVEL_0,ISA95LevelEnum.LEVEL_4,ISA95LevelEnum.LEVEL_3])
# controller.replace_entity_isa_levels(77, levels=[ISA95LevelEnum.LEVEL_0])

# controller.remove_entity_isa_levels(77, levels=[ISA95LevelEnum.LEVEL_4,ISA95LevelEnum.LEVEL_3])

