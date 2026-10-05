# ==============================================================================
# ROUTER: SERVICIOS (/servicios)
# ==============================================================================
# Según el documento P2 (Secciones 2, 5.1 y tabla de endpoints mínimos):
#
# Endpoints requeridos:
# 1. GET /servicios
#    - Qué hace: Retorna el catálogo oficial de servicios disponibles del centro de
#      convenciones (Estación de café, Refrigerios, Sonido básico/profesional, Multimedia, etc.)
#      junto con su categoría, modo de cobro ('Por persona', 'Por hora', 'Por unidad')
#      y su precio unitario en COP.
#    - Códigos de respuesta: 200 OK.
#    - DTO de salida: List[ServicioResponse].
#
# Nota:
# - La configuración de servicios contratados para un evento específico se gestiona
#   a través de las rutas de eventos (/eventos/{id}/servicios) según el diseño de P2.
# ==============================================================================
