--A.1 Disponibilidad y capacidad del salón (trigger). 
CREATE OR REPLACE FUNCTION validar_disponibilidad_capacidad() 
RETURNS TRIGGER AS $$
DECLARE
    v_capacidad INT; -- capacidad del salon
    v_cruce_salon RECORD; -- para ver si el salon se cruza con otro evento
    v_disponible BOOL; -- disponibilidad del salon
    v_nombre_salon VARCHAR (100); -- nombre del salon
BEGIN
    IF NEW.estado_evento = 'Cancelado' THEN --miramos si el evento esta o pasa a cancelado 
        RETURN NEW; --un vnto cancelado libera el salon 
    END IF;

    SELECT capacidad, disponible, nombre_salon INTO v_capacidad, v_disponible, v_nombre_salon --miramos las variables originales y las metemos en las temporales
    FROM salones 
    WHERE id_salon = NEW.salon_id; --buscamos el salon por el id

    IF NEW.aforo_esperado > v_capacidad THEN --comparamos el aforo con la capacidad
        RAISE EXCEPTION 'ERROR: El aforo de % personas excede a la capacidad del salón %, que es de % personas.', --si el aforo es mayor a la capacidad bota error
                        NEW.aforo_esperado, v_nombre_salon, v_capacidad; --le damos los datos en el orden que se ponen en el texto 
    END IF;
    IF v_disponible = FALSE THEN --miramos si el salon esta disponible
        RAISE EXCEPTION 'El salón % se encuentra deshablitado temporalmente', -- lanza error si esta deshabilitado 
                        v_nombre_salon; --le damos el nombre del salon 
    END IF;
    SELECT id_evento, nombre_evento, inicio_evento, fin_evento INTO v_cruce_salon --miramos las variables originales y las metemos en las temporales
    FROM eventos --tomamos los datos de la tabla ventos 
    WHERE salon_id = NEW.salon_id AND estado_evento != 'Cancelado' AND id_evento IS DISTINCT FROM NEW.id_evento --miramos que no se solapen los eventos con la hora extra
    AND NEW.inicio_evento < (fin_evento + INTERVAL '1 hour') --contamos la hora de montaje entre eventos 
    AND NEW.fin_evento > (inicio_evento - INTERVAL '1 hour') --contamos la hora de desmontaje entre eventos 
    LIMIT 1; -- limitamos a 1 por si hay algun problema 
    IF FOUND THEN --si se encuentra un evento lanza error
        RAISE EXCEPTION 'ERROR: El Salon % se encuentra reservado para el vento % de % a %', --muestra el error
                        v_nombre_salon, v_cruce_salon.nombre_evento, v_cruce_salon.inicio_evento, v_cruce_salon.fin_evento; --le damos los datos en el orden que se ponen en el texto 
    END IF;
    RETURN NEW; 
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validar_disponibilidad_capacidad ON eventos;
CREATE TRIGGER trg_validar_disponibilidad_capacidad
BEFORE INSERT OR UPDATE ON eventos
FOR EACH ROW
EXECUTE FUNCTION validar_disponibilidad_capacidad();

--A.2
CREATE OR REPLACE FUNCTION fn_trg_inscripciones_asistencia()
RETURNS TRIGGER AS $$
DECLARE
    -- Variables para almacenar temporalmente los datos del evento
    v_estado_evento VARCHAR;
    v_aforo_esperado INT;
    v_inscritos_actuales INT;
    v_inicio_evento TIMESTAMP;
    v_fin_evento TIMESTAMP;
BEGIN
    -- [Paso A] Obtener la configuración actual del evento al que intentan inscribirse
    SELECT estado_evento, aforo_esperado, inicio_evento, fin_evento
    INTO v_estado_evento, v_aforo_esperado, v_inicio_evento, v_fin_evento
    FROM eventos
    WHERE id_evento = NEW.id_evento;

    -- REGLA 1: No se permiten inscripciones en eventos Cancelados o Finalizados


    IF LOWER(v_estado_evento) IN ('cancelado', 'finalizado') THEN
        RAISE EXCEPTION 'A2_ESTADO_INVALIDO: Operación denegada. El evento se encuentra %.', v_estado_evento;
    END IF;

    -- ==========================================================
    -- REGLA 2: Límite de Aforo (Cupos)
    -- Aplica SOLO para: INSERT (No queremos validar aforo si solo están haciendo un UPDATE del check-in)
    -- ==========================================================
    IF TG_OP = 'INSERT' THEN
        -- Contamos cuánta gente hay inscrita actualmente
        SELECT COUNT(*)
        INTO v_inscritos_actuales
        FROM inscripciones
        WHERE id_evento = NEW.id_evento;

        -- Validamos que los inscritos actuales no superen ni igualen el aforo esperado
        IF v_inscritos_actuales >= v_aforo_esperado THEN
            RAISE EXCEPTION 'A2_AFORO_LLENO: El evento alcanzó su aforo máximo contratado de % asistentes.', v_aforo_esperado;
        END IF;
    END IF;

    -- ==========================================================
    -- REGLA 3 y 4: Validación lógica del Check-in
    -- Aplica para: Cuando el campo check_in no es nulo (alguien intentó registrar asistencia)
    -- ==========================================================
    IF NEW.check_in IS NOT NULL THEN
        
        -- Regla 3: Solo una vez por asistente (Evitar check-ins duplicados)
        -- Si es un UPDATE, verificamos que el asistente no tuviera ya una hora registrada previamente
        IF TG_OP = 'UPDATE' AND OLD.check_in IS NOT NULL AND OLD.check_in <> NEW.check_in THEN
            RAISE EXCEPTION 'A2_CHECKIN_DUPLICADO: El asistente ya cuenta con un check-in registrado en este evento.';
        END IF;

        -- Regla 4: Ventana de tiempo permitida (1 hora antes del inicio hasta el fin del evento)
        IF NEW.check_in < (v_inicio_evento - INTERVAL '1 hour') OR NEW.check_in > v_fin_evento THEN
            RAISE EXCEPTION 'A2_HORARIO_CHECKIN: El check-in solo es válido desde % hasta %. Hora registrada: %', 
                            (v_inicio_evento - INTERVAL '1 hour'), v_fin_evento, NEW.check_in;
        END IF;

    END IF;

    -- Si el script llega a este punto sin ejecutar ningún 'RAISE EXCEPTION',
    -- significa que pasó todas las reglas. Retornamos 'NEW' para que la BD guarde el registro.
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- 2. ASIGNACIÓN DEL TRIGGER A LA TABLA
-- NOTA: Se borra primero por idempotecia (para que puedas correr el script múltiples veces sin error).
DROP TRIGGER IF EXISTS trg_inscripciones_asistencia ON inscripciones;

CREATE TRIGGER trg_inscripciones_asistencia
BEFORE INSERT OR UPDATE ON inscripciones
FOR EACH ROW
EXECUTE FUNCTION fn_trg_inscripciones_asistencia();



---A.3
-- A3. Liquidación automática del evento 
CREATE OR REPLACE FUNCTION liquidacion_auto_evento()
RETURNS TRIGGER AS $$
DECLARE
    v_estado VARCHAR(20);
    v_aforo INT;
    v_inicio TIMESTAMP;
    v_fin TIMESTAMP;
    v_precio_catalogo NUMERIC(12,2);
    v_se_cobra VARCHAR(20);
    v_horas INT;
    v_costo_salon NUMERIC(12,2) := 0;
    v_costo_servicios NUMERIC(12,2) := 0;
BEGIN
    -- Estado
    SELECT estado_evento, aforo_esperado, inicio_evento, fin_evento INTO v_estado, v_aforo, v_inicio, v_fin 
    FROM eventos 
    WHERE id_evento = COALESCE(NEW.id_evento, OLD.id_evento); -- COALESCE es para elegir el primer id q no sea NULL

    IF LOWER(v_estado) IN ('finalizado', 'cancelado') THEN
        RAISE EXCEPTION 'No se pueden modificar los servicios de un evento finalizado o cancelado.';
    END IF;

    -- congelar precio y calcular por defecto
    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        SELECT precio_unitario, modo_cobro INTO v_precio_catalogo, v_se_cobra 
        FROM servicios 
        WHERE id_servicio = NEW.id_servicio;

        -- congelar precio si no se indica
        IF NEW.precio_unitario IS NULL THEN
            NEW.precio_unitario := v_precio_catalogo;
        END IF;

        -- cantidad por defecto
        IF NEW.cantidad IS NULL OR NEW.cantidad <= 0 THEN
            IF v_se_cobra = 'Por persona' THEN
                NEW.cantidad := v_aforo;
            ELSIF v_se_cobra = 'Por hora' THEN
                v_horas := CEILING(EXTRACT(EPOCH FROM (v_fin - v_inicio)) / 3600.0); -- CEILING para redondear hacia arriba
                IF v_horas < 1 THEN v_horas := 1; END IF;
                NEW.cantidad := v_horas;
            ELSE
                NEW.cantidad := 1;
            END IF;
        END IF;

        -- subtotal de ese servicio
        NEW.total_evento_servicios := NEW.cantidad * NEW.precio_unitario;
    END IF;

    -- recalcular el valor_total del evento
    SELECT CEILING(EXTRACT(EPOCH FROM (e.fin_evento - e.inicio_evento)) / 3600.0) * s.precio_hora
    INTO v_costo_salon
    FROM eventos e
    JOIN salones s ON e.salon_id = s.id_salon
    WHERE e.id_evento = COALESCE(NEW.id_evento, OLD.id_evento);

    -- suma de todos los servicios del evento
    SELECT COALESCE(SUM(total_evento_servicios), 0)
    INTO v_costo_servicios
    FROM evento_servicios
    WHERE id_evento = COALESCE(NEW.id_evento, OLD.id_evento)
      AND id_evento_servicio != COALESCE(NEW.id_evento_servicio, 0); -- excluye la fila anterior en updates

    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        v_costo_servicios := v_costo_servicios + NEW.total_evento_servicios;
    END IF;

    -- guardar subtotal actualizado en la tabla eventos
    UPDATE eventos
    SET subtotal = COALESCE(v_costo_salon, 0) + v_costo_servicios
    WHERE id_evento = COALESCE(NEW.id_evento, OLD.id_evento);

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS liquidacion_auto_evento ON evento_servicios;
CREATE TRIGGER liquidacion_auto_evento
BEFORE INSERT OR UPDATE OR DELETE ON evento_servicios
FOR EACH ROW EXECUTE FUNCTION liquidacion_auto_evento();

-- En eventos al reprogramar salon o horarios
CREATE OR REPLACE FUNCTION recalcular_total_reprogramacion()
RETURNS TRIGGER AS $$
DECLARE
    v_horas INT;
    v_precio_salon NUMERIC(12,2);
    v_costo_salon NUMERIC(12,2);
    v_costo_servicios NUMERIC(12,2);
BEGIN
    SELECT precio_hora INTO v_precio_salon FROM salones WHERE id_salon = NEW.salon_id;
    
    v_horas := CEILING(EXTRACT(EPOCH FROM (NEW.fin_evento - NEW.inicio_evento)) / 3600.0);
    IF v_horas < 1 THEN v_horas := 1; END IF;

    v_costo_salon := v_horas * v_precio_salon;

    SELECT COALESCE(SUM(total_evento_servicios), 0)
    INTO v_costo_servicios
    FROM evento_servicios
    WHERE id_evento = NEW.id_evento;

    NEW.subtotal := v_costo_salon + v_costo_servicios;     -- actualizar columna subtotal

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS recalcular_total_reprogramacion ON eventos;
CREATE TRIGGER recalcular_total_reprogramacion
BEFORE INSERT OR UPDATE OF salon_id, inicio_evento, fin_evento ON eventos
FOR EACH ROW EXECUTE FUNCTION recalcular_total_reprogramacion();



---A.4 

CREATE OR REPLACE FUNCTION cierre_evento_y_auditoria()
RETURNS TRIGGER AS $$
DECLARE 
n_asistentes INT;
n_inscritos INT;
tasa_asistentes NUMERIC(5,2);
usuario VARCHAR;
  BEGIN
    IF (OLD.estado_evento<>'Finalizado' AND OLD.estado_evento<>'Cancelado')THEN
      usuario := current_setting('app.usuario_actual', true);
      IF (OLD.salon_id <> NEW.salon_id )THEN  
        INSERT INTO auditoria_eventos (id_evento, campo, valor_anterior, valor_nuevo, fecha_cambio, usuario_cambio) VALUES (OLD.id_evento,'salon_id', OLD.salon_id::VARCHAR, NEW.salon_id::VARCHAR, CURRENT_TIMESTAMP, usuario);
      END IF;IF (OLD.inicio_evento <> NEW.inicio_evento )THEN 
        INSERT INTO auditoria_eventos (id_evento, campo, valor_anterior, valor_nuevo, fecha_cambio, usuario_cambio) VALUES (OLD.id_evento,'inicio_evento', OLD.inicio_evento::VARCHAR, NEW.inicio_evento::VARCHAR, CURRENT_TIMESTAMP, usuario);
      END IF;IF (OLD.fin_evento <> NEW.fin_evento )THEN  
        INSERT INTO auditoria_eventos (id_evento, campo, valor_anterior, valor_nuevo, fecha_cambio, usuario_cambio) VALUES (OLD.id_evento,'fin_evento', OLD.fin_evento::VARCHAR, NEW.fin_evento::VARCHAR, CURRENT_TIMESTAMP, usuario);
      END IF;IF (OLD.estado_evento <> NEW.estado_evento )THEN  
        INSERT INTO auditoria_eventos (id_evento, campo, valor_anterior, valor_nuevo, fecha_cambio, usuario_cambio) VALUES (OLD.id_evento,'estado_evento', OLD.estado_evento, NEW.estado_evento, CURRENT_TIMESTAMP, usuario);
      END IF;
      IF (NEW.estado_evento='finalizado') THEN
        IF(CURRENT_TIMESTAMP>OLD.fin_evento) THEN
          SELECT COUNT(*)
          INTO n_asistentes
          FROM inscripciones i 
          WHERE i.id_evento=OLD.id_evento AND i.check_in IS NOT NULL;
          SELECT COUNT(*)
          INTO n_inscritos
          FROM inscripciones i 
          WHERE i.id_evento=OLD.id_evento;
          IF (n_inscritos=0) THEN 
            tasa_asistentes:=NULL;
          ELSE
            tasa_asistentes:=(n_asistentes::NUMERIC/n_inscritos::NUMERIC*100);
          END IF;
          NEW.tasa_asistencia:=tasa_asistentes;
        ELSE 
          RAISE EXCEPTION 'No es posible finalizar un evento antes de su hora final';
        END IF;
      END IF;
    ELSIF (OLD.estado_evento='finalizado' OR OLD.estado_evento='cancelado') THEN
      RAISE EXCEPTION 'No es posible cambiar un estado finalizado o cancelado';
    END IF;
    RETURN NEW;
  END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS dis_cierre_auditoria ON eventos;
CREATE TRIGGER dis_cierre_auditoria
 BEFORE UPDATE ON eventos
 FOR EACH ROW
 EXECUTE FUNCTION cierre_evento_y_auditoria();


-- A5. Salones disponibles (función)
CREATE OR REPLACE FUNCTION salones_disponibles(p_inicio TIMESTAMP, p_fin TIMESTAMP, p_aforo INT)
RETURNS TABLE (id_salon INT, nombre_salon VARCHAR,tamano VARCHAR, capacidad INT, precio_hora NUMERIC(12,2), costo_estimado NUMERIC(12,2)) AS $$
DECLARE
    v_horas INT;
BEGIN
    v_horas := CEILING(EXTRACT(EPOCH FROM (p_fin - p_inicio)) / 3600.0); -- calculo horas
    IF v_horas < 1 THEN 
        v_horas := 1; 
    END IF;

    -- filtro salones activos y disponibles
    RETURN QUERY
    SELECT s.id_salon, s.nombre_salon, s.tamano, s.capacidad, s.precio_hora, (v_horas * s.precio_hora)::NUMERIC(12,2) AS costo_estimado
    FROM salones s
    WHERE s.disponible = TRUE  -- habilitado
      AND s.capacidad >= p_aforo
      AND NOT EXISTS (
          SELECT 1 
          FROM eventos e
          WHERE e.salon_id = s.id_salon
            AND LOWER(e.estado_evento) != 'cancelado'
            AND (p_inicio - INTERVAL '1 hour') < e.fin_evento
            AND (p_fin + INTERVAL '1 hour') > e.inicio_evento
      )
    ORDER BY s.capacidad ASC, s.precio_hora ASC;  -- Del más pequeño al más grande [P2.pdf]
END;
$$ LANGUAGE plpgsql;


