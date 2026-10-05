# ==============================================================================
# ROUTER: EVENTOS (/eventos) - MÓDULO CENTRAL DEL SISTEMA
# ==============================================================================
# Según el documento P2 (Secciones 1, 3, 5.1 y ejemplos de la Sección 9):
#
# Aspectos fundamentales de integración:
# 1. Auditoría y Usuario de la aplicación (Pista A4):
#    - La API recibe quién hace la operación mediante el encabezado HTTP:
#         X-Usuario: <nombre_usuario> (por ejemplo: X-Usuario: farango)
#    - Antes de ejecutar operaciones que modifican eventos (POST, PATCH),
#      se debe ejecutar en la transacción de PostgreSQL:
#         db.execute(text("SELECT set_config('app.current_user', :user, true)"), {"user": usuario})
#      para que los triggers de auditoría (A4) puedan leerlo con current_setting('app.current_user', true).
#
# 2. Refresco post-trigger:
#    - Después de db.commit(), siempre ejecutar db.refresh(evento) para cargar los
#      valores calculados por los triggers (total, tasa de asistencia, etc.).
#
# 3. Manejo de excepciones de negocio:
#    - Cuando un trigger lanza RAISE EXCEPTION (por ejemplo A1, A2, A3, A4),
#      capturar la excepción SQLAlchemy y devolver HTTP 409 con el mensaje limpio
#      proveniente de exc.orig, sin trazas técnicas de Python.
#
# ------------------------------------------------------------------------------
# Endpoints requeridos:
# ------------------------------------------------------------------------------
#
# 1. GET /eventos/
#    - Listar eventos con filtros opcionales (por estado, cliente, fecha, salón).
#    - Respuesta: 200 OK -> List[EventoResponse].
#
# 2. POST /eventos/
#    - Crear evento (nace en estado 'Cotizado').
#    - Header requerido: X-Usuario.
#    - Valida trigger A1 (capacidad del salón, salón habilitado, no cruces con 1h de montaje).
#    - El trigger A3 calcula el alquiler inicial del salón en el valor total.
#    - Respuestas:
#        * 201 Created -> EventoResponse.
#        * 409 Conflict si viola A1 (salón ocupado, aforo > capacidad, etc.).
#        * 422 Unprocessable Entity si fin <= inicio.
#
# 3. GET /eventos/{id}
#    - Obtener detalle completo del evento: datos generales, servicios contratados,
#      resumen de inscritos y asistencia.
#    - Respuestas: 200 OK -> EventoDetalleResponse, 404 Not Found si no existe.
#
# 4. PATCH /eventos/{id}
#    - Reprogramar evento: cambio de salón, fechas/horario o aforo esperado.
#    - Header requerido: X-Usuario (registra cambio en auditoría A4).
#    - Valida trigger A1 y recalcula valor total con A3.
#    - Respuestas: 200 OK -> EventoResponse, 409 si cruza o si está Finalizado/Cancelado.
#
# 5. PATCH /eventos/{id}/estado
#    - Cambiar estado: 'Cotizado' -> 'Confirmado', 'Confirmado' -> 'Finalizado' o 'Cancelado'.
#    - Header requerido: X-Usuario (registra cambio de estado en auditoría A4).
#    - Trigger A4: Finalizado y Cancelado son definitivos.
#      Solo se puede finalizar si su hora de fin ya pasó; al finalizar calcula y guarda
#      la tasa de asistencia real.
#    - Respuestas: 200 OK -> EventoResponse, 409 si regla de negocio se viola.
#
# 6. POST, PUT, DELETE /eventos/{id}/servicios
#    - Configurar los servicios del evento:
#        * POST: Agregar un servicio (congela precio de catálogo; si cantidad es nula,
#          aplica regla por persona = aforo, por hora = duración redondeada arriba).
#        * PUT: Modificar cantidad de un servicio existente.
#        * DELETE: Quitar servicio contratado.
#    - Trigger A3: No se permite modificar servicios de eventos Finalizados o Cancelados;
#      recalcula el valor total del evento en la base de datos.
#    - Respuestas: 200 OK / 201 Created / 204 No Content. 409 si el evento está cerrado.
#
# 7. GET /eventos/{id}/cotizacion
#    - Desglose detallado de costos:
#        * Costo alquiler de salón: (horas calculadas * precio por hora del salón).
#        * Lista de servicios con cantidad, precio unitario congelado y subtotal.
#        * Gran Total general.
#    - Respuestas: 200 OK -> CotizacionResponse.
#
# 8. GET /eventos/{id}/auditoria
#    - Historial de cambios del evento (tabla auditoria_eventos):
#      lista con [campo, valor_anterior, valor_nuevo, fecha, usuario].
#    - Respuestas: 200 OK -> List[AuditoriaResponse].
#
# 9. GET, POST /eventos/{id}/inscripciones
#    - GET: Lista de asistentes inscritos al evento.
#    - POST: Inscribir un asistente previamente registrado.
#      Trigger A2: No permite inscripciones en eventos Cancelados/Finalizados,
#      ni por encima del aforo esperado contratado. Tampoco asistente duplicado.
#    - Respuestas: 201 Created -> InscripcionResponse, 409 Conflict si cupo lleno.
#
# 10. POST /eventos/{id}/checkin
#     - Registrar la asistencia real en puerta mediante el documento del asistente.
#     - Trigger A2: Solo se acepta desde 1 hora antes del inicio hasta la hora de fin,
#       y solo una vez por asistente inscrito.
#     - Respuestas: 200 OK -> CheckInResponse, 409 Conflict si fuera de ventana o duplicado.
# ==============================================================================
