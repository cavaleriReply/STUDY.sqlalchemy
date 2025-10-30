
# Configura i tuoi parametri
user = "root"           # o l’utente configurato in WAMP
password = ""           # la password (spesso vuota per default)
host = "localhost"
port = "3306"
database = "test_db"    # un database che hai creato in phpMyAdmin

# Crea la stringa di connessione
url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
