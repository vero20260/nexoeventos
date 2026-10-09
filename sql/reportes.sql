--B. REPORTES:
--B1
CREATE OR REPLACE FUNCTION fn_b1_organigrama(p_id_staff INT DEFAULT NULL)
RETURNS TABLE (
    id_staff INT,
    nombre_staff VARCHAR,
    cargo VARCHAR,
    area VARCHAR,
    nivel INT,
    ruta_mando TEXT,
    total_personas_a_cargo INT
) AS $$
BEGIN
    RETURN QUERY
    -- Iniciamos la expresión de tabla común (CTE) recursiva llamada 'jerarquia'
    WITH RECURSIVE jerarquia AS (
        
        -- ==========================================
        -- 1. CASO BASE (El inicio del árbol)
        -- ==========================================
        SELECT 
            s.id_staff,
            s.nombre_staff,
            s.cargo,
            s.area::VARCHAR, -- Casteo a VARCHAR por si usas ENUM en PostgreSQL
            1 AS nivel,      -- El primer empleado consultado empieza en el nivel 1
            s.cargo::TEXT AS ruta_mando, -- Inicializamos la ruta visual con su cargo
            ARRAY[s.id_staff] AS camino  -- Array de IDs para llevar el rastro y evitar ciclos infinitos
        FROM staff s
        WHERE 
            -- Si no me pasan parámetro, busco a los que NO tienen jefe (La punta de la pirámide)
            (p_id_staff IS NULL AND s.jefe_id IS NULL)
            -- Si me pasan parámetro, arranco el organigrama desde esa persona específica
            OR (s.id_staff = p_id_staff)

        UNION ALL

        -- ==========================================
        -- 2. PASO RECURSIVO (Bajar al siguiente nivel)
        -- ==========================================
        SELECT 
            s.id_staff,
            s.nombre_staff,
            s.cargo,
            s.area::VARCHAR,
            j.nivel + 1, -- Bajamos un nivel en la jerarquía
            -- Concatenamos el camino que traía el jefe con el cargo del subordinado:
            j.ruta_mando || ' > ' || s.cargo, 
            -- Agregamos el ID actual al historial de visitas:
            j.camino || s.id_staff 
        FROM staff s
        -- La magia ocurre aquí: Unimos la tabla staff con la CTE 'jerarquia' 
        -- donde el jefe del empleado actual sea el empleado del paso anterior.
        INNER JOIN jerarquia j ON s.jefe_id = j.id_staff
        -- SEGURO CONTRA BUCLES: Evitamos ciclos infinitos si por error alguien pone 
        -- a un subordinado como jefe de su propio jefe.
        WHERE NOT s.id_staff = ANY(j.camino)
    )
    
    -- ==========================================
    -- 3. CONSULTA FINAL Y CÁLCULO DE SUBORDINADOS
    -- ==========================================
    SELECT 
        j.id_staff,
        j.nombre_staff,
        j.cargo,
        j.area,
        j.nivel,
        j.ruta_mando,
        (
            -- Para calcular el "total_personas_a_cargo" (directas e indirectas), 
            -- necesitamos otra subconsulta recursiva independiente por cada fila.
            WITH RECURSIVE conteo_subordinados AS (
                -- Caso base: Sus subordinados directos
                SELECT s2.id_staff FROM staff s2 WHERE s2.jefe_id = j.id_staff
                UNION ALL
                -- Paso recursivo: Los subordinados de sus subordinados
                SELECT s3.id_staff FROM staff s3 
                INNER JOIN conteo_subordinados cs ON s3.jefe_id = cs.id_staff
            )
            -- Contamos todos los registros resultantes
            SELECT COUNT(*)::INT FROM conteo_subordinados
        ) AS total_personas_a_cargo
    FROM jerarquia j
    ORDER BY j.camino; -- Ordena visualmente respetando la estructura de árbol
END;
$$ LANGUAGE plpgsql;


-- B2. Cadena de escalamiento (CTE recursiva)
CREATE OR REPLACE FUNCTION cadena_escalamiento(p_staff_id INT)
RETURNS TABLE (paso INT, id_staff INT, nombre VARCHAR, cargo VARCHAR, area VARCHAR, correo VARCHAR) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE escalamiento AS ( -- empleado inicio
        SELECT 1 AS paso, s.id_staff, s.nombre_staff, s.cargo, s.area, s.correo, s.jefe_id
        FROM staff s
        WHERE s.id_staff = p_staff_id

        UNION ALL

        -- subir al jefe directo
        SELECT e.paso + 1, t.id_staff, t.nombre_staff, t.cargo, t.area, t.correo, t.jefe_id
        FROM staff t
        JOIN escalamiento e ON t.id_staff = e.jefe_id
    )
    SELECT esc.paso, esc.id_staff, esc.nombre_staff AS nombre, esc.cargo, esc.area, esc.correo
    FROM escalamiento esc
    ORDER BY esc.paso ASC;
END;
$$ LANGUAGE plpgsql;

--B3. 
CREATE OR REPLACE VIEW vista_ranking_clientes AS
SELECT e.cliente_id, COUNT(e.estado_evento) AS total_eventos ,SUM(e.subtotal) AS total_facturado,RANK() OVER (ORDER BY SUM(e.subtotal) DESC) AS Ranking, 
(SUM(e.subtotal)*100 /(SUM(SUM(e.subtotal)) OVER())) AS Porcentaje_participacion, (SUM(SUM(e.subtotal)) OVER (ORDER BY SUM(e.subtotal) DESC )*100 /SUM(SUM(e.subtotal))OVER()) AS Porcentaje_acumulado
FROM eventos e
WHERE e.estado_evento<>'Cancelado'
GROUP BY e.cliente_id;


-- B.4 Ocupación de salones y tiempos muertos (funciones de ventana).
-- se crea una vista para almacenar la consulta del reporte
CREATE OR REPLACE VIEW vista_ocupacion_salones AS

-- Paso 1: Se crea una tabla temporal para calcular la duración de cada evento en horas
WITH eventos_duracion_horas AS (
    SELECT 
        e.id_evento AS evento_id, -- miramos el id del evento
        e.salon_id, -- miramos el id del salon
        s.nombre_salon AS nombre_salon, -- miramos el nombre del salon y lo llamamos nombre_salon
        e.nombre_evento AS nombre_evento, -- miramos el nombre del evento y lo llamamos nombre_evento
        e.inicio_evento AS inicio, -- miramos la fecha y hora de inicio del evento
        e.fin_evento AS fin, -- miramos la fecha y hora de fin del evento
        -- Calculamos la duración del evento actual en horas
        -- con EXTRACT(EPOCH FROM ...) calculamos los segundos de diferencia entre el fin y el inicio
        -- Dividimos por 3600 (segundos en 1 hora) para obtener las horas exactas 
        ROUND((EXTRACT(EPOCH FROM (e.fin_evento - e.inicio_evento)) / 3600.0)::numeric, 2) AS duracion_horas
    FROM eventos e
    INNER JOIN salones s ON e.salon_id = s.id_salon -- miramos que el evento sea en ese salon
    WHERE e.estado_evento != 'Cancelado' -- Filtramos para ignorar eventos cancelados 
)
-- creamos la consulta principal con las funciones de ventana
SELECT 
    nombre_salon,
    nombre_evento,
    inicio,
    fin,
    duracion_horas,
    --ennumeramos los eventos por salon 
    ROW_NUMBER() OVER (
        PARTITION BY salon_id 
        ORDER BY inicio
    ) AS numero_evento_salon,
    -- miramos el nombre del evento anterior en ese salon 
    LAG(nombre_evento) OVER (
        PARTITION BY salon_id 
        ORDER BY inicio
    ) AS evento_anterior,
    -- miramos los dias que el salon estuvo libre desde que terminó el evento anterior
    ROUND((
        EXTRACT(EPOCH FROM (
            inicio - LAG(fin) OVER (PARTITION BY salon_id ORDER BY inicio) -- Restamos la hora de inicio de este evento menos la hora de fin del evento anterior (LAG(fin))
        )) / 86400.0
    )::numeric, 2) AS dias_libre_desde_anterior, -- se convierte la diferencia de segundos a dias (1 dia tiene 86400 segundos)
    -- miramos las horas acumuladas 
    SUM(duracion_horas) OVER (
        PARTITION BY salon_id 
        ORDER BY inicio
    ) AS horas_reservadas_acumuladas

FROM eventos_duracion_horas
ORDER BY nombre_salon, inicio;
