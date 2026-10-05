# ==============================================================================
# ROUTER: CLIENTES (/clientes)
# ==============================================================================
# Según el documento P2 (Sección 5.1 y tabla de endpoints mínimos):
#
# Endpoints requeridos:
# 1. GET /clientes/
#    - Qué hace: Listar todos los clientes o buscar por documento/nombre.
#    - Códigos de respuesta: 200 OK.
#    - DTO de salida: List[ClienteResponse].
#
# 2. POST /clientes/
#    - Qué hace: Registrar un nuevo cliente (Persona Natural o Empresa con NIT).
#    - Valida que el documento sea único.
#    - Códigos de respuesta:
#        * 201 Created al registrar exitosamente.
#        * 409 Conflict si el documento ya se encuentra registrado.
#        * 422 Unprocessable Entity si los datos no cumplen con los tipos/validaciones.
#    - DTO de entrada: ClienteCreate.
#    - DTO de salida: ClienteResponse.
#
# 3. GET /clientes/{id}/eventos
#    - Qué hace: Retorna la lista de eventos asociados al cliente con dicho ID.
#    - Códigos de respuesta:
#        * 200 OK si existe el cliente (retorna lista de eventos).
#        * 404 Not Found si el cliente no existe.
# ==============================================================================
