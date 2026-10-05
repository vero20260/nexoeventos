# ==============================================================================
# APP/SCHEMAS.PY - DTOs (DATA TRANSFER OBJECTS) CON PYDANTIC
# ==============================================================================
# Según el documento P2 (Sección 5.1 Backend, 8.4 y Ejemplos de la Sección 9):
#
# Reglas clave de diseño:
# 1. Separación de esquemas:
#    - XxxCreate / XxxUpdate: Validan la carga útil (payload) que entra desde el cliente.
#    - XxxResponse: Modela la respuesta que sale hacia el cliente.
#      DEBE incluir `model_config = ConfigDict(from_attributes=True)` (en Pydantic v2)
#      o `class Config: orm_mode = True` (en Pydantic v1) para convertir entidades ORM.
#
# 2. Validaciones a nivel de DTO (antes de tocar la base de datos):
#    - P2 pág. 14: "Un evento con la hora de fin anterior al inicio responde HTTP 422
#      con el mensaje «La fecha/hora de fin debe ser posterior a la de inicio»."
#      (Implementar con @model_validator o @root_validator).
#    - Aforo esperado > 0, tipos permitidos, precios y cantidades válidas.
#
# 3. Modelos requeridos a implementar:
#
#    A. Clientes:
#       - ClienteBase: documento, tipo_cliente ('Natural'/'Empresa'), nombre, correo, telefono
#       - ClienteCreate(ClienteBase)
#       - ClienteResponse(ClienteBase): id_cliente, fecha_registro
#
#    B. Salones:
#       - SalonResponse: id_salon, nombre, tamano, capacidad, precio_hora, disponible
#       - SalonDisponibleResponse: salon_id, nombre, tamano, capacidad, precio_hora, costo_estimado (según A5)
#
#    C. Servicios:
#       - ServicioResponse: id_servicio, nombre, categoria, modo_cobro, precio_unitario, activo
#       - EventoServicioCreate: id_servicio, cantidad (opcional, calculada por defecto si no se pasa)
#       - EventoServicioResponse: id_evento_servicio, id_evento, id_servicio, cantidad, precio_unitario, subtotal
#
#    D. Staff:
#       - StaffCreate: nombre, cargo, area, correo, fecha_ingreso, jefe_id (opcional)
#       - StaffResponse: id_staff, nombre, cargo, area, correo, fecha_ingreso, jefe_id
#
#    E. Eventos:
#       - EventoCreate: cliente_id, salon_id, nombre, tipo, inicio, fin, aforo_esperado, coordinador_id
#         * Validación: fin > inicio (HTTP 422 si falla).
#       - EventoReprogramar: salon_id (opcional), inicio (opcional), fin (opcional), aforo_esperado (opcional)
#       - EventoEstadoUpdate: estado ('Confirmado', 'Finalizado', 'Cancelado')
#       - EventoResponse: id_evento, cliente_id, salon_id, nombre, tipo, inicio, fin, aforo_esperado,
#         coordinador_id, estado, total, tasa_asistencia
#       - EventoDetalleResponse: EventoResponse con lista de servicios contratados y resumen de inscritos/asistencia
#       - CotizacionResponse: desglose de costos: costo_salon + servicios = total
#
#    F. Asistentes e Inscripciones:
#       - AsistenteCreate: documento, nombre, correo, empresa
#       - AsistenteResponse: id_asistente, documento, nombre, correo, empresa
#       - InscripcionCreate: id_asistente
#       - InscripcionResponse: id_inscripcion, id_evento, id_asistente, fecha_inscripcion, check_in
#       - CheckInRequest: documento (para registrar asistencia en puerta)
#
#    G. Auditoría:
#       - AuditoriaResponse: campo, valor_anterior, valor_nuevo, usuario, fecha
#
#    H. Reportes Analíticos (Módulo B):
#       - OrganigramaItem (B1): id_staff, nombre, cargo, area, nivel, ruta_mando, personas_a_cargo
#       - EscalamientoItem (B2): id_staff, nombre, cargo, nivel_jerarquico
#       - RankingClienteItem (B3): cliente_id, nombre, eventos_validos, total_facturado, ranking, porcentaje, porcentaje_acumulado
#       - OcupacionSalonItem (B4): salon_id, nombre_salon, evento_id, nombre_evento, inicio, fin, evento_anterior_id, dias_libre, horas_reservadas_acumuladas
# ==============================================================================
