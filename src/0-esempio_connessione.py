from sqlalchemy import create_engine, text
import url

# Crea il motore SQLAlchemy
engine = create_engine(url.url, echo=True)

# Test: connessione e query semplice
with engine.connect() as conn:
    result = conn.execute(text("SELECT VERSION()"))
    print("MySQL Version:", list(result)[0][0])
