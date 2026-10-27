-- ============================================================================
-- PLATAFORMA GUBERNAMENTAL URABÁ-PAÍS (SUBREGIÓN DE URABÁ, ANTIOQUIA)
-- CATÁLOGO COMPLETO DE PROCEDIMIENTOS ALMACENADOS (MYSQL STORED PROCEDURES)
-- Base de Datos: uraba_pais_db
-- Motor: MySQL Server 8.0+ / InnoDB
-- Total: 10 Procedimientos Almacenados (Analítica, Transacciones, Buscadores y Filtros)
-- ============================================================================

USE `uraba_pais_db`;

DELIMITER $$

-- ============================================================================
-- 1. ANALÍTICA: sp_resumen_indicadores_subregion
-- PROPÓSITO   : Cálculo consolidado de indicadores globales de Urabá
-- RETORNO     : Dataset con totales de beneficiarios, atenciones, participaciones y programas
-- ============================================================================
DROP PROCEDURE IF EXISTS `sp_resumen_indicadores_subregion`$$
CREATE PROCEDURE `sp_resumen_indicadores_subregion`()
BEGIN
    DECLARE v_total_beneficiarios INT DEFAULT 0;
    DECLARE v_total_atenciones INT DEFAULT 0;
    DECLARE v_total_participaciones INT DEFAULT 0;
    DECLARE v_seguimientos_pendientes INT DEFAULT 0;
    DECLARE v_total_programas INT DEFAULT 0;

    SELECT COUNT(*) INTO v_total_beneficiarios FROM beneficiarios;
    SELECT COUNT(*) INTO v_total_atenciones FROM atenciones;
    SELECT COUNT(*) INTO v_total_participaciones FROM participaciones;
    SELECT COUNT(*) INTO v_seguimientos_pendientes FROM seguimientos WHERE LOWER(estado_accion) IN ('pendiente', 'en proceso');
    SELECT COUNT(DISTINCT programa_nombre) INTO v_total_programas FROM participaciones;

    SELECT 
        v_total_beneficiarios AS total_beneficiarios,
        v_total_atenciones AS total_atenciones,
        v_total_participaciones AS total_participaciones,
        v_seguimientos_pendientes AS seguimientos_pendientes,
        v_total_programas AS total_programas,
        NOW() AS fecha_calculo,
        'Motor MySQL Server 8.0 (uraba_pais_db)' AS motor_ejecucion;
END$$

-- ============================================================================
-- 2. TRANSACCIONAL: sp_registrar_atencion_transaccional
-- PROPÓSITO   : Transacción ACID atómica que inserta atención y auditoría con ROLLBACK
-- RETORNO     : Parámetros OUT: nuevo_id, codigo_estado, mensaje
-- ============================================================================
DROP PROCEDURE IF EXISTS `sp_registrar_atencion_transaccional`$$
CREATE PROCEDURE `sp_registrar_atencion_transaccional`(
    IN p_beneficiario_id INT,
    IN p_tipo VARCHAR(255),
    IN p_fecha VARCHAR(100),
    IN p_responsable VARCHAR(255),
    IN p_descripcion TEXT,
    IN p_remision VARCHAR(255),
    IN p_usuario VARCHAR(100),
    OUT p_nuevo_id INT,
    OUT p_codigo_estado VARCHAR(50),
    OUT p_mensaje VARCHAR(255)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_nuevo_id = 0;
        SET p_codigo_estado = 'ERROR_SQL';
        SET p_mensaje = 'Fallo en la ejecución de la transacción. Se ejecutó ROLLBACK de seguridad.';
    END;

    START TRANSACTION;

    IF NOT EXISTS (SELECT 1 FROM beneficiarios WHERE id = p_beneficiario_id) THEN
        ROLLBACK;
        SET p_nuevo_id = 0;
        SET p_codigo_estado = 'BENEFICIARIO_NO_EXISTE';
        SET p_mensaje = 'El beneficiario especificado no existe en la base de datos.';
    ELSE
        INSERT INTO atenciones (beneficiario_id, tipo, fecha, responsable, descripcion, remision)
        VALUES (p_beneficiario_id, p_tipo, p_fecha, p_responsable, p_descripcion, p_remision);

        SET p_nuevo_id = LAST_INSERT_ID();

        INSERT INTO auditoria (usuario, accion, detalle, nivel, ip_origen)
        VALUES (
            IFNULL(p_usuario, 'Sistema'),
            'NUEVA_ATENCION_SP',
            CONCAT('Atención #', p_nuevo_id, ' registrada mediante Stored Procedure transaccional para el beneficiario ID #', p_beneficiario_id),
            'INFO',
            '127.0.0.1'
        );

        COMMIT;
        SET p_codigo_estado = 'EXITO';
        SET p_mensaje = 'Transacción completada exitosamente. Registro de atención y auditoría creados.';
    END IF;
END$$

-- ============================================================================
-- 3. FICHA 360: sp_ficha_resumen_beneficiario
-- PROPÓSITO   : Consolidación 360° de perfil con conteos relacionales
-- ============================================================================
DROP PROCEDURE IF EXISTS `sp_ficha_resumen_beneficiario`$$
CREATE PROCEDURE `sp_ficha_resumen_beneficiario`(
    IN p_beneficiario_id INT
)
BEGIN
    SELECT 
        b.id,
        b.codigo_interno,
        b.tipo_doc,
        b.num_doc,
        CONCAT(b.nombres, ' ', IFNULL(b.apellidos, '')) AS nombre_completo,
        b.municipio,
        b.sexo,
        b.condicion_poblacional,
        b.discapacidad,
        b.telefono,
        b.fecha_nacimiento,
        (SELECT COUNT(*) FROM participaciones p WHERE p.beneficiario_id = b.id) AS total_participaciones,
        (SELECT COUNT(*) FROM atenciones a WHERE a.beneficiario_id = b.id) AS total_atenciones,
        (SELECT COUNT(*) FROM seguimientos s WHERE s.beneficiario_id = b.id AND LOWER(s.estado_accion) IN ('pendiente', 'en proceso')) AS seguimientos_pendientes
    FROM beneficiarios b
    WHERE b.id = p_beneficiario_id;
END$$

-- ============================================================================
-- 4. SAT ALERTAS: sp_alertas_prioritarias_ivs
-- PROPÓSITO   : Focalización de alertas tempranas en el Sistema SAT
-- ============================================================================
DROP PROCEDURE IF EXISTS `sp_alertas_prioritarias_ivs`$$
CREATE PROCEDURE `sp_alertas_prioritarias_ivs`(
    IN p_municipio VARCHAR(100)
)
BEGIN
    SELECT 
        b.id,
        b.codigo_interno,
        b.tipo_doc,
        b.num_doc,
        CONCAT(b.nombres, ' ', IFNULL(b.apellidos, '')) AS nombre_completo,
        b.municipio,
        b.condicion_poblacional,
        b.discapacidad,
        b.telefono,
        CASE 
            WHEN LOWER(b.condicion_poblacional) LIKE '%víctima%' OR LOWER(b.condicion_poblacional) LIKE '%desplazad%' THEN 'CRÍTICO'
            WHEN b.discapacidad IS NOT NULL AND LOWER(b.discapacidad) NOT IN ('ninguna', 'no', '', 'sin registro') THEN 'ALTO'
            ELSE 'MODERADO'
        END AS nivel_prioridad_sat,
        (SELECT COUNT(*) FROM atenciones a WHERE a.beneficiario_id = b.id) AS total_atenciones_recibidas
    FROM beneficiarios b
    WHERE (p_municipio IS NULL OR p_municipio = '' OR b.municipio = p_municipio)
    ORDER BY 
        CASE 
            WHEN LOWER(b.condicion_poblacional) LIKE '%víctima%' OR LOWER(b.condicion_poblacional) LIKE '%desplazad%' THEN 1
            WHEN b.discapacidad IS NOT NULL AND LOWER(b.discapacidad) NOT IN ('ninguna', 'no', '', 'sin registro') THEN 2
            ELSE 3
        END,
        b.id DESC
    LIMIT 50;
END$$

-- ============================================================================
-- 5. BUSCADOR Y FILTROS: sp_buscar_beneficiarios
-- PROPÓSITO   : Búsqueda y filtrado multi-criterio de beneficiarios con paginación
-- ============================================================================
DROP PROCEDURE IF EXISTS `sp_buscar_beneficiarios`$$
CREATE PROCEDURE `sp_buscar_beneficiarios`(
    IN p_q VARCHAR(255),
    IN p_municipio VARCHAR(255),
    IN p_sexo VARCHAR(50),
    IN p_condicion VARCHAR(255),
    IN p_limit INT,
    IN p_offset INT,
    OUT p_total INT
)
BEGIN
    -- 1. Total de coincidencias
    SELECT COUNT(*) INTO p_total
    FROM beneficiarios
    WHERE (p_q IS NULL OR p_q = '' OR 
           num_doc LIKE CONCAT('%', p_q, '%') OR 
           nombres LIKE CONCAT('%', p_q, '%') OR 
           apellidos LIKE CONCAT('%', p_q, '%') OR 
           codigo_interno LIKE CONCAT('%', p_q, '%'))
      AND (p_municipio IS NULL OR p_municipio = '' OR TRIM(municipio) = TRIM(p_municipio))
      AND (p_sexo IS NULL OR p_sexo = '' OR TRIM(sexo) = TRIM(p_sexo))
      AND (p_condicion IS NULL OR p_condicion = '' OR TRIM(condicion_poblacional) = TRIM(p_condicion));

    -- 2. Página de resultados
    SELECT *
    FROM beneficiarios
    WHERE (p_q IS NULL OR p_q = '' OR 
           num_doc LIKE CONCAT('%', p_q, '%') OR 
           nombres LIKE CONCAT('%', p_q, '%') OR 
           apellidos LIKE CONCAT('%', p_q, '%') OR 
           codigo_interno LIKE CONCAT('%', p_q, '%'))
      AND (p_municipio IS NULL OR p_municipio = '' OR TRIM(municipio) = TRIM(p_municipio))
      AND (p_sexo IS NULL OR p_sexo = '' OR TRIM(sexo) = TRIM(p_sexo))
      AND (p_condicion IS NULL OR p_condicion = '' OR TRIM(condicion_poblacional) = TRIM(p_condicion))
    ORDER BY id DESC
    LIMIT p_limit OFFSET p_offset;
END$$

-- ============================================================================
-- 6. BUSCADOR Y FILTROS: sp_buscar_atenciones
-- PROPÓSITO   : Búsqueda y filtrado de atenciones con relación a beneficiarios
-- ============================================================================
DROP PROCEDURE IF EXISTS `sp_buscar_atenciones`$$
CREATE PROCEDURE `sp_buscar_atenciones`(
    IN p_q VARCHAR(255),
    IN p_tipo VARCHAR(255),
    IN p_limit INT,
    IN p_offset INT,
    OUT p_total INT
)
BEGIN
    SELECT COUNT(*) INTO p_total
    FROM atenciones a
    JOIN beneficiarios b ON a.beneficiario_id = b.id
    WHERE (p_q IS NULL OR p_q = '' OR 
           b.num_doc LIKE CONCAT('%', p_q, '%') OR 
           b.nombres LIKE CONCAT('%', p_q, '%') OR 
           b.apellidos LIKE CONCAT('%', p_q, '%') OR 
           b.codigo_interno LIKE CONCAT('%', p_q, '%') OR 
           a.tipo LIKE CONCAT('%', p_q, '%') OR 
           a.descripcion LIKE CONCAT('%', p_q, '%') OR 
           a.responsable LIKE CONCAT('%', p_q, '%'))
      AND (p_tipo IS NULL OR p_tipo = '' OR a.tipo = p_tipo);

    SELECT a.*, 
           CONCAT(b.nombres, ' ', IFNULL(b.apellidos, '')) AS beneficiario_nombre, 
           b.codigo_interno
    FROM atenciones a
    JOIN beneficiarios b ON a.beneficiario_id = b.id
    WHERE (p_q IS NULL OR p_q = '' OR 
           b.num_doc LIKE CONCAT('%', p_q, '%') OR 
           b.nombres LIKE CONCAT('%', p_q, '%') OR 
           b.apellidos LIKE CONCAT('%', p_q, '%') OR 
           b.codigo_interno LIKE CONCAT('%', p_q, '%') OR 
           a.tipo LIKE CONCAT('%', p_q, '%') OR 
           a.descripcion LIKE CONCAT('%', p_q, '%') OR 
           a.responsable LIKE CONCAT('%', p_q, '%'))
      AND (p_tipo IS NULL OR p_tipo = '' OR a.tipo = p_tipo)
    ORDER BY a.id DESC
    LIMIT p_limit OFFSET p_offset;
END$$

-- ============================================================================
-- 7. BUSCADOR Y FILTROS: sp_buscar_seguimientos
-- PROPÓSITO   : Búsqueda y filtrado de compromisos por estado de acción
-- ============================================================================
DROP PROCEDURE IF EXISTS `sp_buscar_seguimientos`$$
CREATE PROCEDURE `sp_buscar_seguimientos`(
    IN p_q VARCHAR(255),
    IN p_estado VARCHAR(100),
    IN p_limit INT,
    IN p_offset INT,
    OUT p_total INT
)
BEGIN
    SELECT COUNT(*) INTO p_total
    FROM seguimientos s
    JOIN beneficiarios b ON s.beneficiario_id = b.id
    WHERE (p_q IS NULL OR p_q = '' OR 
           b.num_doc LIKE CONCAT('%', p_q, '%') OR 
           b.nombres LIKE CONCAT('%', p_q, '%') OR 
           b.apellidos LIKE CONCAT('%', p_q, '%') OR 
           b.codigo_interno LIKE CONCAT('%', p_q, '%') OR 
           s.avance LIKE CONCAT('%', p_q, '%') OR 
           s.proxima_accion LIKE CONCAT('%', p_q, '%'))
      AND (p_estado IS NULL OR p_estado = '' OR s.estado_accion = p_estado);

    SELECT s.*, 
           CONCAT(b.nombres, ' ', IFNULL(b.apellidos, '')) AS beneficiario_nombre, 
           b.codigo_interno
    FROM seguimientos s
    JOIN beneficiarios b ON s.beneficiario_id = b.id
    WHERE (p_q IS NULL OR p_q = '' OR 
           b.num_doc LIKE CONCAT('%', p_q, '%') OR 
           b.nombres LIKE CONCAT('%', p_q, '%') OR 
           b.apellidos LIKE CONCAT('%', p_q, '%') OR 
           b.codigo_interno LIKE CONCAT('%', p_q, '%') OR 
           s.avance LIKE CONCAT('%', p_q, '%') OR 
           s.proxima_accion LIKE CONCAT('%', p_q, '%'))
      AND (p_estado IS NULL OR p_estado = '' OR s.estado_accion = p_estado)
    ORDER BY s.id DESC
    LIMIT p_limit OFFSET p_offset;
END$$

-- ============================================================================
-- 8. BUSCADOR Y FILTROS: sp_buscar_participaciones
-- PROPÓSITO   : Búsqueda y filtrado de participaciones en programas sociales
-- ============================================================================
DROP PROCEDURE IF EXISTS `sp_buscar_participaciones`$$
CREATE PROCEDURE `sp_buscar_participaciones`(
    IN p_q VARCHAR(255),
    IN p_programa VARCHAR(255),
    IN p_estado VARCHAR(100),
    IN p_limit INT,
    IN p_offset INT,
    OUT p_total INT
)
BEGIN
    SELECT COUNT(*) INTO p_total
    FROM participaciones p
    JOIN beneficiarios b ON p.beneficiario_id = b.id
    WHERE (p_q IS NULL OR p_q = '' OR 
           b.num_doc LIKE CONCAT('%', p_q, '%') OR 
           b.nombres LIKE CONCAT('%', p_q, '%') OR 
           b.apellidos LIKE CONCAT('%', p_q, '%') OR 
           b.codigo_interno LIKE CONCAT('%', p_q, '%') OR 
           p.programa_nombre LIKE CONCAT('%', p_q, '%') OR 
           p.linea_trabajo LIKE CONCAT('%', p_q, '%'))
      AND (p_programa IS NULL OR p_programa = '' OR p.programa_nombre = p_programa)
      AND (p_estado IS NULL OR p_estado = '' OR p.estado = p_estado);

    SELECT p.*, 
           CONCAT(b.nombres, ' ', IFNULL(b.apellidos, '')) AS beneficiario_nombre, 
           b.codigo_interno
    FROM participaciones p
    JOIN beneficiarios b ON p.beneficiario_id = b.id
    WHERE (p_q IS NULL OR p_q = '' OR 
           b.num_doc LIKE CONCAT('%', p_q, '%') OR 
           b.nombres LIKE CONCAT('%', p_q, '%') OR 
           b.apellidos LIKE CONCAT('%', p_q, '%') OR 
           b.codigo_interno LIKE CONCAT('%', p_q, '%') OR 
           p.programa_nombre LIKE CONCAT('%', p_q, '%') OR 
           p.linea_trabajo LIKE CONCAT('%', p_q, '%'))
      AND (p_programa IS NULL OR p_programa = '' OR p.programa_nombre = p_programa)
      AND (p_estado IS NULL OR p_estado = '' OR p.estado = p_estado)
    ORDER BY p.id DESC
    LIMIT p_limit OFFSET p_offset;
END$$

-- ============================================================================
-- 9. BUSCADOR Y FILTROS: sp_buscar_auditoria
-- PROPÓSITO   : Búsqueda y filtrado en bitácora de auditoría forense (ISO 27001)
-- ============================================================================
DROP PROCEDURE IF EXISTS `sp_buscar_auditoria`$$
CREATE PROCEDURE `sp_buscar_auditoria`(
    IN p_q VARCHAR(255),
    IN p_nivel VARCHAR(50),
    IN p_accion VARCHAR(100),
    IN p_limit INT,
    IN p_offset INT,
    OUT p_total INT
)
BEGIN
    SELECT COUNT(*) INTO p_total
    FROM auditoria
    WHERE (p_q IS NULL OR p_q = '' OR 
           usuario LIKE CONCAT('%', p_q, '%') OR 
           detalle LIKE CONCAT('%', p_q, '%') OR 
           ip_origen LIKE CONCAT('%', p_q, '%') OR 
           accion LIKE CONCAT('%', p_q, '%'))
      AND (p_nivel IS NULL OR p_nivel = '' OR nivel = p_nivel)
      AND (p_accion IS NULL OR p_accion = '' OR accion = p_accion);

    SELECT *
    FROM auditoria
    WHERE (p_q IS NULL OR p_q = '' OR 
           usuario LIKE CONCAT('%', p_q, '%') OR 
           detalle LIKE CONCAT('%', p_q, '%') OR 
           ip_origen LIKE CONCAT('%', p_q, '%') OR 
           accion LIKE CONCAT('%', p_q, '%'))
      AND (p_nivel IS NULL OR p_nivel = '' OR nivel = p_nivel)
      AND (p_accion IS NULL OR p_accion = '' OR accion = p_accion)
    ORDER BY id DESC
    LIMIT p_limit OFFSET p_offset;
END$$

-- ============================================================================
-- 10. BÚSQUEDA GLOBAL: sp_busqueda_global_spotlight
-- PROPÓSITO   : Búsqueda instantánea Spotlight para barra superior de navegación
-- ============================================================================
DROP PROCEDURE IF EXISTS `sp_busqueda_global_spotlight`$$
CREATE PROCEDURE `sp_busqueda_global_spotlight`(
    IN p_q VARCHAR(255),
    IN p_limit INT
)
BEGIN
    SELECT 
        id, 
        codigo_interno, 
        num_doc, 
        tipo_doc, 
        CONCAT(nombres, ' ', IFNULL(apellidos, '')) AS nombre, 
        municipio
    FROM beneficiarios
    WHERE (p_q IS NOT NULL AND p_q != '' AND (
           nombres LIKE CONCAT('%', p_q, '%') OR 
           apellidos LIKE CONCAT('%', p_q, '%') OR 
           num_doc LIKE CONCAT('%', p_q, '%') OR 
           codigo_interno LIKE CONCAT('%', p_q, '%') OR
           municipio LIKE CONCAT('%', p_q, '%')))
    ORDER BY id DESC
    LIMIT p_limit;
END$$

DELIMITER ;
