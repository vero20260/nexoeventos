# ==============================================================================
# ROUTER: SALONES (/salones)
# ==============================================================================
# Según el documento P2 (Secciones 3, 5.1 y Módulo A regla A5):
#
# Endpoints requeridos:
# 1. GET /salones
#    - Qué hace: Retorna el catálogo completo de salones con su tamaño, capacidad,
#      precio por hora y estado de disponibilidad (activo/mantenimiento).
#    - Códigos de respuesta: 200 OK.
#    - DTO de salida: List[SalonResponse].
#
# 2. GET /salones/disponibles?inicio=...&fin=...&aforo=...
#    - Qué hace: Consulta y devuelve los salones activos que cuentan con capacidad
#      suficiente para el aforo indicado y que NO presentan cruces de horario
#      con otros eventos no cancelados (incluyendo la hora obligatoria de montaje/aseo).
#    - Implementación: Consume directamente la función de PostgreSQL A5 (fn_salones_disponibles).
#    - Ordenamiento: Del salón más pequeño que sirva al más grande.
#    - Campos retornados: salon_id, nombre, tamano, capacidad, precio_hora, costo_estimado.
#    - Códigos de respuesta:
#        * 200 OK con la lista de salones disponibles.
#        * 422 Unprocessable Entity si las fechas u horas son inválidas (ej. fin <= inicio).
# ==============================================================================
