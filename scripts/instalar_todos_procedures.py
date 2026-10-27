import sys
sys.path.insert(0, '.')
from app import get_db_connection

def instalar_suite_completa():
    print("Iniciando compilación e instalación de la SUITE COMPLETA de Stored Procedures...")
    conn = get_db_connection()
    cur = conn.cursor()

    procs = [
        # --- 1. sp_validar_documento_beneficiario ---
        {
            "name": "sp_validar_documento_beneficiario",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_validar_documento_beneficiario;",
            "sql_create": """
            CREATE PROCEDURE sp_validar_documento_beneficiario(
                IN p_num_doc VARCHAR(100)
            )
            BEGIN
                SELECT * 
                FROM beneficiarios 
                WHERE TRIM(num_doc) = TRIM(p_num_doc) 
                   OR REPLACE(num_doc, ' ', '') = REPLACE(p_num_doc, ' ', '')
                LIMIT 1;
            END
            """
        },

        # --- 2. sp_obtener_beneficiario_por_id ---
        {
            "name": "sp_obtener_beneficiario_por_id",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_obtener_beneficiario_por_id;",
            "sql_create": """
            CREATE PROCEDURE sp_obtener_beneficiario_por_id(
                IN p_id INT
            )
            BEGIN
                SELECT * 
                FROM beneficiarios 
                WHERE id = p_id;
            END
            """
        },

        # --- 3. sp_obtener_relaciones_beneficiario ---
        {
            "name": "sp_obtener_relaciones_beneficiario",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_obtener_relaciones_beneficiario;",
            "sql_create": """
            CREATE PROCEDURE sp_obtener_relaciones_beneficiario(
                IN p_id INT
            )
            BEGIN
                -- Retorna 4 select sets en MySQL: nucleo_familiar, participaciones, atenciones, seguimientos
                SELECT * FROM nucleo_familiar WHERE beneficiario_id = p_id ORDER BY id DESC;
            END
            """
        },

        # --- 4. sp_obtener_participaciones_beneficiario ---
        {
            "name": "sp_obtener_participaciones_beneficiario",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_obtener_participaciones_beneficiario;",
            "sql_create": """
            CREATE PROCEDURE sp_obtener_participaciones_beneficiario(
                IN p_id INT
            )
            BEGIN
                SELECT * FROM participaciones WHERE beneficiario_id = p_id ORDER BY id DESC;
            END
            """
        },

        # --- 5. sp_obtener_atenciones_beneficiario ---
        {
            "name": "sp_obtener_atenciones_beneficiario",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_obtener_atenciones_beneficiario;",
            "sql_create": """
            CREATE PROCEDURE sp_obtener_atenciones_beneficiario(
                IN p_id INT
            )
            BEGIN
                SELECT * FROM atenciones WHERE beneficiario_id = p_id ORDER BY id DESC;
            END
            """
        },

        # --- 6. sp_obtener_seguimientos_beneficiario ---
        {
            "name": "sp_obtener_seguimientos_beneficiario",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_obtener_seguimientos_beneficiario;",
            "sql_create": """
            CREATE PROCEDURE sp_obtener_seguimientos_beneficiario(
                IN p_id INT
            )
            BEGIN
                SELECT * FROM seguimientos WHERE beneficiario_id = p_id ORDER BY id DESC;
            END
            """
        },

        # --- 7. sp_crear_beneficiario ---
        {
            "name": "sp_crear_beneficiario",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_crear_beneficiario;",
            "sql_create": """
            CREATE PROCEDURE sp_crear_beneficiario(
                IN p_codigo VARCHAR(100),
                IN p_tipo_doc VARCHAR(100),
                IN p_num_doc VARCHAR(100),
                IN p_nombres VARCHAR(255),
                IN p_apellidos VARCHAR(255),
                IN p_fecha_nac VARCHAR(100),
                IN p_sexo VARCHAR(50),
                IN p_telefono VARCHAR(100),
                IN p_municipio VARCHAR(255),
                IN p_condicion VARCHAR(255),
                IN p_discapacidad VARCHAR(255),
                IN p_habeas INT,
                OUT p_nuevo_id INT
            )
            BEGIN
                INSERT INTO beneficiarios (
                    codigo_interno, tipo_doc, num_doc, nombres, apellidos,
                    fecha_nacimiento, sexo, telefono, municipio,
                    condicion_poblacional, discapacidad, habeas_data, fecha_registro
                ) VALUES (
                    p_codigo, p_tipo_doc, p_num_doc, p_nombres, p_apellidos,
                    p_fecha_nac, p_sexo, p_telefono, p_municipio,
                    p_condicion, p_discapacidad, p_habeas, NOW()
                );
                SET p_nuevo_id = LAST_INSERT_ID();
            END
            """
        },

        # --- 8. sp_actualizar_beneficiario ---
        {
            "name": "sp_actualizar_beneficiario",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_actualizar_beneficiario;",
            "sql_create": """
            CREATE PROCEDURE sp_actualizar_beneficiario(
                IN p_id INT,
                IN p_tipo_doc VARCHAR(100),
                IN p_num_doc VARCHAR(100),
                IN p_nombres VARCHAR(255),
                IN p_apellidos VARCHAR(255),
                IN p_fecha_nac VARCHAR(100),
                IN p_sexo VARCHAR(50),
                IN p_telefono VARCHAR(100),
                IN p_municipio VARCHAR(255),
                IN p_condicion VARCHAR(255),
                IN p_discapacidad VARCHAR(255),
                IN p_habeas INT
            )
            BEGIN
                UPDATE beneficiarios SET 
                    tipo_doc = p_tipo_doc, 
                    num_doc = p_num_doc, 
                    nombres = p_nombres, 
                    apellidos = p_apellidos, 
                    fecha_nacimiento = p_fecha_nac, 
                    sexo = p_sexo, 
                    telefono = p_telefono, 
                    municipio = p_municipio, 
                    condicion_poblacional = p_condicion, 
                    discapacidad = p_discapacidad, 
                    habeas_data = p_habeas
                WHERE id = p_id;
            END
            """
        },

        # --- 9. sp_eliminar_beneficiario ---
        {
            "name": "sp_eliminar_beneficiario",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_eliminar_beneficiario;",
            "sql_create": """
            CREATE PROCEDURE sp_eliminar_beneficiario(
                IN p_id INT
            )
            BEGIN
                -- Eliminación relacional en cascada segura
                DELETE FROM nucleo_familiar WHERE beneficiario_id = p_id;
                DELETE FROM atenciones WHERE beneficiario_id = p_id;
                DELETE FROM seguimientos WHERE beneficiario_id = p_id;
                DELETE FROM participaciones WHERE beneficiario_id = p_id;
                DELETE FROM beneficiarios WHERE id = p_id;
            END
            """
        },

        # --- 10. sp_obtener_lista_simple_beneficiarios ---
        {
            "name": "sp_obtener_lista_simple_beneficiarios",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_obtener_lista_simple_beneficiarios;",
            "sql_create": """
            CREATE PROCEDURE sp_obtener_lista_simple_beneficiarios()
            BEGIN
                SELECT id, codigo_interno, num_doc, nombres, apellidos 
                FROM beneficiarios 
                ORDER BY nombres ASC;
            END
            """
        },

        # --- 11. sp_obtener_catalogos_filtros_beneficiarios ---
        {
            "name": "sp_obtener_catalogos_filtros_beneficiarios",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_obtener_catalogos_filtros_beneficiarios;",
            "sql_create": """
            CREATE PROCEDURE sp_obtener_catalogos_filtros_beneficiarios()
            BEGIN
                SELECT DISTINCT municipio 
                FROM beneficiarios 
                WHERE municipio IS NOT NULL AND municipio != '' 
                ORDER BY municipio;
            END
            """
        },

        # --- 12. sp_obtener_usuario_por_correo ---
        {
            "name": "sp_obtener_usuario_por_correo",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_obtener_usuario_por_correo;",
            "sql_create": """
            CREATE PROCEDURE sp_obtener_usuario_por_correo(
                IN p_correo VARCHAR(255)
            )
            BEGIN
                SELECT * 
                FROM usuarios 
                WHERE LOWER(correo) = LOWER(p_correo) 
                LIMIT 1;
            END
            """
        },

        # --- 13. sp_obtener_usuario_por_id ---
        {
            "name": "sp_obtener_usuario_por_id",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_obtener_usuario_por_id;",
            "sql_create": """
            CREATE PROCEDURE sp_obtener_usuario_por_id(
                IN p_id INT
            )
            BEGIN
                SELECT id, nombre, correo, password, rol 
                FROM usuarios 
                WHERE id = p_id 
                LIMIT 1;
            END
            """
        },

        # --- 14. sp_actualizar_password_usuario ---
        {
            "name": "sp_actualizar_password_usuario",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_actualizar_password_usuario;",
            "sql_create": """
            CREATE PROCEDURE sp_actualizar_password_usuario(
                IN p_id INT,
                IN p_password VARCHAR(255)
            )
            BEGIN
                UPDATE usuarios 
                SET password = p_password 
                WHERE id = p_id;
            END
            """
        },

        # --- 15. sp_listar_usuarios ---
        {
            "name": "sp_listar_usuarios",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_listar_usuarios;",
            "sql_create": """
            CREATE PROCEDURE sp_listar_usuarios(
                IN p_limit INT,
                IN p_offset INT,
                OUT p_total INT
            )
            BEGIN
                SELECT COUNT(*) INTO p_total FROM usuarios;

                SELECT id, nombre, correo, rol 
                FROM usuarios 
                ORDER BY id ASC
                LIMIT p_limit OFFSET p_offset;
            END
            """
        },

        # --- 16. sp_crear_usuario ---
        {
            "name": "sp_crear_usuario",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_crear_usuario;",
            "sql_create": """
            CREATE PROCEDURE sp_crear_usuario(
                IN p_nombre VARCHAR(150),
                IN p_correo VARCHAR(255),
                IN p_password VARCHAR(255),
                IN p_rol VARCHAR(50),
                OUT p_nuevo_id INT
            )
            BEGIN
                INSERT INTO usuarios (nombre, correo, password, rol) 
                VALUES (p_nombre, p_correo, p_password, p_rol);
                SET p_nuevo_id = LAST_INSERT_ID();
            END
            """
        },

        # --- 17. sp_eliminar_usuario ---
        {
            "name": "sp_eliminar_usuario",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_eliminar_usuario;",
            "sql_create": """
            CREATE PROCEDURE sp_eliminar_usuario(
                IN p_id INT
            )
            BEGIN
                DELETE FROM usuarios WHERE id = p_id;
            END
            """
        },

        # --- 18. sp_cambiar_rol_usuario ---
        {
            "name": "sp_cambiar_rol_usuario",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_cambiar_rol_usuario;",
            "sql_create": """
            CREATE PROCEDURE sp_cambiar_rol_usuario(
                IN p_id INT,
                IN p_rol VARCHAR(50)
            )
            BEGIN
                UPDATE usuarios SET rol = p_rol WHERE id = p_id;
            END
            """
        },

        # --- 19. sp_crear_familiar ---
        {
            "name": "sp_crear_familiar",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_crear_familiar;",
            "sql_create": """
            CREATE PROCEDURE sp_crear_familiar(
                IN p_beneficiario_id INT,
                IN p_nombre VARCHAR(255),
                IN p_parentesco VARCHAR(100),
                IN p_edad INT
            )
            BEGIN
                INSERT INTO nucleo_familiar (beneficiario_id, nombre_completo, parentesco, edad) 
                VALUES (p_beneficiario_id, p_nombre, p_parentesco, p_edad);
            END
            """
        },

        # --- 20. sp_eliminar_familiar ---
        {
            "name": "sp_eliminar_familiar",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_eliminar_familiar;",
            "sql_create": """
            CREATE PROCEDURE sp_eliminar_familiar(
                IN p_id INT,
                OUT p_beneficiario_id INT
            )
            BEGIN
                SELECT beneficiario_id INTO p_beneficiario_id FROM nucleo_familiar WHERE id = p_id;
                DELETE FROM nucleo_familiar WHERE id = p_id;
            END
            """
        },

        # --- 21. sp_crear_participacion ---
        {
            "name": "sp_crear_participacion",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_crear_participacion;",
            "sql_create": """
            CREATE PROCEDURE sp_crear_participacion(
                IN p_beneficiario_id INT,
                IN p_programa VARCHAR(255),
                IN p_linea VARCHAR(255),
                IN p_fecha VARCHAR(100),
                IN p_estado VARCHAR(100)
            )
            BEGIN
                INSERT INTO participaciones (beneficiario_id, programa_nombre, linea_trabajo, fecha_vinculacion, estado) 
                VALUES (p_beneficiario_id, p_programa, p_linea, p_fecha, p_estado);
            END
            """
        },

        # --- 22. sp_eliminar_participacion ---
        {
            "name": "sp_eliminar_participacion",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_eliminar_participacion;",
            "sql_create": """
            CREATE PROCEDURE sp_eliminar_participacion(
                IN p_id INT
            )
            BEGIN
                DELETE FROM participaciones WHERE id = p_id;
            END
            """
        },

        # --- 23. sp_crear_seguimiento ---
        {
            "name": "sp_crear_seguimiento",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_crear_seguimiento;",
            "sql_create": """
            CREATE PROCEDURE sp_crear_seguimiento(
                IN p_beneficiario_id INT,
                IN p_fecha VARCHAR(100),
                IN p_avance TEXT,
                IN p_proxima TEXT,
                IN p_fecha_prox VARCHAR(100),
                IN p_estado VARCHAR(100)
            )
            BEGIN
                INSERT INTO seguimientos (beneficiario_id, fecha, avance, proxima_accion, fecha_proximo_contacto, estado_accion) 
                VALUES (p_beneficiario_id, p_fecha, p_avance, p_proxima, p_fecha_prox, p_estado);
            END
            """
        },

        # --- 24. sp_actualizar_estado_seguimiento ---
        {
            "name": "sp_actualizar_estado_seguimiento",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_actualizar_estado_seguimiento;",
            "sql_create": """
            CREATE PROCEDURE sp_actualizar_estado_seguimiento(
                IN p_id INT,
                IN p_estado VARCHAR(100)
            )
            BEGIN
                UPDATE seguimientos SET estado_accion = p_estado WHERE id = p_id;
            END
            """
        },

        # --- 25. sp_eliminar_seguimiento ---
        {
            "name": "sp_eliminar_seguimiento",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_eliminar_seguimiento;",
            "sql_create": """
            CREATE PROCEDURE sp_eliminar_seguimiento(
                IN p_id INT
            )
            BEGIN
                DELETE FROM seguimientos WHERE id = p_id;
            END
            """
        },

        # --- 26. sp_eliminar_atencion ---
        {
            "name": "sp_eliminar_atencion",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_eliminar_atencion;",
            "sql_create": """
            CREATE PROCEDURE sp_eliminar_atencion(
                IN p_id INT
            )
            BEGIN
                DELETE FROM atenciones WHERE id = p_id;
            END
            """
        },

        # --- 27. sp_insertar_auditoria ---
        {
            "name": "sp_insertar_auditoria",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_insertar_auditoria;",
            "sql_create": """
            CREATE PROCEDURE sp_insertar_auditoria(
                IN p_usuario VARCHAR(100),
                IN p_accion VARCHAR(100),
                IN p_detalle TEXT,
                IN p_nivel VARCHAR(20),
                IN p_ip VARCHAR(45)
            )
            BEGIN
                INSERT INTO auditoria (usuario, accion, detalle, nivel, ip_origen, fecha_hora)
                VALUES (p_usuario, p_accion, p_detalle, p_nivel, p_ip, NOW());
            END
            """
        },

        # --- 28. sp_catalogos_seguimientos ---
        {
            "name": "sp_catalogos_seguimientos",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_catalogos_seguimientos;",
            "sql_create": """
            CREATE PROCEDURE sp_catalogos_seguimientos()
            BEGIN
                SELECT DISTINCT estado_accion 
                FROM seguimientos 
                WHERE estado_accion IS NOT NULL AND estado_accion != '' 
                ORDER BY estado_accion;
            END
            """
        },

        # --- 29. sp_catalogos_atenciones ---
        {
            "name": "sp_catalogos_atenciones",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_catalogos_atenciones;",
            "sql_create": """
            CREATE PROCEDURE sp_catalogos_atenciones()
            BEGIN
                SELECT DISTINCT tipo 
                FROM atenciones 
                WHERE tipo IS NOT NULL AND tipo != '' 
                ORDER BY tipo;
            END
            """
        },

        # --- 30. sp_catalogos_programas ---
        {
            "name": "sp_catalogos_programas",
            "sql_drop": "DROP PROCEDURE IF EXISTS sp_catalogos_programas;",
            "sql_create": """
            CREATE PROCEDURE sp_catalogos_programas()
            BEGIN
                SELECT DISTINCT programa_nombre 
                FROM participaciones 
                WHERE programa_nombre IS NOT NULL AND programa_nombre != '' 
                ORDER BY programa_nombre;
            END
            """
        }
    ]

    for p in procs:
        cur.execute(p["sql_drop"])
        cur.execute(p["sql_create"])
        print(f" -> Compilado en MySQL: {p['name']}")

    conn.close()
    print("¡Suite completa de Stored Procedures instalada con éxito en uraba_pais_db!")

if __name__ == '__main__':
    instalar_suite_completa()
