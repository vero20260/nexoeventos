# ==============================================================================
# MAIN.PY - PUNTO DE ENTRADA PRINCIPAL DE LA API FASTAPI
# ==============================================================================
# Según el documento P2 (Sección 5.1 Backend y Requisitos adicionales):
#
# Este archivo debe encargarse de:
# 1. Crear las tablas en PostgreSQL con:
#       Base.metadata.create_all(bind=engine)
#    (Opcionalmente, ejecutar o aplicar los scripts SQL de triggers, funciones y
#    vistas ubicados en /sql para garantizar idempotencia al iniciar la API).
#
# 2. Instanciar la aplicación FastAPI:
#       app = FastAPI(
#           title="Sistema NexoEventos API",
#           description="API REST para la gestión del Centro de Convenciones Nexo",
#           version="1.0.0"
#       )
#
# 3. Configurar Middleware (por ejemplo CORS) para permitir que el Frontend
#    de Streamlit u otros clientes se comuniquen sin bloqueos.
#
# 4. Registrar los routers modulares de la aplicación:
#       - app.include_router(clientes.router, prefix="/clientes", tags=["Clientes"])
#       - app.include_router(salones.router, prefix="/salones", tags=["Salones"])
#       - app.include_router(servicios.router, prefix="/servicios", tags=["Servicios"])
#       - app.include_router(staff.router, prefix="/staff", tags=["Staff"])
#       - app.include_router(eventos.router, prefix="/eventos", tags=["Eventos"])
#       - app.include_router(asistentes.router, prefix="/asistentes", tags=["Asistentes"])
#       - app.include_router(reportes.router, prefix="/reportes", tags=["Reportes"])
#
# 5. Manejador Global de Errores (CRÍTICO SEGÚN P2):
#    - Códigos HTTP coherentes:
#        * 201 al crear registros
#        * 404 si el recurso no existe
#        * 409 cuando un trigger rechaza la operación (DatabaseError / IntegrityError).
#          LA RESPUESTA 409 DEBE INCLUIR EL MENSAJE DE LA REGLA VIOLADA (exc.orig),
#          NO UNA TRAZA DE PYTHON.
#        * 422 cuando los datos son inválidos según los DTOs de Pydantic.
#    - Ninguna excepción de base de datos no controlada debe romper la API en un error 500
#      sin formato amigable.
#
# 6. Documentación Swagger automática disponible en /docs y /redoc.
# ==============================================================================
