import os #Modulo nativo de Python para poder interactuar con el sistema operativo. La utilizamos para leer las variables de entorno que están en la memora del sistema.
#Por ejemplo: os.getenv("DATABASE_URL").
from dotenv import load_dotenv #Ayuda a leer el archivo .env y cargarlo en el entorno.
from sqlalchemy import create_engine #Crea el motor de conexión con la base de datos.
from sqlalchemy.orm import declarative_base,sessionmaker

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("No se encontró la variable de entorno DATABASE_URL en el .env")

#Esto crea el motor de la base de datos
engine = create_engine(DATABASE_URL)

#Esto crea una sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base para definir los modelos ORM
Base = declarative_base()

#Función para obtener la sesión de base de datos. Para obtener la sesion de bd en cada endpoint.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()