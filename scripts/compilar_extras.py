import sys
sys.path.insert(0, '.')
from app import get_db_connection

def compilar_procs_adicionales():
    print("Compilando procedimientos adicionales para cobertura 100% CALL...")
    conn = get_db_connection()
    cur = conn.cursor()

    extras = [
        # --- sp_verificar_certificado_qr ---
        {
            "name": "sp_verificar_certificado_qr",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_verificar_certificado_qr;",
            "sql_create": """
            CREATE PROCEDURE sp_verificar_certificado_qr(
                IN p_codigo VARCHAR(100)
            )
            BEGIN
                SELECT * FROM beneficiarios 
                WHERE UPPER(codigo_interno) = UPPER(p_codigo) 
                   OR UPPER(num_doc) = UPPER(p_codigo) 
                LIMIT 1;
            END
            """
        },

        # --- sp_notificaciones_usuario ---
        {
            "name": "sp_notificaciones_usuario",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_notificaciones_usuario;",
            "sql_create": """
            CREATE PROCEDURE sp_notificaciones_usuario()
            BEGIN
                SELECT 
                    (SELECT COUNT(*) FROM seguimientos WHERE estado_accion = 'Pendiente') AS segs_pend,
                    (SELECT COUNT(*) FROM beneficiarios WHERE id NOT IN (SELECT DISTINCT beneficiario_id FROM participaciones)) AS sin_prog;
            END
            """
        },

        # --- sp_obtener_alertas_sistema ---
        {
            "name": "sp_obtener_alertas_sistema",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_obtener_alertas_sistema;",
            "sql_create": """
            CREATE PROCEDURE sp_obtener_alertas_sistema()
            BEGIN
                SELECT id, codigo_interno, num_doc, nombres, apellidos, municipio, condicion_poblacional, discapacidad, fecha_nacimiento, telefono 
                FROM beneficiarios;
            END
            """
        },

        # --- sp_metricas_participaciones_agrupadas ---
        {
            "name": "sp_metricas_participaciones_agrupadas",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_metricas_participaciones_agrupadas;",
            "sql_create": """
            CREATE PROCEDURE sp_metricas_participaciones_agrupadas()
            BEGIN
                SELECT beneficiario_id, COUNT(*) as c FROM participaciones GROUP BY beneficiario_id;
            END
            """
        },

        # --- sp_ultimas_atenciones_agrupadas ---
        {
            "name": "sp_ultimas_atenciones_agrupadas",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_ultimas_atenciones_agrupadas;",
            "sql_create": """
            CREATE PROCEDURE sp_ultimas_atenciones_agrupadas()
            BEGIN
                SELECT beneficiario_id, MAX(fecha) as ult FROM atenciones GROUP BY beneficiario_id;
            END
            """
        },

        # --- sp_exportar_beneficiarios_csv ---
        {
            "name": "sp_exportar_beneficiarios_csv",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_exportar_beneficiarios_csv;",
            "sql_create": """
            CREATE PROCEDURE sp_exportar_beneficiarios_csv()
            BEGIN
                SELECT * FROM beneficiarios ORDER BY id ASC;
            END
            """
        },

        # --- sp_obtener_indicadores_dashboard ---
        {
            "name": "sp_obtener_indicadores_dashboard",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_obtener_indicadores_dashboard;",
            "sql_create": """
            CREATE PROCEDURE sp_obtener_indicadores_dashboard()
            BEGIN
                SELECT 
                    (SELECT COUNT(*) FROM beneficiarios) AS total_beneficiarios,
                    (SELECT COUNT(*) FROM participaciones) AS total_participaciones,
                    (SELECT COUNT(*) FROM atenciones) AS total_atenciones,
                    (SELECT COUNT(*) FROM seguimientos WHERE estado_accion = 'Pendiente') AS seguimientos_pendientes;
            END
            """
        },

        # --- sp_metricas_auditoria_resumen ---
        {
            "name": "sp_metricas_auditoria_resumen",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_metricas_auditoria_resumen;",
            "sql_create": """
            CREATE PROCEDURE sp_metricas_auditoria_resumen()
            BEGIN
                SELECT 
                    (SELECT COUNT(*) FROM auditoria) AS total_eventos,
                    (SELECT COUNT(*) FROM auditoria WHERE nivel = 'SEGURIDAD' OR nivel = 'ALERTA' OR nivel = 'CRITICO') AS total_seguridad,
                    (SELECT COUNT(DISTINCT ip_origen) FROM auditoria) AS total_ips;
            END
            """
        },

        # --- sp_validar_existencia_importacion ---
        {
            "name": "sp_validar_existencia_importacion",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_validar_existencia_importacion;",
            "sql_create": """
            CREATE PROCEDURE sp_validar_existencia_importacion()
            BEGIN
                SELECT num_doc FROM beneficiarios WHERE num_doc IS NOT NULL AND num_doc != '';
            END
            """
        },

        # --- sp_codigos_existentes_importacion ---
        {
            "name": "sp_codigos_existentes_importacion",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_codigos_existentes_importacion;",
            "sql_create": """
            CREATE PROCEDURE sp_codigos_existentes_importacion()
            BEGIN
                SELECT codigo_interno FROM beneficiarios WHERE codigo_interno IS NOT NULL;
            END
            """
        }
    ]

    for p in extras:
        cur.execute(p["sql_drop"])
        cur.execute(p["sql_create"])
        print(f" -> Compilado: {p['name']}")

    conn.close()
    print("¡Procedimientos adicionales compilados exitosamente!")

if __name__ == '__main__':
    compilar_procs_adicionales()
