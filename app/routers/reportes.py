# ==============================================================================
# ROUTER: REPORTES ANALÍTICOS Y BI (/reportes)
# ==============================================================================
# Según el documento P2 (Sección 4 Módulo B, Sección 5.1 y 8.3):
#
# Regla de implementación:
# - La API consulta estos cuatro reportes ejecutando SQL parametrizado
#   (usando text(...) de SQLAlchemy) contra las funciones o vistas creadas en PostgreSQL.
# - NO deben ser reescritos ni procesados en memoria con el ORM de Python.
#
# Endpoints requeridos:
#
# 1. GET /reportes/organigrama?staff_id=...
#    - Módulo B1: Organigrama (CTE recursiva).
#    - Dado un miembro del staff (o toda la organización si no se pasa parámetro),
#      lista a todas las personas que dependen de él directa o indirectamente.
#    - Retorna: id_staff, nombre, cargo, area, nivel jerárquico, ruta de mando
#      (ej. «Directora > Gerente > Jefe») y el total de personas que tiene a cargo.
#    - Protegido contra ciclos en la jerarquía.
#
# 2. GET /reportes/escalamiento/{staff_id}
#    - Módulo B2: Cadena de escalamiento (CTE recursiva).
#    - Dado un miembro del staff, lista en orden ascendente a todos sus jefes hasta
#      llegar a la Dirección General. Responde a: "¿A quién escalo un incidente?".
#
# 3. GET /reportes/ranking-clientes
#    - Módulo B3: Ranking de clientes y análisis de Pareto (Funciones de ventana).
#    - Por cada cliente lista: número de eventos no cancelados, total facturado acumulado,
#      posición en el ranking, porcentaje de participación y porcentaje acumulado (regla 80/20).
#    - Utiliza: SUM(...) OVER () y SUM(...) OVER (ORDER BY ...).
#
# 4. GET /reportes/ocupacion-salones
#    - Módulo B4: Ocupación de salones y tiempos muertos (Funciones de ventana).
#    - Por cada salón y en orden cronológico, lista cada evento no cancelado indicando:
#      número secuencial de evento en el salón, evento anterior, días que el salón
#      estuvo libre desde que terminó el anterior y horas reservadas acumuladas.
#    - Utiliza: LAG(...) con PARTITION BY salon_id ORDER BY inicio.
# ==============================================================================
