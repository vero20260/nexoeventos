from fastapi import FastAPI
from app.database import engine, Base
from app.routers import clientes, salones, servicios, staff, eventos, asistentes, reportes
from fastapi.middleware.cors import CORSMiddleware #le da permiso a Streamlit para comunicarse con la API sin ser bloqueada. Porque los navegadores web bloquean que una página en el puerto 8501 le haga preguntas a una en el puerto 8000
import app.models  # Importa los modelos para que Base.metadata conozca las entidades



# 1. CREACIÓN DE TABLAS EN POSTGRESQL


Base.metadata.create_all(bind=engine)

# 2. INICIALIZACIÓN DE LA APLICACIÓN FASTAPI

app = FastAPI(
    title="Sistema NexoEventos API",
    description="API REST para la gestión del Centro de Convenciones Nexo (Parcial 2)",
    version="1.0.0"
)


# 3. MIDDLEWARE CORS (Permite comunicación fluida con Streamlit)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. RUTAs

#aqui se tienen que llamar todos los routers que se hagan
# app.include_router(clientes.router, prefix="/clientes", tags=["Clientes"])
# app.include_router(salones.router, prefix="/salones", tags=["Salones"])
# app.include_router(servicios.router, prefix="/servicios", tags=["Servicios"])
# app.include_router(staff.router, prefix="/staff", tags=["Staff"])
# app.include_router(eventos.router, prefix="/eventos", tags=["Eventos"])
# app.include_router(asistentes.router, prefix="/asistentes", tags=["Asistentes"])
# app.include_router(reportes.router, prefix="/reportes", tags=["Reportes"])
