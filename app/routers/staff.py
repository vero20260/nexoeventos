# ==============================================================================
# ROUTER: STAFF (/staff)
# ==============================================================================
# Según el documento P2 (Secciones 1, 5.1 y tabla de endpoints mínimos):
#
# Endpoints requeridos:
# 1. GET /staff/
#    - Qué hace: Listar todos los empleados del centro de convenciones, incluyendo
#      su cargo, área (Dirección, Operaciones, Comercial, Logística, Alimentos y Bebidas,
#      Audiovisuales) y la identificación / información de su jefe inmediato.
#    - Códigos de respuesta: 200 OK.
#    - DTO de salida: List[StaffResponse].
#
# 2. POST /staff/
#    - Qué hace: Registrar un nuevo empleado. Permite asignar su jefe inmediato
#      (excepto la Dirección General que no tiene jefe inmediato, jefe_id=NULL).
#    - Debe validar que el correo no esté duplicado.
#    - Códigos de respuesta:
#        * 201 Created al registrar exitosamente.
#        * 409 Conflict si el correo ya existe o si la clave foránea del jefe no es válida.
#        * 422 Unprocessable Entity si los campos no cumplen las restricciones.
#    - DTO de entrada: StaffCreate.
#    - DTO de salida: StaffResponse.
# ==============================================================================
