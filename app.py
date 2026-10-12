import os
import unicodedata
import random
from functools import wraps
from dotenv import load_dotenv 
import pymysql
import pymysql.cursors
from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash


load_dotenv()

app = Flask(__name__)


app.secret_key = os.getenv('SECRET_KEY', 'clave_fallback_segura')


DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_NAME = os.getenv('DB_NAME', 'uraba_pais_db')

def get_db_connection():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            flash('Debes iniciar sesión para acceder al sistema.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            flash('Debes iniciar sesión para acceder al sistema.', 'warning')
            return redirect(url_for('login'))
        if session.get('rol') != 'administrador':
            flash('Esta acción está reservada para el administrador.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_config_visual():
    rol = session.get('rol', 'funcionario')
    return {
        'tema_actual': session.get('tema', 'claro'),
        'fuente_actual': session.get('fuente', 'Roboto'),
        'tamanio_letra_actual': session.get('tamanio_letra', '16px'),
        'usuario_actual': session.get('usuario', ''),
        'rol_actual': rol,
        'es_admin': rol == 'administrador'
    }

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255),
            correo VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            rol VARCHAR(50) DEFAULT 'funcionario'
        )
    ''')

    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN rol VARCHAR(50) DEFAULT 'funcionario'")
    except Exception:
        pass

    cursor.execute("SELECT COUNT(*) as total FROM usuarios")
    if cursor.fetchone()['total'] == 0:
        cursor.execute('''
            INSERT INTO usuarios (nombre, correo, password, rol)
            VALUES (%s, %s, %s, %s)
        ''', ('Administrador', 'admin@uraba.gov.co', generate_password_hash('1234'), 'administrador'))

    cursor.execute("SELECT id FROM usuarios WHERE LOWER(correo) = %s", ('funcionario@uraba.gov.co',))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO usuarios (nombre, correo, password, rol)
            VALUES (%s, %s, %s, %s)
        ''', ('Funcionario', 'funcionario@uraba.gov.co', generate_password_hash('1234'), 'funcionario'))

    cursor.execute("UPDATE usuarios SET rol = 'administrador' WHERE LOWER(correo) = 'admin@uraba.gov.co'")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS beneficiarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            codigo_interno VARCHAR(100),
            tipo_doc VARCHAR(100),
            num_doc VARCHAR(100) UNIQUE,
            nombres VARCHAR(255),
            apellidos VARCHAR(255),
            fecha_nacimiento VARCHAR(100),
            sexo VARCHAR(50),
            telefono VARCHAR(100),
            municipio VARCHAR(255),
            condicion_poblacional VARCHAR(255),
            discapacidad VARCHAR(255),
            habeas_data INT DEFAULT 1,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nucleo_familiar (
            id INT AUTO_INCREMENT PRIMARY KEY,
            beneficiario_id INT,
            nombre_completo VARCHAR(255),
            parentesco VARCHAR(100),
            edad INT,
            FOREIGN KEY (beneficiario_id) REFERENCES beneficiarios (id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participaciones (
            id INT AUTO_INCREMENT PRIMARY KEY,
            beneficiario_id INT,
            programa_nombre VARCHAR(255),
            linea_trabajo VARCHAR(255),
            fecha_vinculacion VARCHAR(100),
            estado VARCHAR(100) DEFAULT 'inscrito',
            FOREIGN KEY (beneficiario_id) REFERENCES beneficiarios (id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS atenciones (
            id INT AUTO_INCREMENT PRIMARY KEY,
            beneficiario_id INT,
            tipo VARCHAR(255),
            fecha VARCHAR(100),
            descripcion TEXT,
            responsable VARCHAR(255),
            remision VARCHAR(255),
            FOREIGN KEY (beneficiario_id) REFERENCES beneficiarios (id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seguimientos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            beneficiario_id INT,
            fecha VARCHAR(100),
            avance TEXT,
            proxima_accion TEXT,
            fecha_proximo_contacto VARCHAR(100),
            estado_accion VARCHAR(100) DEFAULT 'Pendiente',
            FOREIGN KEY (beneficiario_id) REFERENCES beneficiarios (id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tblcondicionp (
            idcondicion INT AUTO_INCREMENT PRIMARY KEY,
            condicion ENUM('Migrante','Refugiado/a o solicitante de asilo','Retornado/a','Desplazado/a','Población local') NOT NULL
        )
    ''')
    cursor.execute('SELECT COUNT(*) as total FROM tblcondicionp')
    if cursor.fetchone()['total'] == 0:
        cursor.execute('''
            INSERT INTO tblcondicionp (condicion) VALUES
            ('Migrante'),
            ('Refugiado/a o solicitante de asilo'),
            ('Retornado/a'),
            ('Desplazado/a'),
            ('Población local')
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tbldiscapacidad (
            iddiscapacidad INT AUTO_INCREMENT PRIMARY KEY,
            discapacidad ENUM('Ninguna','Física','Visual','Auditiva','Intelectual','Psicosocial','Múltiple','Sordoceguera') NOT NULL
        )
    ''')
    cursor.execute('SELECT COUNT(*) as total FROM tbldiscapacidad')
    if cursor.fetchone()['total'] == 0:
        cursor.execute('''
            INSERT INTO tbldiscapacidad (discapacidad) VALUES
            ('Ninguna'),
            ('Física'),
            ('Visual'),
            ('Auditiva'),
            ('Intelectual'),
            ('Psicosocial'),
            ('Múltiple'),
            ('Sordoceguera')
        ''')

    conn.close()

def obtener_indicadores():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM beneficiarios')
    total_beneficiarios = cursor.fetchone()['total']
    cursor.execute('SELECT COUNT(*) as total FROM participaciones')
    total_participaciones = cursor.fetchone()['total']
    cursor.execute('SELECT COUNT(*) as total FROM atenciones')
    total_atenciones = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM seguimientos WHERE estado_accion = 'Pendiente'")
    seguimientos_pendientes = cursor.fetchone()['total']
    cursor.execute('''
        SELECT programa_nombre, COUNT(*) as cantidad
        FROM participaciones
        GROUP BY programa_nombre
        ORDER BY cantidad DESC
    ''')
    programas_resumen = cursor.fetchall()
    cursor.execute('''
        SELECT estado, COUNT(*) as cantidad
        FROM participaciones
        GROUP BY estado
        ORDER BY cantidad DESC
    ''')
    estados_resumen = cursor.fetchall()
    cursor.execute('''
        SELECT municipio, COUNT(*) as cantidad
        FROM beneficiarios
        WHERE municipio IS NOT NULL AND municipio != ''
        GROUP BY municipio
        ORDER BY cantidad DESC
    ''')
    municipios_resumen = cursor.fetchall()
    conn.close()
    return {
        'total_beneficiarios': total_beneficiarios,
        'total_participaciones': total_participaciones,
        'total_atenciones': total_atenciones,
        'seguimientos_pendientes': seguimientos_pendientes,
        'programas_resumen': programas_resumen,
        'estados_resumen': estados_resumen,
        'municipios_resumen': municipios_resumen
    }

def obtener_catalogos():
    condiciones_base = [
        {'condicion': 'Migrante'},
        {'condicion': 'Refugiado/a o solicitante de asilo'},
        {'condicion': 'Retornado/a'},
        {'condicion': 'Desplazado/a'},
        {'condicion': 'Población local'},
    ]
    discapacidades_base = [
        {'discapacidad': 'Ninguna'},
        {'discapacidad': 'Física'},
        {'discapacidad': 'Visual'},
        {'discapacidad': 'Auditiva'},
        {'discapacidad': 'Intelectual'},
        {'discapacidad': 'Psicosocial'},
        {'discapacidad': 'Múltiple'},
        {'discapacidad': 'Sordoceguera'},
    ]
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT condicion FROM tblcondicionp ORDER BY idcondicion')
        condiciones = cursor.fetchall()
        cursor.execute('SELECT discapacidad FROM tbldiscapacidad ORDER BY iddiscapacidad')
        discapacidades = cursor.fetchall()
        conn.close()
        if not condiciones:
            condiciones = condiciones_base
        if not discapacidades:
            discapacidades = discapacidades_base
        return condiciones, discapacidades
    except Exception:
        return condiciones_base, discapacidades_base

init_db()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip().lower()
        password = request.form.get('password', '')
        if not correo or not password:
            flash('Por favor ingrese su correo y contraseña.', 'warning')
            return redirect(url_for('login'))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE LOWER(correo) = %s", (correo,))
        usuario = cursor.fetchone()
        conn.close()
        if usuario:
            db_pass = usuario['password']
            es_valido = False
            if db_pass.startswith('pbkdf2:') or db_pass.startswith('scrypt:'):
                es_valido = check_password_hash(db_pass, password)
            else:
                es_valido = (db_pass == password)
            if es_valido:
                session['usuario'] = usuario['nombre'] if usuario['nombre'] else usuario['correo']
                session['usuario_id'] = usuario['id']
                session['correo'] = usuario['correo']
                session['rol'] = usuario.get('rol') or 'funcionario'
                flash(f"¡Bienvenido, {session['usuario']} ({session['rol']})!", 'success')
                return redirect(url_for('dashboard'))
        flash('Correo o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('login'))

@app.route('/configuracion')
@login_required
@admin_required
def configuracion():
    return render_template('configuracion.html', usuario_actual=session.get('usuario'))

@app.route('/configuracion/guardar_apariencia', methods=['POST'])
@login_required
@admin_required
def guardar_apariencia():
    session['tema'] = request.form.get('tema', 'claro')
    session['fuente'] = request.form.get('fuente', 'Inter')
    session['estilo_visual'] = request.form.get('estilo_visual', 'glassy')
    flash('¡Preferencias visuales y estilo de diseño actualizados correctamente!', 'success')
    return redirect(url_for('configuracion'))

@app.route('/configuracion/cambiar_password', methods=['POST'])
@login_required
@admin_required
def cambiar_password():
    nueva_password = request.form.get('password_nueva') or request.form.get('nueva_password', '')
    confirmar_password = request.form.get('password_confirmar') or request.form.get('confirmar_password', '')
    if nueva_password != confirmar_password:
        flash('Las nuevas contraseñas no coinciden.', 'danger')
        return redirect(url_for('configuracion'))
    if len(nueva_password) < 4:
        flash('La contraseña debe tener al menos 4 caracteres.', 'warning')
        return redirect(url_for('configuracion'))
    usuario_id = session.get('usuario_id')
    correo = session.get('correo', 'admin@uraba.gov.co')
    conn = get_db_connection()
    cursor = conn.cursor()
    password_encriptada = generate_password_hash(nueva_password)
    if usuario_id:
        cursor.execute("UPDATE usuarios SET password = %s WHERE id = %s", (password_encriptada, usuario_id))
    else:
        cursor.execute("UPDATE usuarios SET password = %s WHERE LOWER(correo) = LOWER(%s)", (password_encriptada, correo))
    conn.close()
    flash('¡Contraseña actualizada correctamente!', 'success')
    return redirect(url_for('configuracion'))

@app.route('/configuracion/respaldo_db')
@login_required
@admin_required
def respaldo_db():
    flash('Las copias de seguridad de MySQL se gestionan a través de herramientas de administración como phpMyAdmin, MySQL Workbench o mysqldump.', 'info')
    return redirect(url_for('configuracion'))

@app.route('/')
@app.route('/inicio')
@app.route('/home')
def index():
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    indicadores = obtener_indicadores()
    total_programas = len(indicadores.get('programas_resumen', []))
    return render_template(
        'landing.html',
        total_beneficiarios=indicadores.get('total_beneficiarios', 0),
        total_atenciones=indicadores.get('total_atenciones', 0),
        total_programas=total_programas
    )

@app.route('/dashboard')
@login_required
def dashboard():
    indicadores = obtener_indicadores()
    return render_template('dashboard.html', **indicadores)

@app.route('/beneficiarios', methods=['GET'], endpoint='beneficiarios')
@app.route('/beneficiarios-lista', methods=['GET'], endpoint='listar_beneficiarios')
@login_required
def listar_beneficiarios():
    q = request.args.get('q', '').strip()
    municipio_filtro = request.args.get('municipio', '').strip()
    pagina = int(request.args.get('pagina', 1))
    por_pagina = 15
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT municipio FROM beneficiarios WHERE municipio IS NOT NULL AND municipio != "" ORDER BY municipio')
    municipios_db = cursor.fetchall()
    query_base = 'FROM beneficiarios WHERE 1=1'
    params = []
    if q:
        query_base += ' AND (num_doc LIKE %s OR nombres LIKE %s OR apellidos LIKE %s OR codigo_interno LIKE %s)'
        params.extend([f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%'])
    if municipio_filtro:
        query_base += ' AND municipio = %s'
        params.append(municipio_filtro)
    cursor.execute(f'SELECT COUNT(*) as total {query_base}', params)
    total = cursor.fetchone()['total']
    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)
    pagina = max(1, min(pagina, total_paginas))
    offset = (pagina - 1) * por_pagina
    cursor.execute(f'SELECT * {query_base} ORDER BY id DESC LIMIT %s OFFSET %s', params + [por_pagina, offset])
    beneficiarios = cursor.fetchall()
    conn.close()
    return render_template('beneficiarios.html', beneficiarios=beneficiarios, q=q, municipio_filtro=municipio_filtro,
                           municipios=municipios_db, pagina=pagina, total_paginas=total_paginas, total=total)

@app.route('/beneficiarios/buscar-previo', methods=['GET', 'POST'])
@login_required
def buscar_previo():
    if request.method == 'POST':
        tipo_doc = request.form.get('tipo_doc', '').strip()
        num_doc = request.form.get('num_doc', '').strip()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM beneficiarios WHERE TRIM(num_doc) = %s OR REPLACE(num_doc, ' ', '') = REPLACE(%s, ' ', '')", (num_doc, num_doc))
        beneficiario = cursor.fetchone()
        conn.close()
        if beneficiario:
            flash(f'El documento {num_doc} ya está registrado a nombre de {beneficiario["nombres"]} {beneficiario["apellidos"]}.', 'warning')
            return redirect(url_for('ficha_beneficiario', id=beneficiario['id']))
        flash(f'Documento {num_doc} no registrado. Puedes proceder con la creación.', 'info')
        return redirect(url_for('crear_beneficiario', tipo_doc=tipo_doc, num_doc=num_doc))
    return render_template('buscar_previo.html')

@app.route('/beneficiarios/crear', methods=['GET', 'POST'])
@login_required
def crear_beneficiario():
    if request.method == 'POST':
        tipo_doc = request.form.get('tipo_doc')
        num_doc = request.form.get('num_doc', '').strip()
        codigo_interno = request.form.get('codigo_interno') or f"BEN-{random.randint(1000, 9999)}"
        nombres_input = request.form.get('nombres', '').strip()
        apellidos_input = request.form.get('apellidos', '').strip()
        if nombres_input and not apellidos_input:
            partes = nombres_input.split(' ', 1)
            nombres = partes[0]
            apellidos = partes[1] if len(partes) > 1 else ''
        else:
            nombres = nombres_input
            apellidos = apellidos_input
        fecha_nacimiento = request.form.get('fecha_nacimiento', '')
        sexo = request.form.get('sexo', '')
        telefono = request.form.get('telefono', '')
        municipio = request.form.get('municipio', '')
        condicion_poblacional = request.form.get('condicion_poblacional', '')
        discapacidad = request.form.get('discapacidad', '')
        habeas_data = 1 if request.form.get('habeas_data') else 0
        # Validaciones obligatorias
        if not num_doc or not nombres:
            flash('El número de documento y el nombre son obligatorios.', 'danger')
            condiciones, discapacidades = obtener_catalogos()
            return render_template('crear_beneficiario.html', tipo_doc=tipo_doc, num_doc=num_doc, codigo_sugerido=codigo_interno, condiciones=condiciones, discapacidades=discapacidades)
        if not condicion_poblacional:
            flash('Debes seleccionar una condición poblacional.', 'danger')
            condiciones, discapacidades = obtener_catalogos()
            return render_template('crear_beneficiario.html', tipo_doc=tipo_doc, num_doc=num_doc, codigo_sugerido=codigo_interno, condiciones=condiciones, discapacidades=discapacidades)
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO beneficiarios
                (tipo_doc, num_doc, codigo_interno, nombres, apellidos, fecha_nacimiento, sexo, telefono, municipio, condicion_poblacional, discapacidad, habeas_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (tipo_doc, num_doc, codigo_interno, nombres, apellidos, fecha_nacimiento, sexo, telefono, municipio, condicion_poblacional, discapacidad, habeas_data))
            nuevo_id = cursor.lastrowid
            conn.close()
            flash('Beneficiario registrado exitosamente.', 'success')
            return redirect(url_for('ficha_beneficiario', id=nuevo_id))
        except pymysql.IntegrityError:
            conn.close()
            flash(f'El número de documento {num_doc} ya se encuentra registrado.', 'danger')
            return redirect(url_for('listar_beneficiarios'))
    tipo_doc = request.args.get('tipo_doc', 'Cédula de Ciudadanía')
    num_doc = request.args.get('num_doc', '')
    codigo_sugerido = f"BEN-{random.randint(1000, 9999)}"
    condiciones, discapacidades = obtener_catalogos()
    return render_template('crear_beneficiario.html', tipo_doc=tipo_doc, num_doc=num_doc, codigo_sugerido=codigo_sugerido, condiciones=condiciones, discapacidades=discapacidades)

@app.route('/beneficiario/<int:id>')
@app.route('/beneficiarios/<int:id>')
@login_required
def ficha_beneficiario(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM beneficiarios WHERE id = %s', (id,))
    b = cursor.fetchone()
    if not b:
        conn.close()
        flash('Beneficiario no encontrado.', 'danger')
        return redirect(url_for('listar_beneficiarios'))
    cursor.execute('SELECT * FROM nucleo_familiar WHERE beneficiario_id = %s', (id,))
    familia = cursor.fetchall()
    cursor.execute('SELECT * FROM participaciones WHERE beneficiario_id = %s', (id,))
    participaciones = cursor.fetchall()
    cursor.execute('SELECT * FROM atenciones WHERE beneficiario_id = %s', (id,))
    atenciones = cursor.fetchall()
    cursor.execute('SELECT * FROM seguimientos WHERE beneficiario_id = %s', (id,))
    seguimientos = cursor.fetchall()
    conn.close()
    return render_template('ficha.html', b=b, familia=familia, participaciones=participaciones, atenciones=atenciones, seguimientos=seguimientos)

@app.route('/beneficiario/<int:id>/editar', methods=['GET', 'POST'])
@app.route('/beneficiarios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_beneficiario(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM beneficiarios WHERE id = %s', (id,))
    b = cursor.fetchone()
    if not b:
        conn.close()
        flash('Beneficiario no encontrado.', 'danger')
        return redirect(url_for('listar_beneficiarios'))
    if request.method == 'POST':
        tipo_doc = request.form.get('tipo_doc')
        num_doc = request.form.get('num_doc', '').strip()
        codigo_interno = request.form.get('codigo_interno')
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        fecha_nacimiento = request.form.get('fecha_nacimiento')
        sexo = request.form.get('sexo')
        telefono = request.form.get('telefono')
        municipio = request.form.get('municipio')
        condicion_poblacional = request.form.get('condicion_poblacional')
        discapacidad = request.form.get('discapacidad')
        habeas_data = 1 if request.form.get('habeas_data') else 0
        if not num_doc or not nombres:
            flash('El número de documento y el nombre son obligatorios.', 'danger')
            return redirect(url_for('editar_beneficiario', id=id))
        cursor.execute('''
            UPDATE beneficiarios
            SET tipo_doc=%s, num_doc=%s, codigo_interno=%s, nombres=%s, apellidos=%s,
                fecha_nacimiento=%s, sexo=%s, telefono=%s, municipio=%s,
                condicion_poblacional=%s, discapacidad=%s, habeas_data=%s
            WHERE id=%s
        ''', (tipo_doc, num_doc, codigo_interno, nombres, apellidos, fecha_nacimiento, sexo, telefono, municipio, condicion_poblacional, discapacidad, habeas_data, id))
        conn.close()
        flash('Beneficiario actualizado exitosamente.', 'success')
        return redirect(url_for('ficha_beneficiario', id=id))
    conn.close()
    condiciones, discapacidades = obtener_catalogos()
    return render_template('editar_beneficiario.html', b=b, condiciones=condiciones, discapacidades=discapacidades)

@app.route('/beneficiario/<int:id>/eliminar', methods=['POST'])
@app.route('/beneficiarios/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_beneficiario(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM beneficiarios WHERE id = %s', (id,))
    conn.close()
    flash('Beneficiario eliminado del sistema correctamente.', 'success')
    return redirect(url_for('listar_beneficiarios'))

@app.route('/programas')
@login_required
def programas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, CONCAT(b.nombres, ' ', IFNULL(b.apellidos, '')) as beneficiario_nombre, b.codigo_interno
        FROM participaciones p
        JOIN beneficiarios b ON p.beneficiario_id = b.id
        ORDER BY p.id DESC
    ''')
    participaciones = cursor.fetchall()
    cursor.execute('SELECT id, codigo_interno, num_doc, nombres, apellidos FROM beneficiarios ORDER BY nombres')
    beneficiarios = cursor.fetchall()
    conn.close()
    return render_template('programas.html', participaciones=participaciones, beneficiarios=beneficiarios)

@app.route('/programas/crear', methods=['POST'])
@login_required
def crear_programa_general():
    beneficiario_id = request.form.get('beneficiario_id')
    programa_nombre = request.form.get('programa_nombre')
    linea_trabajo = request.form.get('linea_trabajo', '')
    fecha_vinculacion = request.form.get('fecha_vinculacion')
    estado = request.form.get('estado', 'inscrito')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO participaciones (beneficiario_id, programa_nombre, linea_trabajo, fecha_vinculacion, estado)
        VALUES (%s, %s, %s, %s, %s)
    ''', (beneficiario_id, programa_nombre, linea_trabajo, fecha_vinculacion, estado))
    conn.close()
    flash('Beneficiario vinculado al programa exitosamente.', 'success')
    return redirect(url_for('programas'))

@app.route('/atenciones')
@login_required
def atenciones():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.*, CONCAT(b.nombres, ' ', IFNULL(b.apellidos, '')) as beneficiario_nombre, b.codigo_interno
        FROM atenciones a
        JOIN beneficiarios b ON a.beneficiario_id = b.id
        ORDER BY a.id DESC
    ''')
    atenciones = cursor.fetchall()
    cursor.execute('SELECT id, codigo_interno, num_doc, nombres, apellidos FROM beneficiarios ORDER BY nombres')
    beneficiarios = cursor.fetchall()
    conn.close()
    return render_template('atenciones.html', atenciones=atenciones, beneficiarios=beneficiarios)

@app.route('/atenciones/crear', methods=['POST'])
@login_required
def crear_atencion_general():
    beneficiario_id = request.form.get('beneficiario_id')
    tipo = request.form.get('tipo')
    fecha = request.form.get('fecha')
    responsable = request.form.get('responsable')
    descripcion = request.form.get('descripcion')
    resultado = request.form.get('resultado') or request.form.get('remision') or 'Ninguno'
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO atenciones (beneficiario_id, tipo, fecha, responsable, descripcion, remision)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (beneficiario_id, tipo, fecha, responsable, descripcion, resultado))
    conn.close()
    flash('Atención registrada exitosamente.', 'success')
    return redirect(url_for('atenciones'))

@app.route('/seguimientos')
@login_required
def seguimientos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, CONCAT(b.nombres, ' ', IFNULL(b.apellidos, '')) as beneficiario_nombre, b.codigo_interno
        FROM seguimientos s
        JOIN beneficiarios b ON s.beneficiario_id = b.id
        ORDER BY s.id DESC
    ''')
    seguimientos = cursor.fetchall()
    cursor.execute('SELECT id, codigo_interno, num_doc, nombres, apellidos FROM beneficiarios ORDER BY nombres')
    beneficiarios = cursor.fetchall()
    conn.close()
    return render_template('seguimientos.html', seguimientos=seguimientos, beneficiarios=beneficiarios)

@app.route('/seguimientos/crear', methods=['POST'])
@login_required
def crear_seguimiento_general():
    beneficiario_id = request.form.get('beneficiario_id')
    fecha = request.form.get('fecha')
    avance = request.form.get('avance')
    proxima_accion = request.form.get('proxima_accion')
    fecha_proximo_contacto = request.form.get('fecha_proximo_contacto')
    estado_accion = request.form.get('estado_accion', 'Pendiente')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO seguimientos (beneficiario_id, fecha, avance, proxima_accion, fecha_proximo_contacto, estado_accion)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (beneficiario_id, fecha, avance, proxima_accion, fecha_proximo_contacto, estado_accion))
    conn.close()
    flash('Seguimiento registrado exitosamente.', 'success')
    return redirect(url_for('seguimientos'))

@app.route('/certificados')
@login_required
def certificados():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM beneficiarios ORDER BY nombres')
    beneficiarios = cursor.fetchall()
    conn.close()
    return render_template('certificados.html', beneficiarios=beneficiarios)

@app.route('/certificados/imprimir/<int:id>')
@login_required
def imprimir_certificado(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM beneficiarios WHERE id = %s', (id,))
    b = cursor.fetchone()
    cursor.execute('SELECT * FROM participaciones WHERE beneficiario_id = %s', (id,))
    participaciones = cursor.fetchall()
    conn.close()
    if not b:
        flash('Beneficiario no encontrado.', 'danger')
        return redirect(url_for('certificados'))
    return render_template('certificado_documento.html', b=b, participaciones=participaciones)

@app.route('/reportes')
@login_required
def reportes():
    indicadores = obtener_indicadores()
    return render_template('reportes.html', **indicadores)

@app.route('/reportes/exportar')
@login_required
def exportar_reportes():
    indicadores = obtener_indicadores()
    lineas = [
        'Indicador,Valor',
        f'Beneficiarios unicos,{indicadores["total_beneficiarios"]}',
        f'Participaciones,{indicadores["total_participaciones"]}',
        f'Atenciones o ayudas,{indicadores["total_atenciones"]}',
        f'Seguimientos pendientes,{indicadores["seguimientos_pendientes"]}',
        '',
        'Programa,Participaciones'
    ]
    for p in indicadores['programas_resumen']:
        lineas.append(f'"{p["programa_nombre"]}",{p["cantidad"]}')
    lineas.append('')
    lineas.append('Estado de participacion,Cantidad')
    for e in indicadores['estados_resumen']:
        lineas.append(f'"{e["estado"]}",{e["cantidad"]}')
    output = '\ufeff' + '\n'.join(lineas)
    return Response(output, mimetype='text/csv; charset=utf-8', headers={'Content-Disposition': 'attachment;filename=reporte_resumen_uraba.csv'})

@app.route('/reportes/exportar-beneficiarios')
@login_required
@admin_required
def exportar_beneficiarios_csv():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT codigo_interno, tipo_doc, num_doc, nombres, apellidos, fecha_nacimiento, sexo, telefono, municipio, condicion_poblacional, discapacidad,
               IF(habeas_data = 1, 'Autorizado', 'No') as habeas_data
        FROM beneficiarios
        ORDER BY id DESC
    ''')
    filas = cursor.fetchall()
    conn.close()

    columnas = ['Codigo Interno', 'Tipo Documento', 'Documento', 'Nombres', 'Apellidos', 'Fecha Nacimiento', 'Sexo', 'Telefono', 'Municipio', 'Condicion Poblacional', 'Discapacidad', 'Habeas Data']
    csv_rows = [','.join(f'"{col}"' for col in columnas)]
    for f in filas:
        row = [
            f.get('codigo_interno', '') or '',
            f.get('tipo_doc', '') or '',
            f.get('num_doc', '') or '',
            f.get('nombres', '') or '',
            f.get('apellidos', '') or '',
            f.get('fecha_nacimiento', '') or '',
            f.get('sexo', '') or '',
            f.get('telefono', '') or '',
            f.get('municipio', '') or '',
            f.get('condicion_poblacional', '') or '',
            f.get('discapacidad', '') or '',
            f.get('habeas_data', '') or ''
        ]
        csv_rows.append(','.join(f'"{str(val).replace(chr(34), chr(39))}"' for val in row))

    output = '\ufeff' + '\n'.join(csv_rows)
    return Response(output, mimetype='text/csv; charset=utf-8', headers={'Content-Disposition': 'attachment;filename=matriz_beneficiarios_uraba.csv'})

@app.route('/beneficiarios/<int:id>/familiar', methods=['POST'])
@app.route('/beneficiario/<int:id>/familiar', methods=['POST'])
@login_required
def agregar_familiar(id):
    nombre_completo = request.form.get('nombre_completo')
    parentesco = request.form.get('parentesco')
    edad = request.form.get('edad') or None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO nucleo_familiar (beneficiario_id, nombre_completo, parentesco, edad) VALUES (%s, %s, %s, %s)', (id, nombre_completo, parentesco, edad))
    conn.close()
    flash('Integrante familiar agregado.', 'success')
    return redirect(url_for('ficha_beneficiario', id=id))

@app.route('/beneficiarios/<int:id>/programa', methods=['POST'])
@app.route('/beneficiario/<int:id>/programa', methods=['POST'])
@login_required
def vincular_programa(id):
    programa_nombre = request.form.get('programa_nombre')
    linea_trabajo = request.form.get('linea_trabajo')
    fecha_vinculacion = request.form.get('fecha_vinculacion')
    estado = request.form.get('estado', 'inscrito')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO participaciones (beneficiario_id, programa_nombre, linea_trabajo, fecha_vinculacion, estado) VALUES (%s, %s, %s, %s, %s)', (id, programa_nombre, linea_trabajo, fecha_vinculacion, estado))
    conn.close()
    flash('Programa vinculado correctamente.', 'success')
    return redirect(url_for('ficha_beneficiario', id=id))

@app.route('/beneficiarios/<int:id>/atencion', methods=['POST'])
@app.route('/beneficiario/<int:id>/atencion', methods=['POST'])
@login_required
def registrar_atencion(id):
    tipo = request.form.get('tipo')
    fecha = request.form.get('fecha')
    descripcion = request.form.get('descripcion')
    responsable = request.form.get('responsable')
    resultado = request.form.get('resultado') or request.form.get('remision') or 'Ninguno'
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO atenciones (beneficiario_id, tipo, fecha, descripcion, responsable, remision) VALUES (%s, %s, %s, %s, %s, %s)', (id, tipo, fecha, descripcion, responsable, resultado))
    conn.close()
    flash('Atención registrada correctamente.', 'success')
    return redirect(url_for('ficha_beneficiario', id=id))

@app.route('/beneficiarios/<int:id>/seguimiento', methods=['POST'])
@app.route('/beneficiario/<int:id>/seguimiento', methods=['POST'])
@login_required
def registrar_seguimiento(id):
    fecha = request.form.get('fecha')
    avance = request.form.get('avance')
    proxima_accion = request.form.get('proxima_accion')
    fecha_proximo_contacto = request.form.get('fecha_proximo_contacto')
    estado_accion = request.form.get('estado_accion', 'Pendiente')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO seguimientos (beneficiario_id, fecha, avance, proxima_accion, fecha_proximo_contacto, estado_accion) VALUES (%s, %s, %s, %s, %s, %s)''', (id, fecha, avance, proxima_accion, fecha_proximo_contacto, estado_accion))
    conn.close()
    flash('Seguimiento registrado correctamente.', 'success')
    return redirect(url_for('ficha_beneficiario', id=id))

def normalizar_texto(texto):
    texto = (texto or '').lower().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    for ch in '¿?¡!,.;:()"\'':
        texto = texto.replace(ch, ' ')
    return ' '.join(texto.split())

def puntuar_intencion(texto, pistas):
    puntos = 0
    for pista in pistas:
        if pista in texto:
            puntos += len(pista.split())
    return puntos

def responder_asistente(mensaje, usuario, rol):
    t = normalizar_texto(mensaje)
    nombre = (usuario or 'operador').split()[0]
    rol_txt = rol or 'funcionario'
    indicadores = obtener_indicadores()
    intenciones = []

    def agregar(pistas, respuesta):
        puntos = puntuar_intencion(t, pistas)
        if puntos:
            intenciones.append((puntos, respuesta))

    if t in ['hola', 'buenas', 'buen dia', 'buenos dias', 'buenas tardes', 'buenas noches', 'hey', 'saludos', 'que tal', 'como estas', 'como va'] or t.startswith('hola ') or t.startswith('buenas '):
        return f"Hola, {nombre}. ¿En qué te ayudo? Puedo explicarte cómo registrar, vincular un programa, armar la ficha o darte los totales de hoy."
    if t in ['gracias', 'ok', 'listo', 'perfecto', 'vale', 'si', 'de acuerdo', 'muy bien', 'genial']:
        return "Dale. Si se traba algún paso, escríbeme y te digo exactamente dónde entrar."

    agregar(['quien eres', 'que eres', 'como te llamas', 'que puedes', 'ayuda', 'menu', 'opciones', 'que haces'], "Soy el asistente de URABÁ-PAÍS. Puedo orientarte sobre cómo registrar beneficiarios, vincular programas, registrar atenciones y seguimientos, generar certificados o exportar reportes. ¿Qué necesitas?")
    agregar(['rol', 'permiso', 'administrador', 'funcionario', 'login', 'iniciar sesion', 'contrasena', 'clave'], f"Hay dos roles: Administrador (acceso total, puede editar y eliminar) y Funcionario (puede registrar y consultar, pero no editar ni eliminar). Tú estás como {nombre}, rol {rol_txt}.")
    agregar(['crear usuario', 'nuevo usuario', 'agregar usuario', 'gestion de usuarios', 'usuarios'], "Ve a Usuarios en el menú lateral (solo admin). Allí puedes crear nuevos usuarios, cambiar su rol entre Funcionario y Administrador, o eliminarlos.")
    agregar(['duplicado', 'ya existe', 'validar documento', 'buscar documento', 'documento repetido'], "Antes de crear a alguien, usa Beneficiarios > Validar Documento. Si ya existe, abre la ficha directamente. Si no, te redirige al formulario de registro.")
    agregar(['crear beneficiario', 'nuevo beneficiario', 'registrar beneficiario', 'como registro', 'como creo', 'registrar persona'], "Ve a Beneficiarios > Validar Documento > si el doc no aparece, haz clic en + Nuevo Beneficiario. Llena: nombre, documento, municipio, teléfono, condición poblacional y autorización de datos.")
    agregar(['beneficiario', 'personas', 'directorio', 'lista'], f"En Beneficiarios ves el directorio completo. Puedes buscar por nombre, documento o código, filtrar por municipio y navegar por páginas. Hay {indicadores['total_beneficiarios']} personas registradas.")
    agregar(['ficha', '360', 'historial', 'expediente'], "La Ficha 360° es el expediente completo: datos personales, núcleo familiar, programas vinculados, atenciones recibidas y seguimientos. Entra a Beneficiarios y pulsa 'Ficha 360°' en el registro.")
    agregar(['nucleo familiar', 'familia', 'familiar', 'hijo', 'conyuge'], "Dentro de la Ficha 360°, en la sección Núcleo Familiar, pulsa '+ Agregar' para añadir un integrante con nombre, parentesco y edad. El administrador puede eliminar integrantes con el ícono de papelera.")
    agregar(['vincular', 'programa', 'inscrito', 'en proceso', 'finalizado', 'retirado', 'participacion', 'inscribir'], "Ve a Programas > + Vincular a Programa, o desde la Ficha 360° > sección Programas > + Vincular. Selecciona la persona, el programa, la línea de trabajo y el estado.")
    agregar(['eliminar atencion', 'borrar atencion', 'eliminar seguimiento', 'borrar seguimiento', 'eliminar participacion', 'corregir', 'eliminar familiar', 'borrar familiar'], "Puedes eliminar atenciones, seguimientos, participaciones y familiares desde sus respectivos módulos usando el botón de papelera al final de cada fila (solo administrador).")
    agregar(['diferencia', 'atencion y seguimiento', 'diferencia entre'], "Atención = lo que se entregó o realizó hoy (ayuda concreta). Seguimiento = el avance del caso y lo que queda pendiente para después.")
    agregar(['atencion', 'ayuda', 'resultado', 'remision', 'registrar atencion'], "Ve a Atenciones > + Nueva Atención, o desde la Ficha 360° > sección Atenciones. Ingresa tipo, fecha, descripción, responsable y resultado.")
    agregar(['seguimiento', 'proxima accion', 'compromiso', 'pendiente', 'caso'], f"Ve a Seguimientos > + Nuevo Seguimiento. Registra fecha, avance, próxima acción y cuándo volver a contactar. Hay {indicadores['seguimientos_pendientes']} seguimientos pendientes ahora.")
    agregar(['reporte', 'indicador', 'csv', 'exportar', 'estadistica', 'resumen', 'total', 'cuantos', 'cuantas', 'cuanto', 'dashboard', 'municipio', 'datos'], f"Estadísticas actuales: {indicadores['total_beneficiarios']} beneficiarios, {indicadores['total_participaciones']} participaciones, {indicadores['total_atenciones']} atenciones y {indicadores['seguimientos_pendientes']} seguimientos pendientes. Para exportar en CSV ve a Reportes > Exportar.")
    agregar(['certificado', 'imprimir', 'constancia', 'documento'], "El certificado de participación sale desde Certificados (menú lateral) o desde la Ficha 360° > 'Imprimir Certificado'. Se abre en una página lista para imprimir.")
    agregar(['habeas', 'autorizacion', 'datos personales', 'privacidad', 'ley'], "Al registrar un beneficiario se marca si autorizó el tratamiento de sus datos (Habeas Data). Los reportes exportados no contienen datos personales identificables.")
    agregar(['oscuro', 'claro', 'tema', 'modo', 'apariencia', 'color'], "Usa el botón de luna/sol en la parte inferior del menú lateral para cambiar entre modo claro y oscuro.")
    agregar(['configuracion', 'configurar', 'ajustes', 'sistema'], f"La configuración solo la ve el administrador. Desde allí puedes cambiar la contraseña. Tu rol actual es {rol_txt}.")
    agregar(['paginacion', 'pagina', 'siguiente', 'anterior', 'ver mas'], "La lista de beneficiarios está paginada de 15 en 15. Usa los botones Anterior y Siguiente al pie de la tabla, o busca directamente por nombre o documento.")

    if intenciones:
        intenciones.sort(key=lambda x: x[0], reverse=True)
        return intenciones[0][1]
    return f"No te seguí del todo, {nombre}. Pregúntame algo concreto: cómo registro a alguien, cómo vinculo un programa, cómo elimino un registro, o cuántas personas hay registradas hoy."

# ─── Eliminar registros de atenciones, seguimientos, participaciones y familiares ─

@app.route('/atenciones/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_atencion(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM atenciones WHERE id = %s', (id,))
    conn.close()
    flash('Atención eliminada correctamente.', 'success')
    ref = request.referrer or ''
    if 'ficha' in ref or 'beneficiario' in ref:
        return redirect(ref)
    return redirect(url_for('atenciones'))

@app.route('/seguimientos/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_seguimiento(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM seguimientos WHERE id = %s', (id,))
    conn.close()
    flash('Seguimiento eliminado correctamente.', 'success')
    ref = request.referrer or ''
    if 'ficha' in ref or 'beneficiario' in ref:
        return redirect(ref)
    return redirect(url_for('seguimientos'))

@app.route('/participaciones/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_participacion(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM participaciones WHERE id = %s', (id,))
    conn.close()
    flash('Participación eliminada correctamente.', 'success')
    ref = request.referrer or ''
    if 'ficha' in ref or 'beneficiario' in ref:
        return redirect(ref)
    return redirect(url_for('programas'))

@app.route('/familiar/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_familiar(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT beneficiario_id FROM nucleo_familiar WHERE id = %s', (id,))
    row = cursor.fetchone()
    beneficiario_id = row['beneficiario_id'] if row else None
    cursor.execute('DELETE FROM nucleo_familiar WHERE id = %s', (id,))
    conn.close()
    flash('Integrante familiar eliminado correctamente.', 'success')
    if beneficiario_id:
        return redirect(url_for('ficha_beneficiario', id=beneficiario_id))
    return redirect(url_for('listar_beneficiarios'))

@app.route('/api/asistente', methods=['POST'])
@login_required
def api_asistente():
    data = request.get_json() or {}
    mensaje = data.get('mensaje', '').strip()
    if not mensaje:
        return jsonify({'respuesta': 'Escríbeme la duda y te oriento.'}), 400
    respuesta = responder_asistente(mensaje, session.get('usuario'), session.get('rol'))
    return jsonify({'respuesta': respuesta})

@app.route('/api/buscar_global')
@login_required
def api_buscar_global():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify({'resultados': []})

    conn = get_db_connection()
    cursor = conn.cursor()
    like_q = f'%{q}%'
    cursor.execute('''
        SELECT id, codigo_interno, num_doc, tipo_doc, CONCAT(nombres, ' ', IFNULL(apellidos, '')) as nombre, municipio
        FROM beneficiarios
        WHERE nombres LIKE %s OR apellidos LIKE %s OR num_doc LIKE %s OR codigo_interno LIKE %s
        LIMIT 8
    ''', (like_q, like_q, like_q, like_q))
    beneficiarios = cursor.fetchall()
    conn.close()

    resultados = []
    # Accesos rápidos del sistema
    modulos = [
        {'titulo': 'Panel de Control (Dashboard)', 'tipo': 'Módulo', 'url': url_for('dashboard'), 'icon': 'bi-grid-1x2-fill'},
        {'titulo': 'Beneficiarios Únicos', 'tipo': 'Módulo', 'url': url_for('listar_beneficiarios'), 'icon': 'bi-people-fill'},
        {'titulo': 'Programas Sociales', 'tipo': 'Módulo', 'url': url_for('programas'), 'icon': 'bi-diagram-3-fill'},
        {'titulo': 'Atenciones y Ayudas', 'tipo': 'Módulo', 'url': url_for('atenciones'), 'icon': 'bi-heart-pulse-fill'},
        {'titulo': 'Seguimientos y Alertas', 'tipo': 'Módulo', 'url': url_for('seguimientos'), 'icon': 'bi-journal-check'},
        {'titulo': 'Reportes y Métricas', 'tipo': 'Módulo', 'url': url_for('reportes'), 'icon': 'bi-bar-chart-line-fill'},
        {'titulo': 'Certificados QR', 'tipo': 'Módulo', 'url': url_for('certificados'), 'icon': 'bi-file-earmark-text-fill'},
        {'titulo': 'Nuevo Registro de Beneficiario', 'tipo': 'Acción', 'url': url_for('crear_beneficiario'), 'icon': 'bi-person-plus-fill'}
    ]
    for m in modulos:
        if q.lower() in m['titulo'].lower():
            resultados.append(m)

    for b in beneficiarios:
        resultados.append({
            'titulo': f"{b['nombre']} ({b['codigo_interno']})",
            'subtitulo': f"Doc: {b['tipo_doc']} {b['num_doc']} · {b['municipio'] or 'Urabá'}",
            'tipo': 'Beneficiario',
            'url': url_for('ficha_beneficiario', id=b['id']),
            'icon': 'bi-person-badge-fill'
        })

    return jsonify({'resultados': resultados})

@app.route('/usuarios')
@login_required
@admin_required
def listar_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nombre, correo, rol FROM usuarios ORDER BY id')
    usuarios = cursor.fetchall()
    conn.close()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuarios/crear', methods=['POST'])
@login_required
@admin_required
def crear_usuario():
    nombre = request.form.get('nombre', '').strip()
    correo = request.form.get('correo', '').strip().lower()
    password = request.form.get('password', '')
    rol = request.form.get('rol', 'funcionario')
    if not nombre or not correo or not password:
        flash('Todos los campos son obligatorios para crear un usuario.', 'danger')
        return redirect(url_for('listar_usuarios'))
    if len(password) < 4:
        flash('La contraseña debe tener al menos 4 caracteres.', 'warning')
        return redirect(url_for('listar_usuarios'))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO usuarios (nombre, correo, password, rol) VALUES (%s, %s, %s, %s)',
            (nombre, correo, generate_password_hash(password), rol)
        )
        conn.close()
        flash(f'Usuario {nombre} creado correctamente.', 'success')
    except pymysql.IntegrityError:
        conn.close()
        flash(f'El correo {correo} ya está registrado.', 'danger')
    return redirect(url_for('listar_usuarios'))

@app.route('/usuarios/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_usuario(id):
    if id == session.get('usuario_id'):
        flash('No puedes eliminar tu propio usuario.', 'danger')
        return redirect(url_for('listar_usuarios'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM usuarios WHERE id = %s', (id,))
    conn.close()
    flash('Usuario eliminado correctamente.', 'success')
    return redirect(url_for('listar_usuarios'))

@app.route('/usuarios/<int:id>/cambiar_rol', methods=['POST'])
@login_required
@admin_required
def cambiar_rol_usuario(id):
    if id == session.get('usuario_id'):
        flash('No puedes cambiar tu propio rol.', 'danger')
        return redirect(url_for('listar_usuarios'))
    nuevo_rol = request.form.get('rol', 'funcionario')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE usuarios SET rol = %s WHERE id = %s', (nuevo_rol, id))
    conn.close()
    flash('Rol actualizado correctamente.', 'success')
    return redirect(url_for('listar_usuarios'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
