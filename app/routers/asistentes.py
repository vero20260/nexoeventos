# ==============================================================================
# ROUTER: ASISTENTES (/asistentes)
# ==============================================================================
# Según el documento P2 (Secciones 1, 5.1 y tabla de endpoints mínimos):
#
# Endpoints requeridos:
# 1. GET /asistentes/
#    - Qué hace: Listar todos los visitantes/asistentes registrados o buscar
#      por documento o nombre.
#    - Códigos de respuesta: 200 OK -> List[AsistenteResponse].
#
# 2. POST /asistentes/
#    - Qué hace: Registrar a un visitante por primera vez en el sistema NexoEventos
#      con documento único, nombre completo, correo y empresa (opcional).
#    - Debe validar que el documento sea único.
#    - Códigos de respuesta:
#        * 201 Created al registrar exitosamente -> AsistenteResponse.
#        * 409 Conflict si el documento ya existe en el sistema.
#        * 422 Unprocessable Entity si los datos no son válidos.
# ==============================================================================
