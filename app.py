import os

import unicodedata

import hashlib

from datetime import datetime, date

import pymysql

import pymysql.cursors

import random

import time

from datetime import timedelta

from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify, session, send_file

from werkzeug.security import generate_password_hash, check_password_hash





app = Flask(__name__)



# Configuración de Seguridad de Sesiones y Cookies (OWASP)

app.config.update(

    SECRET_KEY=os.environ.get('SECRET_KEY', 'uraba_pais_gov_sec_token_2026_9e8f7a6b5c4d3e2f'),

    SESSION_COOKIE_HTTPONLY=True,

    SESSION_COOKIE_SAMESITE='Lax',

    PERMANENT_SESSION_LIFETIME=timedelta(hours=8)

)

app.secret_key = app.config['SECRET_KEY']



# Conexión optimizada (127.0.0.1 previene lag de resolución DNS IPv6 en Windows)

DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')

DB_USER = os.environ.get('DB_USER', 'root')

DB_PASSWORD = os.environ.get('DB_PASSWORD', 'root')

DB_NAME = os.environ.get('DB_NAME', 'uraba_pais_db')



# Seguridad: Limitador de intentos fallidos en login (Mitigación de Fuerza Bruta)

INTENTOS_LOGIN = {}

MAX_INTENTOS_FALLIDOS = 5

TIEMPO_BLOQUEO_SEGUNDOS = 300  # 5 minutos



# Rendimiento: Cache en memoria de indicadores analíticos

_cache_indicadores = None

_cache_indicadores_ts = 0.0

CACHE_INDICADORES_TTL = 30.0  # 30 segundos



def invalidar_cache_indicadores():

    global _cache_indicadores, _cache_indicadores_ts

    _cache_indicadores = None

    _cache_indicadores_ts = 0.0



def registrar_auditoria(accion, detalle, nivel='INFO', usuario=None, ip=None):

    """Registra una operación en la bitácora inalterable de auditoría (Ley 1581 / Habeas Data)."""

    try:

        if usuario is None:

            usuario = session.get('usuario') or 'Sistema'

        if ip is None:

            ip = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1')

            if ',' in ip:

                ip = ip.split(',')[0].strip()

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute("""

            INSERT INTO auditoria (usuario, accion, detalle, ip_origen, nivel, fecha_hora)

            VALUES (%s, %s, %s, %s, %s, NOW())

        """, (usuario, accion, detalle, ip, nivel))

        conn.commit()

        conn.close()

    except Exception:

        pass



def calcular_ivs(b, num_participaciones=0, num_familiares=0):

    """

    Calcula el Índice Multidimensional de Vulnerabilidad Social (IVS: 0-100)

    Basado en metodología CONPES / Sisbén IV.

    """

    score = 0

    desglose = []



    # 1. Condición Poblacional (Máx 35 pts)

    cond = (b.get('condicion_poblacional') or '').lower().strip()

    pts_cond = 5

    motivo_cond = "Población general registrada (+5)"

    if any(k in cond for k in ['víctima', 'victima', 'desplazad', 'conflicto']):

        pts_cond = 35

        motivo_cond = "Víctima del conflicto armado / Desplazamiento forzado (+35)"

    elif any(k in cond for k in ['extrema', 'indigente', 'calle']):

        pts_cond = 30

        motivo_cond = "Pobreza extrema multidimensional (+30)"

    elif any(k in cond for k in ['indígena', 'indigena', 'afro', 'negritudes', 'palenquer', 'raizal', 'etnica', 'étnica']):

        pts_cond = 25

        motivo_cond = "Población étnica o afrocolombiana (+25)"

    elif any(k in cond for k in ['migrante', 'refugiado', 'retornado']):

        pts_cond = 25

        motivo_cond = "Población migrante o refugiada (+25)"

    elif any(k in cond for k in ['cabeza', 'madre comunitaria', 'cuidador', 'cuidadora']):

        pts_cond = 20

        motivo_cond = "Jefatura monoparental / Cuidador(a) (+20)"

    elif cond and cond not in ['ninguna', 'ninguno', 'general', 'sin condicion', 'sin condición']:

        pts_cond = 15

        motivo_cond = f"Condición vulnerable: {cond.capitalize()} (+15)"



    score += pts_cond

    desglose.append({'categoria': 'Condición Poblacional', 'puntos': pts_cond, 'detalle': motivo_cond})



    # 2. Inclusión y Discapacidad (Máx 25 pts)

    disc = (b.get('discapacidad') or '').lower().strip()

    pts_disc = 0

    if disc and disc not in ['ninguna', 'ninguno', 'no', 'sin registro', '']:

        pts_disc = 25

        motivo_disc = f"Condición de discapacidad: {b.get('discapacidad')} (+25)"

    else:

        pts_disc = 0

        motivo_disc = "Sin reporte de discapacidad (+0)"

    score += pts_disc

    desglose.append({'categoria': 'Discapacidad e Inclusión', 'puntos': pts_disc, 'detalle': motivo_disc})



    # 3. Ciclo Vital / Edad (Máx 20 pts)

    fn = b.get('fecha_nacimiento')

    edad = None

    pts_edad = 5

    motivo_edad = "Rango de edad productiva (+5)"

    if fn:

        try:

            if hasattr(fn, 'year'):

                nac = fn

            else:

                nac = datetime.strptime(str(fn)[:10], '%Y-%m-%d').date()

            hoy = date.today()

            edad = hoy.year - nac.year - ((hoy.month, hoy.day) < (nac.month, nac.day))

            if edad >= 60:

                pts_edad = 20

                motivo_edad = f"Adulto mayor ({edad} años) - Alta vulnerabilidad (+20)"

            elif edad <= 5:

                pts_edad = 20

                motivo_edad = f"Primera infancia ({edad} años) - Prioridad CONPES (+20)"

            elif edad <= 12:

                pts_edad = 15

                motivo_edad = f"Infancia escolar ({edad} años) (+15)"

            elif edad <= 17:

                pts_edad = 10

                motivo_edad = f"Adolescencia ({edad} años) (+10)"

            else:

                pts_edad = 5

                motivo_edad = f"Adulto en edad productiva ({edad} años) (+5)"

        except Exception:

            pts_edad = 5

            motivo_edad = "Edad no verificable (+5)"

    score += pts_edad

    desglose.append({'categoria': 'Ciclo Vital / Edad', 'puntos': pts_edad, 'detalle': motivo_edad, 'edad': edad})



    # 4. Núcleo Familiar / Dependencia (Máx 15 pts)

    pts_fam = 0

    if num_familiares >= 4:

        pts_fam = 15

        motivo_fam = f"Hogar numeroso ({num_familiares} personas a cargo) (+15)"

    elif num_familiares >= 2:

        pts_fam = 10

        motivo_fam = f"Carga familiar ({num_familiares} personas a cargo) (+10)"

    elif num_familiares >= 1:

        pts_fam = 5

        motivo_fam = f"Hogar con 1 familiar registrado (+5)"

    else:

        pts_fam = 0

        motivo_fam = "Sin dependientes familiares en sistema (+0)"

    score += pts_fam

    desglose.append({'categoria': 'Dependencia Familiar', 'puntos': pts_fam, 'detalle': motivo_fam, 'cantidad': num_familiares})



    # 5. Cobertura Institucional (Máx 10 pts)

    pts_cob = 0

    if num_participaciones == 0:

        pts_cob = 10

        motivo_cob = "Desprotección (Sin programas sociales activos) (+10)"

    elif num_participaciones == 1:

        pts_cob = 5

        motivo_cob = "Cobertura inicial (1 programa social) (+5)"

    else:

        pts_cob = 0

        motivo_cob = f"Cobertura suficiente ({num_participaciones} programas activos) (+0)"

    score += pts_cob

    desglose.append({'categoria': 'Cobertura Institucional', 'puntos': pts_cob, 'detalle': motivo_cob})



    score = min(max(score, 5), 100)



    if score >= 70:

        nivel = "CRÍTICO"

        clase = "danger"

        badge_bg = "#ef4444"

        recomendacion = "Prioridad Nivel 1: Focalización urgente para entrega de subsidio humanitario y atención psicosocial."

    elif score >= 50:

        nivel = "ALTO"

        clase = "warning"

        badge_bg = "#f59e0b"

        recomendacion = "Prioridad Nivel 2: Asignación prioritaria en programas productivos y seguridad alimentaria."

    elif score >= 25:

        nivel = "MODERADO"

        clase = "info"

        badge_bg = "#0284c7"

        recomendacion = "Prioridad Nivel 3: Acompañamiento ordinario y vinculación a formación técnica regional."

    else:

        nivel = "BAJO"

        clase = "success"

        badge_bg = "#10b981"

        recomendacion = "Prioridad Nivel 4: Seguimiento institucional periódico sin riesgo inminente."



    return {

        'score': score,

        'nivel': nivel,

        'clase': clase,

        'badge_bg': badge_bg,

        'desglose': desglose,

        'recomendacion': recomendacion,

        'edad': edad

    }





@app.errorhandler(404)

def error_404(e):

    return render_template('error.html', codigo=404, titulo="Página no encontrada", mensaje="El recurso al que intentas acceder no existe o fue movido."), 404



@app.errorhandler(500)

def error_500(e):

    return render_template('error.html', codigo=500, titulo='Error interno del servidor', mensaje='Ocurrió un error inesperado controlado. El sistema ha protegido tus datos y la incidencia fue aislada.'), 500

def get_db_connection():

    conn = pymysql.connect(

        host=DB_HOST,

        user=DB_USER,

        password=DB_PASSWORD,

        database=DB_NAME,

        charset='utf8mb4',

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

        'color_tema_actual': session.get('color_tema', 'verde'),

        'fuente_actual': session.get('fuente', 'Inter'),

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



def obtener_indicadores(forzar=False):

    global _cache_indicadores, _cache_indicadores_ts

    ahora = time.time()

    if not forzar and _cache_indicadores is not None and (ahora - _cache_indicadores_ts) < CACHE_INDICADORES_TTL:

        return _cache_indicadores



    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute('CALL sp_obtener_indicadores_dashboard()')

    row = cursor.fetchone() or {}

    total_beneficiarios = row.get('total_beneficiarios', 0)

    total_participaciones = row.get('total_participaciones', 0)

    total_atenciones = row.get('total_atenciones', 0)

    seguimientos_pendientes = row.get('seguimientos_pendientes', 0)

    # Vaciar resultados adicionales del CALL

    try:

        cursor.nextset()

    except Exception:

        pass

    cursor.execute('CALL sp_programas_resumen()')

    programas_resumen = cursor.fetchall()

    try:

        cursor.nextset()

    except Exception:

        pass

    cursor.execute('CALL sp_estados_participaciones()')

    estados_resumen = cursor.fetchall()

    try:

        cursor.nextset()

    except Exception:

        pass

    cursor.execute('CALL sp_municipios_resumen()')

    municipios_resumen = cursor.fetchall()

    try:

        cursor.nextset()

    except Exception:

        pass

    conn.close()

    _cache_indicadores = {

        'total_beneficiarios': total_beneficiarios,

        'total_participaciones': total_participaciones,

        'total_atenciones': total_atenciones,

        'seguimientos_pendientes': seguimientos_pendientes,

        'programas_resumen': programas_resumen,

        'estados_resumen': estados_resumen,

        'municipios_resumen': municipios_resumen

    }

    _cache_indicadores_ts = ahora

    return _cache_indicadores



_cache_catalogos = None



def obtener_catalogos():

    global _cache_catalogos

    if _cache_catalogos is not None:

        return _cache_catalogos

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

        _cache_catalogos = (condiciones, discapacidades)

        return _cache_catalogos

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

        client_ip = request.remote_addr or '127.0.0.1'

        lock_key = f"{client_ip}:{correo}"

        ahora = time.time()



        # Mitigación de Fuerza Bruta: verificar si la cuenta/IP está bloqueada

        record = INTENTOS_LOGIN.get(lock_key)

        if record and record.get('bloqueado_hasta', 0) > ahora:

            segundos = int(record['bloqueado_hasta'] - ahora)

            minutos = max(1, (segundos + 59) // 60)

            flash(f'Acceso bloqueado por seguridad tras reiterados intentos fallidos. Por favor espera {minutos} minuto(s).', 'danger')

            return render_template('login.html')



        if not correo or not password:

            flash('Por favor ingrese su correo y contraseña.', 'warning')

            return redirect(url_for('login'))



        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute("CALL sp_obtener_usuario_por_correo(%s)", (correo,))

        usuario = cursor.fetchone()



        es_valido = False

        if usuario:

            db_pass = usuario['password']

            if db_pass.startswith('pbkdf2:') or db_pass.startswith('scrypt:'):

                es_valido = check_password_hash(db_pass, password)

            else:

                es_valido = (db_pass == password)

                if es_valido:

                    # Auto-upgrade de contraseña en texto plano a hash seguro

                    cursor.execute('CALL sp_actualizar_password_usuario(%s, %s)', (usuario['id'], generate_password_hash(password)))

                    try:

                        cursor.nextset()

                    except Exception:

                        pass

                    conn.commit()

        conn.close()



        if es_valido:

            # Login exitoso: restablecer contador de intentos y regenerar sesión (anti Session Fixation)

            INTENTOS_LOGIN.pop(lock_key, None)

            session.clear()

            session.permanent = True

            session['usuario'] = usuario['nombre'] if usuario['nombre'] else usuario['correo']

            session['usuario_id'] = usuario['id']

            session['correo'] = usuario['correo']

            session['rol'] = usuario.get('rol') or 'funcionario'

            session['es_admin'] = (session['rol'].lower() == 'administrador')

            registrar_auditoria('INICIO_SESION', f"Ingreso exitoso del usuario '{session['usuario']}' con rol '{session['rol']}'", 'SEGURIDAD', usuario=session['usuario'])

            flash(f"¡Bienvenido, {session['usuario']} ({session['rol']})!", 'success')

            return redirect(url_for('dashboard'))

        else:

            # Registrar intento fallido

            if lock_key not in INTENTOS_LOGIN:

                INTENTOS_LOGIN[lock_key] = {'intentos': 1, 'bloqueado_hasta': 0}

            else:

                INTENTOS_LOGIN[lock_key]['intentos'] += 1

                if INTENTOS_LOGIN[lock_key]['intentos'] >= MAX_INTENTOS_FALLIDOS:

                    INTENTOS_LOGIN[lock_key]['bloqueado_hasta'] = ahora + TIEMPO_BLOQUEO_SEGUNDOS

                    flash('Has superado el límite de intentos (5). Tu acceso ha sido bloqueado temporalmente por 5 minutos por seguridad.', 'danger')

                    return render_template('login.html')



            registrar_auditoria('FALLO_LOGIN', f"Intento fallido de autenticación para correo '{correo}'", 'WARNING', usuario=correo)

            intentos_restantes = MAX_INTENTOS_FALLIDOS - INTENTOS_LOGIN[lock_key]['intentos']

            if 0 < intentos_restantes <= 2:

                flash(f'Correo o contraseña incorrectos. Advertencia de seguridad: te quedan {intentos_restantes} intento(s) antes del bloqueo temporal.', 'warning')

            else:

                flash('Correo o contraseña incorrectos.', 'danger')



    return render_template('login.html')



@app.route('/logout')

def logout():

    u = session.get('usuario') or 'Usuario'

    razon = request.args.get('razon', '')

    if razon == 'inactividad':

        registrar_auditoria('SESION_EXPIRADA', f"Cierre automático de sesión por inactividad prolongada (OWASP Session Timeout) del usuario '{u}'", 'ALERTA', usuario=u)

        session.clear()

        flash('Su sesión ha expirado automáticamente por inactividad prolongada para salvaguardar la información ciudadana.', 'warning')

    else:

        registrar_auditoria('CIERRE_SESION', f"Cierre voluntario de sesión del usuario '{u}'", 'INFO', usuario=u)

        session.clear()

        flash('Sesión cerrada correctamente.', 'info')

    return redirect(url_for('login'))



@app.route('/api/mantener-sesion', methods=['POST'])

@login_required

def api_mantener_sesion():

    session.modified = True

    return jsonify({'status': 'ok', 'mensaje': 'Sesión activa renovada exitosamente'})



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

    session['color_tema'] = request.form.get('color_tema', 'verde')

    flash('¡Paleta de color y tipografía actualizadas correctamente!', 'success')

    return redirect(url_for('configuracion'))



@app.route('/configuracion/cambiar_password', methods=['POST'])

@login_required

@admin_required

def cambiar_password():

    password_actual = request.form.get('password_actual', '')

    nueva_password = request.form.get('password_nueva') or request.form.get('nueva_password', '')

    confirmar_password = request.form.get('password_confirmar') or request.form.get('confirmar_password', '')

    

    if not password_actual:

        flash('Debes ingresar tu contraseña actual para autorizar el cambio.', 'danger')

        return redirect(url_for('configuracion'))

        

    usuario_id = session.get('usuario_id')

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("CALL sp_obtener_usuario_por_id(%s)", (usuario_id,))

    usuario = cursor.fetchone()

    

    if not usuario:

        conn.close()

        flash('Usuario no encontrado.', 'danger')

        return redirect(url_for('configuracion'))

        

    db_pass = usuario['password']

    pass_ok = False

    if db_pass.startswith('pbkdf2:') or db_pass.startswith('scrypt:'):

        pass_ok = check_password_hash(db_pass, password_actual)

    else:

        pass_ok = (db_pass == password_actual)

        

    if not pass_ok:

        conn.close()

        flash('La contraseña actual es incorrecta.', 'danger')

        return redirect(url_for('configuracion'))

        

    if nueva_password != confirmar_password:

        conn.close()

        flash('Las nuevas contraseñas no coinciden.', 'danger')

        return redirect(url_for('configuracion'))

        

    if len(nueva_password) < 6:

        conn.close()

        flash('Por seguridad institucional, la nueva contraseña debe tener al menos 6 caracteres.', 'warning')

        return redirect(url_for('configuracion'))

        

    password_encriptada = generate_password_hash(nueva_password)

    cursor.execute("CALL sp_actualizar_password_usuario(%s, %s)", (usuario_id, password_encriptada))

    conn.close()

    flash('¡Contraseña actualizada de forma segura y encriptada!', 'success')

    return redirect(url_for('configuracion'))



@app.route('/configuracion/respaldo_db')

@login_required

@admin_required

def respaldo_db():

    try:

        conn = get_db_connection()

        cursor = conn.cursor()



        cursor.execute("SHOW TABLES")

        tablas_raw = cursor.fetchall()

        tablas = [list(r.values())[0] for r in tablas_raw]



        ahora_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        timestamp_archivo = datetime.now().strftime('%Y%m%d_%H%M%S')

        usuario_actual = session.get('usuario', 'Admin')

        rol_actual = session.get('rol', 'admin')



        sql_body = []

        sql_body.append("SET FOREIGN_KEY_CHECKS=0;\n")

        sql_body.append("SET NAMES utf8mb4;\n\n")



        for tabla in tablas:

            sql_body.append(f"-- --------------------------------------------------------\n")

            sql_body.append(f"-- Estructura y datos de la tabla `{tabla}`\n")

            sql_body.append(f"-- --------------------------------------------------------\n\n")



            cursor.execute(f"SHOW CREATE TABLE `{tabla}`")

            create_info = cursor.fetchone()

            create_sql = create_info.get('Create Table') or list(create_info.values())[1]

            sql_body.append(f"DROP TABLE IF EXISTS `{tabla}`;\n")

            sql_body.append(f"{create_sql};\n\n")



            cursor.execute(f"SELECT * FROM `{tabla}`")

            filas = cursor.fetchall()

            if filas:

                sql_body.append(f"-- Volcado de datos para la tabla `{tabla}` ({len(filas)} registros)\n")

                columnas = list(filas[0].keys())

                cols_str = ", ".join([f"`{c}`" for c in columnas])



                for fila in filas:

                    valores = []

                    for c in columnas:

                        v = fila[c]

                        if v is None:

                            valores.append("NULL")

                        elif isinstance(v, (int, float)):

                            valores.append(str(v))

                        else:

                            v_str = str(v).replace("\\", "\\\\").replace("'", "''")

                            valores.append(f"'{v_str}'")

                    sql_body.append(f"INSERT INTO `{tabla}` ({cols_str}) VALUES ({', '.join(valores)});\n")

                sql_body.append("\n")



        sql_body.append("SET FOREIGN_KEY_CHECKS=1;\n")

        cuerpo_dump = "".join(sql_body)



        sha256_hash = hashlib.sha256(cuerpo_dump.encode('utf-8')).hexdigest().upper()



        header = f"""-- ====================================================================

-- PLATAFORMA GUBERNAMENTAL URABÁ-PAÍS (SUBREGIÓN DE URABÁ, ANTIOQUIA)

-- COPIA DE SEGURIDAD Y RESPALDO CRIPTOGRÁFICO DE BASE DE DATOS

-- ====================================================================

-- Fecha y Hora de Generación : {ahora_str}

-- Operador Responsable       : {usuario_actual} ({rol_actual})

-- Estándar de Seguridad      : ISO/IEC 27001 - Control A.12.3.1 (Copias de Respaldo)

-- Algoritmo Criptográfico    : SHA-256 (Integridad Anti-Alteración / Anti-Ransomware)

-- Hash de Verificación       : {sha256_hash}

-- Total de Tablas Respaldadas: {len(tablas)} tablas

-- Sistema Gestor             : MySQL / MariaDB (uraba_pais_db)

-- Marco Legal                : Ley Estatutaria 1581 de 2012 (Protección de Datos Personales)

-- ====================================================================



"""

        dump_completo = header + cuerpo_dump



        registrar_auditoria('BACKUP_CRIPTOGRAFICO', f"Generación de respaldo SQL criptográfico SHA-256: {sha256_hash[:16]}... ({len(tablas)} tablas)", 'ALERTA', usuario=usuario_actual)



        return Response(

            dump_completo,

            mimetype="application/sql",

            headers={

                "Content-Disposition": f"attachment; filename=respaldo_uraba_pais_{timestamp_archivo}.sql",

                "X-SHA256-Checksum": sha256_hash

            }

        )

    except Exception as e:

        registrar_auditoria('ERROR_BACKUP', f"Fallo al generar respaldo de BD: {str(e)}", 'CRITICO')

        flash(f'Error al generar la copia de seguridad: {str(e)}', 'danger')

        return redirect(url_for('configuracion'))



@app.route('/')

@app.route('/')

@app.route('/inicio')

@app.route('/home')

def landing():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute('CALL sp_obtener_indicadores_dashboard()')

    _ind = cursor.fetchone() or {}

    total_beneficiarios = _ind.get('total_beneficiarios', 0)

    total_atenciones = _ind.get('total_atenciones', 0)

    total_programas = _ind.get('total_participaciones', 0)

    try:

        cursor.nextset()

    except Exception:

        pass

    conn.close()

    return render_template(

        'landing.html',

        total_beneficiarios=total_beneficiarios,

        total_atenciones=total_atenciones,

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

    sexo_filtro = request.args.get('sexo', '').strip()

    condicion_filtro = request.args.get('condicion', '').strip()

    ivs_filtro = request.args.get('ivs', '').strip()

    try:

        pagina = int(request.args.get('pagina', 1))

    except ValueError:

        pagina = 1

    por_pagina = 20

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute('CALL sp_catalogos_beneficiarios()')

    _cats = cursor.fetchall()

    try:

        cursor.nextset()

    except Exception:

        pass

    municipios_db = [{'municipio': r['valor']} for r in _cats if r.get('tipo') == 'municipio']

    condiciones_en_db = [r['valor'].strip() for r in _cats if r.get('tipo') == 'condicion_poblacional' and r.get('valor')]

    catalog_conds, _ = obtener_catalogos()

    condiciones_catalogo = [c['condicion'].strip() for c in catalog_conds if c.get('condicion')]

    seen_cond = {}

    for c in condiciones_catalogo + condiciones_en_db:

        k = c.strip().lower()

        if k and k not in seen_cond:

            seen_cond[k] = c.strip()

    condiciones_todas = sorted(list(seen_cond.values()))



    sexos_en_db = [r['valor'].strip() for r in _cats if r.get('tipo') == 'sexo' and r.get('valor')]

    seen_sex = {}

    for s in ['Masculino', 'Femenino', 'Otro'] + sexos_en_db:

        k = s.strip().lower()

        if k and k not in seen_sex:

            seen_sex[k] = s.strip()

    sexos_todos = sorted(list(seen_sex.values()))



    offset = (pagina - 1) * por_pagina



    if ivs_filtro:

        # Consulta mediante Stored Procedure de Búsqueda y Filtrado

        cursor.execute("CALL sp_buscar_beneficiarios(%s, %s, %s, %s, %s, %s, @p_total)", 

                       (q, municipio_filtro, sexo_filtro, condicion_filtro, 1000, 0))

        todos_candidatos = cursor.fetchall()

        filtrados_ivs = []

        for b in todos_candidatos:

            b['ivs'] = calcular_ivs(b)

            if b['ivs']['nivel'] == ivs_filtro:

                filtrados_ivs.append(b)

        total = len(filtrados_ivs)

        total_paginas = max(1, (total + por_pagina - 1) // por_pagina)

        pagina = max(1, min(pagina, total_paginas))

        offset = (pagina - 1) * por_pagina

        beneficiarios = filtrados_ivs[offset:offset + por_pagina]

    else:

        # Invocación directa del Stored Procedure de Búsqueda con Paginación MySQL

        cursor.execute("CALL sp_buscar_beneficiarios(%s, %s, %s, %s, %s, %s, @p_total)", 

                       (q, municipio_filtro, sexo_filtro, condicion_filtro, por_pagina, offset))

        beneficiarios = cursor.fetchall()

        cursor.execute("SELECT @p_total as total")

        total = cursor.fetchone()['total'] or 0

        total_paginas = max(1, (total + por_pagina - 1) // por_pagina)

        pagina = max(1, min(pagina, total_paginas))

        for b in beneficiarios:

            b['ivs'] = calcular_ivs(b)

    conn.close()

    return render_template(

        'beneficiarios.html',

        beneficiarios=beneficiarios,

        q=q,

        municipio_filtro=municipio_filtro,

        sexo_filtro=sexo_filtro,

        condicion_filtro=condicion_filtro,

        ivs_filtro=ivs_filtro,

        municipios=municipios_db,

        condiciones=condiciones_todas,

        sexos=sexos_todos,

        pagina=pagina,

        total_paginas=total_paginas,

        total=total

    )



@app.route('/beneficiarios/buscar-previo', methods=['GET', 'POST'])

@login_required

def buscar_previo():

    if request.method == 'POST':

        tipo_doc = request.form.get('tipo_doc', '').strip()

        num_doc = request.form.get('num_doc', '').strip()

        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute("CALL sp_validar_documento_beneficiario(%s)", (num_doc,))

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

            invalidar_cache_indicadores()

            flash('Beneficiario registrado exitosamente.', 'success')

            return redirect(url_for('ficha_beneficiario', id=nuevo_id))

        except pymysql.IntegrityError:

            conn.close()

            flash(f'El número de documento {num_doc} ya se encuentra registrado.', 'danger')

            return redirect(url_for('listar_beneficiarios'))

    tipo_doc = request.args.get('tipo_doc', 'Cédula de Ciudadanía')

    num_doc = request.args.get('num_doc', '')

    municipio_sel = request.args.get('municipio', '')

    condicion_sel = request.args.get('condicion', '')

    discapacidad_sel = request.args.get('discapacidad', '')

    codigo_sugerido = f"BEN-{random.randint(1000, 9999)}"

    condiciones, discapacidades = obtener_catalogos()

    return render_template('crear_beneficiario.html', tipo_doc=tipo_doc, num_doc=num_doc, municipio_sel=municipio_sel, condicion_sel=condicion_sel, discapacidad_sel=discapacidad_sel, codigo_sugerido=codigo_sugerido, condiciones=condiciones, discapacidades=discapacidades)



@app.route('/beneficiario/<int:id>')

@app.route('/beneficiarios/<int:id>')

@login_required

def ficha_beneficiario(id):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute('CALL sp_obtener_beneficiario_por_id(%s)', (id,))

    b = cursor.fetchone()

    try:

        cursor.nextset()

    except Exception:

        pass

    if not b:

        conn.close()

        flash('Beneficiario no encontrado.', 'danger')

        return redirect(url_for('listar_beneficiarios'))

    cursor.execute('CALL sp_obtener_relaciones_beneficiario(%s)', (id,))

    familia = cursor.fetchall()

    try:

        cursor.nextset()

    except Exception:

        pass

    cursor.execute('CALL sp_obtener_participaciones_beneficiario(%s)', (id,))

    participaciones = cursor.fetchall()

    try:

        cursor.nextset()

    except Exception:

        pass

    cursor.execute('CALL sp_obtener_atenciones_beneficiario(%s)', (id,))

    atenciones = cursor.fetchall()

    try:

        cursor.nextset()

    except Exception:

        pass

    cursor.execute('CALL sp_obtener_seguimientos_beneficiario(%s)', (id,))

    seguimientos = cursor.fetchall()

    try:

        cursor.nextset()

    except Exception:

        pass

    conn.close()

    

    # Calcular IVS con datos completos

    ivs = calcular_ivs(b, num_participaciones=len(participaciones), num_familiares=len(familia))

    

    # Construir Línea de Tiempo Social Cronológica unificada

    timeline = []

    for p in participaciones:

        fec = str(p.get('fecha_vinculacion') or '')[:10] or 'Sin fecha'

        timeline.append({

            'tipo': 'programa',

            'categoria': 'Programa Social',

            'titulo': p.get('programa_nombre') or 'Programa',

            'fecha': fec,

            'detalle': p.get('linea_trabajo') or 'Línea de acompañamiento social',

            'estado': p.get('estado') or 'Activo',

            'badge_bg': '#059669',

            'icon': 'bi-diagram-3-fill'

        })

    for a in atenciones:

        fec = str(a.get('fecha') or a.get('fecha_atencion') or '')[:10] or 'Sin fecha'

        timeline.append({

            'tipo': 'atencion',

            'categoria': 'Atención Integral',

            'titulo': a.get('tipo') or a.get('tipo_atencion') or 'Atención',

            'fecha': fec,

            'detalle': a.get('descripcion') or a.get('observaciones') or 'Atención profesional recibida',

            'estado': a.get('profesional') or 'Equipo Técnico',

            'badge_bg': '#0284c7',

            'icon': 'bi-heart-pulse-fill'

        })

    for s in seguimientos:

        fec = str(s.get('fecha') or s.get('fecha_seguimiento') or '')[:10] or 'Sin fecha'

        timeline.append({

            'tipo': 'seguimiento',

            'categoria': 'Seguimiento Psicosocial',

            'titulo': s.get('tipo') or s.get('tipo_seguimiento') or 'Visita / Evaluación',

            'fecha': fec,

            'detalle': s.get('observaciones') or 'Evaluación periódica de compromisos y bienestar',

            'estado': s.get('estado') or s.get('estado_accion') or 'Registrado',

            'badge_bg': '#d97706',

            'icon': 'bi-journal-check'

        })

    timeline.sort(key=lambda x: str(x['fecha']), reverse=True)



    return render_template('ficha.html', b=b, familia=familia, participaciones=participaciones, atenciones=atenciones, seguimientos=seguimientos, ivs=ivs, timeline=timeline)



@app.route('/beneficiario/<int:id>/editar', methods=['GET', 'POST'])

@app.route('/beneficiarios/<int:id>/editar', methods=['GET', 'POST'])

@login_required

@admin_required

def editar_beneficiario(id):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute('CALL sp_obtener_beneficiario_por_id(%s)', (id,))

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

        invalidar_cache_indicadores()

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

    cursor.execute('CALL sp_eliminar_beneficiario(%s)', (id,))

    conn.close()

    invalidar_cache_indicadores()

    flash('Beneficiario eliminado del sistema correctamente.', 'success')

    return redirect(url_for('listar_beneficiarios'))



@app.route('/programas')

@login_required

def programas():

    q = request.args.get('q', '').strip()

    programa_filtro = request.args.get('programa', '').strip()

    estado_filtro = request.args.get('estado', '').strip()

    try:

        pagina = int(request.args.get('pagina', 1))

    except ValueError:

        pagina = 1

    por_pagina = 20



    conn = get_db_connection()

    cursor = conn.cursor()



    cursor.execute('CALL sp_catalogos_programas()')

    programas_catalogo = [r['programa_nombre'] for r in cursor.fetchall()]



    # Catalogo de estados de participaciones via SP

    cursor.execute('CALL sp_catalogos_seguimientos()')

    _est_rows = cursor.fetchall()

    try:

        cursor.nextset()

    except Exception:

        pass

    estados_catalogo = list({r.get('estado_accion', r.get('estado', '')) for r in _est_rows if r.get('estado_accion') or r.get('estado')})

    if not estados_catalogo:

        estados_catalogo = ['Activo', 'Inactivo', 'Pendiente', 'Completado']



    offset = (pagina - 1) * por_pagina



    # Búsqueda y filtrado ejecutados mediante Stored Procedure en MySQL

    cursor.execute("""

        CALL sp_buscar_participaciones(%s, %s, %s, %s, %s, @p_total)

    """, (q, programa_filtro, estado_filtro, por_pagina, offset))

    participaciones = cursor.fetchall()

    cursor.execute("SELECT @p_total as total")

    total = cursor.fetchone()['total'] or 0

    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)

    pagina = max(1, min(pagina, total_paginas))

    cursor.execute('CALL sp_obtener_lista_simple_beneficiarios()')

    beneficiarios = cursor.fetchall()

    conn.close()

    return render_template('programas.html', participaciones=participaciones, beneficiarios=beneficiarios,

                           q=q, programa_filtro=programa_filtro, estado_filtro=estado_filtro,

                           programas_catalogo=programas_catalogo, estados_catalogo=estados_catalogo,

                           pagina=pagina, total_paginas=total_paginas, total=total)



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

    cursor.execute("""

        INSERT INTO participaciones (beneficiario_id, programa_nombre, linea_trabajo, fecha_vinculacion, estado)

        VALUES (%s, %s, %s, %s, %s)

    """, (beneficiario_id, programa_nombre, linea_trabajo, fecha_vinculacion, estado))

    conn.close()

    invalidar_cache_indicadores()

    flash('Beneficiario vinculado al programa exitosamente.', 'success')

    return redirect(url_for('programas'))



@app.route('/atenciones')

@login_required

def atenciones():

    q = request.args.get('q', '').strip()

    tipo_filtro = request.args.get('tipo', '').strip()

    try:

        pagina = int(request.args.get('pagina', 1))

    except ValueError:

        pagina = 1

    por_pagina = 20



    conn = get_db_connection()

    cursor = conn.cursor()



    cursor.execute('CALL sp_catalogos_atenciones()')

    tipos_catalogo = [r['tipo'] for r in cursor.fetchall()]



    offset = (pagina - 1) * por_pagina



    # Búsqueda y filtrado ejecutados mediante Stored Procedure en MySQL

    cursor.execute("""

        CALL sp_buscar_atenciones(%s, %s, %s, %s, @p_total)

    """, (q, tipo_filtro, por_pagina, offset))

    atenciones = cursor.fetchall()

    cursor.execute("SELECT @p_total as total")

    total = cursor.fetchone()['total'] or 0

    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)

    pagina = max(1, min(pagina, total_paginas))

    cursor.execute('CALL sp_obtener_lista_simple_beneficiarios()')

    beneficiarios = cursor.fetchall()

    conn.close()

    return render_template('atenciones.html', atenciones=atenciones, beneficiarios=beneficiarios,

                           q=q, tipo_filtro=tipo_filtro, tipos_catalogo=tipos_catalogo,

                           pagina=pagina, total_paginas=total_paginas, total=total)



@app.route('/atenciones/crear', methods=['POST'])

@login_required

def crear_atencion_general():

    beneficiario_id = request.form.get('beneficiario_id')

    tipo = request.form.get('tipo', '').strip()

    if tipo == '__otro__' or not tipo:

        tipo = request.form.get('otro_tipo', '').strip() or 'Atención General'

    fecha = request.form.get('fecha')

    responsable = request.form.get('responsable')

    descripcion = request.form.get('descripcion')

    resultado = request.form.get('resultado', '').strip()

    if resultado == '__otro__' or not resultado:

        resultado = request.form.get('otro_resultado', '').strip() or request.form.get('remision', '').strip() or 'Atendido'

    usuario = session.get('usuario', 'Funcionario')



    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        # Invocación de Stored Procedure Transaccional ACID en MySQL

        cursor.execute("""

            CALL sp_registrar_atencion_transaccional(

                %s, %s, %s, %s, %s, %s, %s,

                @p_nuevo_id, @p_estado, @p_msg

            )

        """, (beneficiario_id, tipo, fecha, responsable, descripcion, resultado, usuario))

        cursor.execute("SELECT @p_nuevo_id as nuevo_id, @p_estado as estado, @p_msg as mensaje")

        res_sp = cursor.fetchone()

        conn.close()

        invalidar_cache_indicadores()

        if res_sp and res_sp['estado'] == 'EXITO':

            flash(f"Atención #{res_sp['nuevo_id']} registrada exitosamente vía Stored Procedure transaccional MySQL.", "success")

        else:

            flash(f"Atención registrada: {res_sp.get('mensaje', 'Operación completada')}", "info")

    except Exception as e:

        flash(f"Error al registrar atención vía Stored Procedure: {str(e)}", "danger")



    return redirect(url_for('atenciones'))



@app.route('/seguimientos')

@login_required

def seguimientos():

    q = request.args.get('q', '').strip()

    estado_filtro = request.args.get('estado', '').strip()

    try:

        pagina = int(request.args.get('pagina', 1))

    except ValueError:

        pagina = 1

    por_pagina = 20



    conn = get_db_connection()

    cursor = conn.cursor()



    cursor.execute('CALL sp_catalogos_seguimientos()')

    estados_catalogo = [r['estado_accion'] for r in cursor.fetchall()]



    offset = (pagina - 1) * por_pagina



    # Búsqueda y filtrado ejecutados mediante Stored Procedure en MySQL

    cursor.execute("""

        CALL sp_buscar_seguimientos(%s, %s, %s, %s, @p_total)

    """, (q, estado_filtro, por_pagina, offset))

    seguimientos = cursor.fetchall()

    cursor.execute("SELECT @p_total as total")

    total = cursor.fetchone()['total'] or 0

    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)

    pagina = max(1, min(pagina, total_paginas))

    

    # Obtener todos para el Tablero Kanban (hasta 150 registros activos)

    cursor.execute("""

        SELECT s.*, CONCAT(b.nombres, ' ', IFNULL(b.apellidos, '')) as beneficiario_nombre, b.codigo_interno, b.num_doc, b.municipio

        FROM seguimientos s

        JOIN beneficiarios b ON s.beneficiario_id = b.id

        ORDER BY s.id DESC

        LIMIT 150

    """)

    todos_kanban = cursor.fetchall()

    kanban_pendientes = [s for s in todos_kanban if s.get('estado_accion') == 'Pendiente']

    kanban_en_proceso = [s for s in todos_kanban if s.get('estado_accion') == 'En proceso']

    kanban_finalizadas = [s for s in todos_kanban if s.get('estado_accion') == 'Finalizada']



    cursor.execute('CALL sp_obtener_lista_simple_beneficiarios()')

    beneficiarios = cursor.fetchall()

    conn.close()

    return render_template('seguimientos.html', seguimientos=seguimientos, beneficiarios=beneficiarios,

                           q=q, estado_filtro=estado_filtro, estados_catalogo=estados_catalogo,

                           pagina=pagina, total_paginas=total_paginas, total=total,

                           kanban_pendientes=kanban_pendientes, kanban_en_proceso=kanban_en_proceso, kanban_finalizadas=kanban_finalizadas)



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

    cursor.execute("""

        INSERT INTO seguimientos (beneficiario_id, fecha, avance, proxima_accion, fecha_proximo_contacto, estado_accion)

        VALUES (%s, %s, %s, %s, %s, %s)

    """, (beneficiario_id, fecha, avance, proxima_accion, fecha_proximo_contacto, estado_accion))

    conn.close()

    invalidar_cache_indicadores()

    flash('Seguimiento registrado exitosamente.', 'success')

    return redirect(url_for('seguimientos'))



@app.route('/certificados')

@login_required

def certificados():

    try:

        pagina = int(request.args.get('pagina', 1))

    except ValueError:

        pagina = 1

    por_pagina = 20

    q = request.args.get('q', '').strip()



    conn = get_db_connection()

    cursor = conn.cursor()



    query_base = 'FROM beneficiarios WHERE 1=1'

    params = []

    if q:

        query_base += ' AND (num_doc LIKE %s OR nombres LIKE %s OR apellidos LIKE %s OR codigo_interno LIKE %s)'

        params.extend([f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%'])



    cursor.execute(f'SELECT COUNT(*) as total {query_base}', params)

    total = cursor.fetchone()['total']

    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)

    pagina = max(1, min(pagina, total_paginas))

    offset = (pagina - 1) * por_pagina



    cursor.execute(f'SELECT * {query_base} ORDER BY nombres LIMIT %s OFFSET %s', params + [por_pagina, offset])

    beneficiarios = cursor.fetchall()

    conn.close()

    return render_template('certificados.html', beneficiarios=beneficiarios, q=q,

                           pagina=pagina, total_paginas=total_paginas, total=total)



@app.route('/certificados/imprimir/<int:id>')

@login_required

def imprimir_certificado(id):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute('CALL sp_obtener_beneficiario_por_id(%s)', (id,))

    b = cursor.fetchone()

    try:

        cursor.nextset()

    except Exception:

        pass

    cursor.execute('CALL sp_obtener_participaciones_beneficiario(%s)', (id,))

    participaciones = cursor.fetchall()

    try:

        cursor.nextset()

    except Exception:

        pass

    conn.close()

    if not b:

        flash('Beneficiario no encontrado.', 'danger')

        return redirect(url_for('certificados'))

    

    # Generar Hash Criptográfico SHA-256 de Autenticidad

    semilla = f"{b['codigo_interno']}-{b['num_doc']}-URABA-PAIS-SECURE-2026"

    hash_raw = hashlib.sha256(semilla.encode('utf-8')).hexdigest().upper()

    hash_cert = f"UP26-{hash_raw[0:4]}-{hash_raw[4:8]}-{hash_raw[8:12]}-{hash_raw[12:16]}"

    

    registrar_auditoria('EMISION_CERTIFICADO', f"Emisión de certificado oficial con folio {b['codigo_interno']} para {b['nombres']} {b['apellidos']}", 'INFO')

    

    return render_template('certificado_documento.html', b=b, participaciones=participaciones, hash_cert=hash_cert)



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

        'Indicador;Valor',

        f'Beneficiarios únicos;{indicadores["total_beneficiarios"]}',

        f'Participaciones registradas;{indicadores["total_participaciones"]}',

        f'Atenciones y ayudas entregadas;{indicadores["total_atenciones"]}',

        f'Seguimientos pendientes;{indicadores["seguimientos_pendientes"]}',

        '',

        'Programa Social;Participaciones'

    ]

    for p in indicadores.get('programas_resumen', []):

        nombre = str(p.get('programa_nombre', '')).replace(';', ',')

        lineas.append(f'"{nombre}";{p.get("cantidad", 0)}')

    lineas.append('')

    lineas.append('Estado de Participación;Cantidad')

    for e in indicadores.get('estados_resumen', []):

        lineas.append(f'"{e.get("estado", "").capitalize()}";{e.get("cantidad", 0)}')

    lineas.append('')

    lineas.append('Municipio;Beneficiarios')

    for m in indicadores.get('municipios_resumen', []):

        lineas.append(f'"{m.get("municipio", "")}";{m.get("cantidad", 0)}')



    output = '\ufeff' + '\r\n'.join(lineas)

    return Response(

        output,

        mimetype='text/csv; charset=utf-8',

        headers={

            'Content-Disposition': 'attachment; filename=reporte_ejecutivo_uraba_2026.csv',

            'Content-Type': 'text/csv; charset=utf-8'

        }

    )



@app.route('/reportes/exportar-beneficiarios')

@login_required

def exportar_beneficiarios_csv():

    q = request.args.get('q', '').strip()

    municipio_filtro = request.args.get('municipio', '').strip()

    sexo_filtro = request.args.get('sexo', '').strip()

    condicion_filtro = request.args.get('condicion', '').strip()



    query = '''

        SELECT codigo_interno, tipo_doc, num_doc, nombres, apellidos, fecha_nacimiento, sexo, telefono, municipio, condicion_poblacional, discapacidad,

               IF(habeas_data = 1, 'Autorizado', 'No') as habeas_data

        FROM beneficiarios

        WHERE 1=1

    '''

    params = []

    if q:

        query += ' AND (num_doc LIKE %s OR nombres LIKE %s OR apellidos LIKE %s OR codigo_interno LIKE %s)'

        params.extend([f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%'])

    if municipio_filtro:

        query += ' AND TRIM(municipio) = TRIM(%s)'

        params.append(municipio_filtro)

    if sexo_filtro:

        query += ' AND TRIM(sexo) = TRIM(%s)'

        params.append(sexo_filtro)

    if condicion_filtro:

        query += ' AND TRIM(condicion_poblacional) = TRIM(%s)'

        params.append(condicion_filtro)

    query += ' ORDER BY id DESC'



    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute(query, params)

    filas = cursor.fetchall()

    conn.close()



    registrar_auditoria('EXPORTACION_DATOS', f"Descarga de matriz de beneficiarios ({len(filas)} filas) conforme a Ley 1581 de 2012 (Habeas Data)", 'SEGURIDAD')

    columnas = ['Código Interno', 'Tipo Documento', 'Número Documento', 'Nombres', 'Apellidos', 'Fecha Nacimiento', 'Sexo', 'Teléfono', 'Municipio', 'Condición Poblacional', 'Discapacidad', 'Puntaje IVS (0-100)', 'Nivel Prioridad Social', 'Habeas Data']

    csv_rows = [';'.join(f'"{col}"' for col in columnas)]

    for f in filas:

        ivs_res = calcular_ivs(f)

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

            f"{ivs_res['score']} pts",

            ivs_res['nivel'],

            'Autorizado (Ley 1581)' if f.get('habeas_data') else 'No registrado'

        ]

        csv_rows.append(';'.join(f'"{str(val).replace(chr(34), chr(39))}"' for val in row))



    output = '\ufeff' + '\r\n'.join(csv_rows)

    filename = 'matriz_beneficiarios_filtrados.csv' if (q or municipio_filtro or sexo_filtro or condicion_filtro) else 'matriz_general_beneficiarios_uraba.csv'

    return Response(

        output,

        mimetype='text/csv; charset=utf-8',

        headers={

            'Content-Disposition': f'attachment; filename={filename}',

            'Content-Type': 'text/csv; charset=utf-8'

        }

    )



@app.route('/beneficiarios/<int:id>/familiar', methods=['POST'])

@app.route('/beneficiario/<int:id>/familiar', methods=['POST'])

@login_required

def agregar_familiar(id):

    nombre_completo = request.form.get('nombre_completo')

    parentesco = request.form.get('parentesco')

    edad = request.form.get('edad') or None

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute('CALL sp_crear_familiar(%s, %s, %s, %s)', (id, nombre_completo, parentesco, edad))

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

    cursor.execute('CALL sp_crear_participacion(%s, %s, %s, %s, %s)', (id, programa_nombre, linea_trabajo, fecha_vinculacion, estado))

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

    usuario_reg = session.get('usuario', 'sistema')

    cursor.execute('CALL sp_registrar_atencion_transaccional(%s, %s, %s, %s, %s, %s, @p_id)',

                   (id, tipo, fecha, descripcion, responsable, resultado))

    try:

        cursor.nextset()

    except Exception:

        pass

    conn.commit()

    conn.close()

    redirect_to = request.args.get('redirect_to') or request.form.get('redirect_to')

    flash('¡Atención social registrada exitosamente y caso atendido!', 'success')

    if redirect_to == 'alertas':

        return redirect(url_for('alertas'))

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

    usuario_reg = session.get('usuario', 'sistema')

    cursor.execute('CALL sp_crear_seguimiento(%s, %s, %s, %s, %s, %s)',

                   (id, fecha, avance, proxima_accion, fecha_proximo_contacto, estado_accion))

    try:

        cursor.nextset()

    except Exception:

        pass

    conn.commit()

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



# â”€â”€â”€ Eliminar registros de atenciones, seguimientos, participaciones y familiares â”€



@app.route('/atenciones/<int:id>/eliminar', methods=['POST'])

@login_required

@admin_required

def eliminar_atencion(id):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute('CALL sp_eliminar_atencion(%s)', (id,))

    conn.close()

    invalidar_cache_indicadores()

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

    cursor.execute('CALL sp_eliminar_seguimiento(%s)', (id,))

    conn.close()

    invalidar_cache_indicadores()

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

    cursor.execute('CALL sp_eliminar_participacion(%s)', (id,))

    conn.close()

    invalidar_cache_indicadores()

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

    cursor.execute('CALL sp_eliminar_familiar(%s, @p_ben_id)', (id,))

    cursor.execute('SELECT @p_ben_id as beneficiario_id')

    row = cursor.fetchone()

    beneficiario_id = row['beneficiario_id'] if row else None

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

    # Búsqueda global Spotlight ejecutada mediante Stored Procedure en MySQL

    cursor.callproc('sp_busqueda_global_spotlight', [q, 8])

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

            'subtitulo': f"Doc: {b['tipo_doc']} {b['num_doc']} Â· {b['municipio'] or 'Urabá'}",

            'tipo': 'Beneficiario',

            'url': url_for('ficha_beneficiario', id=b['id']),

            'icon': 'bi-person-badge-fill'

        })



    return jsonify({'resultados': resultados})



@app.route('/usuarios')

@login_required

@admin_required

def listar_usuarios():

    try:

        pagina = int(request.args.get('pagina', 1))

    except ValueError:

        pagina = 1

    por_pagina = 20



    conn = get_db_connection()

    cursor = conn.cursor()

    offset = (pagina - 1) * por_pagina

    cursor.execute('CALL sp_listar_usuarios(%s, %s, @p_total)', (por_pagina, offset))

    usuarios = cursor.fetchall()

    cursor.execute('SELECT @p_total as total')

    total = cursor.fetchone()['total'] or 0

    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)

    pagina = max(1, min(pagina, total_paginas))

    conn.close()

    return render_template('usuarios.html', usuarios=usuarios,

                           pagina=pagina, total_paginas=total_paginas, total=total)



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

    if len(password) < 6:

        flash('Por seguridad, la contraseña debe tener al menos 6 caracteres.', 'warning')

        return redirect(url_for('listar_usuarios'))

    conn = get_db_connection()

    cursor = conn.cursor()

    try:

        cursor.execute(

            'CALL sp_crear_usuario(%s, %s, %s, %s, @p_nuevo_id)',

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

    cursor.execute('CALL sp_eliminar_usuario(%s)', (id,))

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

    cursor.execute('CALL sp_cambiar_rol_usuario(%s, %s)', (id, nuevo_rol))

    conn.close()

    flash('Rol actualizado correctamente.', 'success')

    return redirect(url_for('listar_usuarios'))









@app.route('/verificar')

@app.route('/verificar/<codigo>')

def verificar_certificado_publico(codigo=None):

    """Portal público de validación de autenticidad de certificaciones con código QR."""

    if not codigo:

        codigo = request.args.get('codigo', '').strip()

    

    if not codigo:

        return render_template('verificar_certificado.html', b=None, participaciones=[], codigo_buscado='', hash_cert='', consultado=False)

    

    codigo = codigo.strip().upper()

    conn = get_db_connection()

    cur = conn.cursor()

    cur.execute('''

        SELECT * FROM beneficiarios 

        WHERE UPPER(codigo_interno) = %s OR UPPER(num_doc) = %s 

        LIMIT 1

    ''', (codigo, codigo))

    b = cur.fetchone()

    participaciones = []

    hash_cert = ''

    if b:

        cur.execute('SELECT * FROM participaciones WHERE beneficiario_id = %s ORDER BY id DESC', (b['id'],))

        participaciones = cur.fetchall()

        semilla = f"{b['codigo_interno']}-{b['num_doc']}-URABA-PAIS-SECURE-2026"

        hash_raw = hashlib.sha256(semilla.encode('utf-8')).hexdigest().upper()

        hash_cert = f"UP26-{hash_raw[0:4]}-{hash_raw[4:8]}-{hash_raw[8:12]}-{hash_raw[12:16]}"

        

        registrar_auditoria('VERIFICACION_QR', f"Consulta pública de certificado folio {b['codigo_interno']} ({b['nombres']} {b['apellidos']})", 'INFO', usuario='Público')

    conn.close()

    

    return render_template(

        'verificar_certificado.html',

        b=b,

        participaciones=participaciones,

        codigo_buscado=codigo,

        hash_cert=hash_cert,

        consultado=True

    )



@app.route('/auditoria')

@login_required

@admin_required

def auditoria():

    """Bitácora de Auditoría y Trazabilidad Forense (Ley 1581 / Habeas Data & ISO 27001)."""

    q = request.args.get('q', '').strip()

    nivel_filtro = request.args.get('nivel', '').strip()

    accion_filtro = request.args.get('accion', '').strip()

    try:

        pagina = int(request.args.get('pagina', 1))

    except ValueError:

        pagina = 1

    por_pagina = 20



    conn = get_db_connection()

    cur = conn.cursor()



    offset = (pagina - 1) * por_pagina



    # Búsqueda y filtrado de auditoría forense mediante Stored Procedure en MySQL

    cur.execute("""

        CALL sp_buscar_auditoria(%s, %s, %s, %s, %s, @p_total)

    """, (q, nivel_filtro, accion_filtro, por_pagina, offset))

    registros = cur.fetchall()

    cur.execute("SELECT @p_total as total")

    total = cur.fetchone()['total'] or 0

    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)

    pagina = max(1, min(pagina, total_paginas))



    # Métricas de auditoría

    cur.execute('SELECT COUNT(*) as total_eventos FROM auditoria')

    total_eventos = cur.fetchone()['total_eventos']

    cur.execute("SELECT COUNT(*) as total_seguridad FROM auditoria WHERE nivel = 'SEGURIDAD' OR nivel = 'WARNING'")

    total_seguridad = cur.fetchone()['total_seguridad']

    cur.execute("SELECT COUNT(DISTINCT ip_origen) as total_ips FROM auditoria")

    total_ips = cur.fetchone()['total_ips']



    conn.close()



    return render_template(

        'auditoria.html',

        registros=registros,

        q=q,

        nivel_filtro=nivel_filtro,

        accion_filtro=accion_filtro,

        pagina=pagina,

        total_paginas=total_paginas,

        total=total,

        total_eventos=total_eventos,

        total_seguridad=total_seguridad,

        total_ips=total_ips

    )





# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# SISTEMA DE ALERTAS TEMPRANAS (SAT), KANBAN API & IMPORTADOR CSV

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•



@app.context_processor

def inject_global_notifications():

    """Inyecta contador de alertas y notificaciones activas en todas las vistas."""

    if 'usuario' in session:

        try:

            conn = get_db_connection()

            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) as c FROM seguimientos WHERE estado_accion = 'Pendiente'")

            segs_pend = cur.fetchone()['c']

            cur.execute("SELECT COUNT(*) as c FROM beneficiarios WHERE id NOT IN (SELECT DISTINCT beneficiario_id FROM participaciones)")

            sin_prog = cur.fetchone()['c']

            conn.close()

            total = segs_pend + (1 if sin_prog > 0 else 0)

            return {

                'notif_count': min(total, 99),

                'notif_segs_pendientes': segs_pend,

                'notif_sin_programa': sin_prog

            }

        except Exception:

            pass

    return {'notif_count': 0, 'notif_segs_pendientes': 0, 'notif_sin_programa': 0}



def obtener_alertas_sistema():

    """Analiza la base de datos para detectar casos en riesgo, falta de atención o vencimientos."""

    conn = get_db_connection()

    cur = conn.cursor()

    cur.execute("SELECT id, codigo_interno, num_doc, nombres, apellidos, municipio, condicion_poblacional, discapacidad, fecha_nacimiento, telefono FROM beneficiarios")

    todos = cur.fetchall()

    

    cur.execute("SELECT beneficiario_id, COUNT(*) as c FROM participaciones GROUP BY beneficiario_id")

    part_map = {r['beneficiario_id']: r['c'] for r in cur.fetchall()}

    

    cur.execute("SELECT beneficiario_id, MAX(fecha) as ult FROM atenciones GROUP BY beneficiario_id")

    at_map = {r['beneficiario_id']: r['ult'] for r in cur.fetchall()}

    

    hoy = date.today()

    alertas_criticas = []

    sin_cobertura = []

    

    for b in todos:

        bid = b['id']

        ivs = calcular_ivs(b)

        n_part = part_map.get(bid, 0)

        ult_at = at_map.get(bid)

        

        dias = 999

        if ult_at:

            try:

                f_at = datetime.strptime(str(ult_at)[:10], '%Y-%m-%d').date()

                dias = (hoy - f_at).days

            except Exception:

                dias = 45

        

        if n_part == 0:

            sin_cobertura.append({

                'id': bid,

                'codigo': b['codigo_interno'],

                'nombre': f"{b['nombres']} {b['apellidos']}",

                'num_doc': b['num_doc'],

                'municipio': b.get('municipio') or 'Urabá',

                'ivs': ivs,

                'telefono': b.get('telefono') or 'Sin teléfono'

            })

            

        if ivs['score'] >= 50 and (dias > 30 or n_part == 0):

            alertas_criticas.append({

                'id': bid,

                'codigo': b['codigo_interno'],

                'nombre': f"{b['nombres']} {b['apellidos']}",

                'num_doc': b['num_doc'],

                'municipio': b.get('municipio') or 'Urabá',

                'ivs': ivs,

                'dias_sin_atencion': dias if dias < 900 else 'Sin registro',

                'programas': n_part,

                'telefono': b.get('telefono') or 'Sin teléfono'

            })

            

    cur.execute("""

        SELECT s.*, CONCAT(b.nombres, ' ', IFNULL(b.apellidos, '')) as beneficiario_nombre, b.codigo_interno, b.num_doc, b.municipio, b.telefono

        FROM seguimientos s

        JOIN beneficiarios b ON s.beneficiario_id = b.id

        WHERE s.estado_accion = 'Pendiente'

        ORDER BY s.id DESC

    """)

    segs_pendientes = cur.fetchall()

    conn.close()

    

    kpis = {

        'total_criticas': len(alertas_criticas),

        'total_seguimientos': len(segs_pendientes),

        'total_sin_cobertura': len(sin_cobertura),

        'tasa_urgencia': round((len(alertas_criticas) / max(len(todos), 1)) * 100, 1)

    }

    

    return {

        'criticas': alertas_criticas,

        'seguimientos': segs_pendientes,

        'sin_cobertura': sin_cobertura,

        'kpis': kpis

    }



@app.route('/alertas')

@login_required

def alertas():

    """Centro de Alertas Tempranas y Semáforo de Riesgo Territorial."""

    data = obtener_alertas_sistema()

    registrar_auditoria('CONSULTA_ALERTAS', 'Acceso al módulo de Alertas Tempranas y Semáforo de Riesgo Territorial', 'INFO')

    return render_template('alertas.html', 

                           criticas=data['criticas'], 

                           seguimientos=data['seguimientos'], 

                           sin_cobertura=data['sin_cobertura'], 

                           kpis=data['kpis'])



@app.route('/api/seguimiento/<int:id>/estado', methods=['POST'])

@login_required

def api_mover_seguimiento(id):

    """Actualiza el estado de un seguimiento desde el Tablero Kanban vía AJAX."""

    try:

        data = request.get_json(silent=True) or request.form

        nuevo_estado = (data.get('estado') or '').strip()

        estados_validos = ['Pendiente', 'En proceso', 'Finalizada']

        if nuevo_estado not in estados_validos:

            return jsonify({'success': False, 'error': 'Estado no válido'}), 400

            

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute("CALL sp_actualizar_estado_seguimiento(%s, %s)", (id, nuevo_estado))

        conn.commit()

        conn.close()

        

        invalidar_cache_indicadores()

        registrar_auditoria('ACTUALIZAR_SEGUIMIENTO', f"Seguimiento #{id} cambiado a '{nuevo_estado}' desde Tablero Kanban", 'INFO')

        return jsonify({'success': True, 'id': id, 'nuevo_estado': nuevo_estado})

    except Exception as e:

        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/beneficiarios/plantilla-csv')

@login_required

def descargar_plantilla_csv():

    """Descarga de plantilla CSV oficial con estructura y ejemplos para importación masiva."""

    columnas = [

        'Tipo Documento', 'Numero Documento', 'Nombres', 'Apellidos',

        'Fecha Nacimiento', 'Sexo', 'Telefono', 'Municipio',

        'Condicion Poblacional', 'Discapacidad', 'Habeas Data'

    ]

    ejemplos = [

        ['CC', '1045987112', 'Carlos Mario', 'Palacios Urrutia', '1988-04-15', 'Masculino', '3124567890', 'Apartadó', 'Víctima del conflicto', 'Ninguna', '1'],

        ['CC', '1038472910', 'Yurleis Tatiana', 'Moreno Mosquera', '1995-11-22', 'Femenino', '3145678901', 'Turbo', 'Madre cabeza de hogar', 'Ninguna', '1'],

        ['TI', '1089234567', 'Brayan David', 'Henao Restrepo', '2008-08-05', 'Masculino', '3206789012', 'Carepa', 'Población general', 'Visual', '1']

    ]

    filas = [';'.join(f'"{c}"' for c in columnas)]

    for ej in ejemplos:

        filas.append(';'.join(f'"{v}"' for v in ej))

    output = '\ufeff' + '\r\n'.join(filas)

    return Response(

        output,

        mimetype='text/csv; charset=utf-8',

        headers={

            'Content-Disposition': 'attachment; filename=plantilla_importacion_uraba_pais.csv',

            'Content-Type': 'text/csv; charset=utf-8'

        }

    )



@app.route('/beneficiarios/importar', methods=['GET', 'POST'])

@login_required

def importar_beneficiarios():

    """Módulo de carga e importación masiva de beneficiarios por archivo CSV."""

    if request.method == 'GET':

        return render_template('importar_beneficiarios.html')

        

    archivo = request.files.get('archivo_csv')

    if not archivo or not archivo.filename:

        flash('Por favor seleccione un archivo CSV para importar.', 'warning')

        return redirect(url_for('importar_beneficiarios'))

        

    if not archivo.filename.lower().endswith(('.csv', '.txt')):

        flash('El archivo debe tener extensión .csv', 'danger')

        return redirect(url_for('importar_beneficiarios'))

        

    try:

        raw_bytes = archivo.read()

        try:

            texto = raw_bytes.decode('utf-8-sig')

        except UnicodeDecodeError:

            try:

                texto = raw_bytes.decode('utf-8')

            except UnicodeDecodeError:

                texto = raw_bytes.decode('latin-1')

                

        import csv

        import io

        delimitador = ';' if ';' in texto.splitlines()[0] else ','

        lector = csv.reader(io.StringIO(texto), delimiter=delimitador)

        filas = list(lector)

        

        if len(filas) < 2:

            flash('El archivo CSV está vacío o solo contiene la cabecera.', 'warning')

            return redirect(url_for('importar_beneficiarios'))

            

        registros_data = filas[1:]

        conn = get_db_connection()

        cur = conn.cursor()

        

        cur.execute("SELECT num_doc FROM beneficiarios WHERE num_doc IS NOT NULL AND num_doc != ''")

        docs_existentes = set(r['num_doc'].strip() for r in cur.fetchall())

        

        cur.execute("SELECT codigo_interno FROM beneficiarios WHERE codigo_interno IS NOT NULL")

        cods_existentes = set(r['codigo_interno'].strip() for r in cur.fetchall())

        

        importados = 0

        omitidos_duplicados = 0

        errores = 0

        

        for fila in registros_data:

            if not any(campo.strip() for campo in fila):

                continue

            if len(fila) < 3:

                errores += 1

                continue

                

            tipo_doc = fila[0].strip() or 'CC'

            num_doc = fila[1].strip()

            nombres = fila[2].strip()

            apellidos = fila[3].strip() if len(fila) > 3 else ''

            fecha_nac = fila[4].strip() if len(fila) > 4 else None

            sexo = fila[5].strip() if len(fila) > 5 else 'Otro'

            telefono = fila[6].strip() if len(fila) > 6 else ''

            municipio = fila[7].strip() if len(fila) > 7 else 'Apartadó'

            condicion = fila[8].strip() if len(fila) > 8 else 'Población general'

            discapacidad = fila[9].strip() if len(fila) > 9 else 'Ninguna'

            habeas = 1 if len(fila) > 10 and fila[10].strip() in ['1', 'true', 'si', 'sí', 'TRUE'] else 1

            

            if not num_doc or not nombres:

                errores += 1

                continue

                

            if num_doc in docs_existentes:

                omitidos_duplicados += 1

                continue

                

            while True:

                num_rand = random.randint(1000, 9999)

                nuevo_cod = f"BEN-{num_rand}"

                if nuevo_cod not in cods_existentes:

                    cods_existentes.add(nuevo_cod)

                    break

                    

            cur.execute("""

                INSERT INTO beneficiarios (

                    codigo_interno, tipo_doc, num_doc, nombres, apellidos,

                    fecha_nacimiento, sexo, telefono, municipio,

                    condicion_poblacional, discapacidad, habeas_data

                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

            """, (

                nuevo_cod, tipo_doc, num_doc, nombres, apellidos,

                fecha_nac or None, sexo, telefono, municipio,

                condicion, discapacidad, habeas

            ))

            docs_existentes.add(num_doc)

            importados += 1

            

        conn.commit()

        conn.close()

        

        invalidar_cache_indicadores()

        registrar_auditoria('IMPORTACION_MASIVA', f"Importación masiva: {importados} nuevos beneficiarios registrados ({omitidos_duplicados} omitidos por duplicado)", 'SEGURIDAD')

        

        flash(f'¡Importación exitosa! Se ingresaron {importados} beneficiarios al padrón oficial. ({omitidos_duplicados} omitidos por documento ya existente).', 'success')

        return redirect(url_for('listar_beneficiarios'))

        

    except Exception as e:

        flash(f'Error al procesar el archivo CSV: {str(e)}', 'danger')

        return redirect(url_for('importar_beneficiarios'))









# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# PROCEDIMIENTOS ALMACENADOS (MYSQL STORED PROCEDURES)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•



@app.route('/stored-procedures')

@login_required

def stored_procedures_view():

    conn = get_db_connection()

    cur = conn.cursor()



    cur.execute("""

        SELECT 

            ROUTINE_NAME as nombre,

            ROUTINE_TYPE as tipo,

            DEFINER as definer,

            CREATED as creado,

            LAST_ALTERED as modificado,

            SECURITY_TYPE as seguridad

        FROM information_schema.ROUTINES

        WHERE ROUTINE_SCHEMA = DATABASE()

        ORDER BY ROUTINE_NAME

    """)

    procedures_raw = cur.fetchall()



    meta_procs = {

        # --- Procedimientos de Analítica & Transaccionales ---

        'sp_resumen_indicadores_subregion': {

            'titulo': 'Cálculo Consolidado de Indicadores Subregionales',

            'categoria': 'Analítica & Agregación',

            'icono': 'bi-bar-chart-steps',

            'color': 'primary',

            'descripcion': 'Calcula y consolida en una sola operación de base de datos los KPIs de beneficiarios, participaciones, atenciones y seguimientos de los 11 municipios de Urabá.',

            'parametros': 'Sin parámetros (Ejecución directa en servidor)',

            'retorno': 'Dataset tabular con métricas consolidadas',

            'justificacion': 'Reduce la latencia de red de múltiples consultas HTTP independientes a 1 sola invocación en el motor relacional MySQL.'

        },

        'sp_registrar_atencion_transaccional': {

            'titulo': 'Registro Transaccional ACID con Auditoría Atómica',

            'categoria': 'Transaccional & Seguridad',

            'icono': 'bi-shield-lock-fill',

            'color': 'success',

            'descripcion': 'Ejecuta una transacción ACID atómica que inserta la atención social y genera automáticamente el registro inmutable en la bitácora de auditoría. Si ocurre un fallo, ejecuta un ROLLBACK de seguridad.',

            'parametros': 'IN beneficiario_id, tipo, fecha, responsable, descripcion, remision, usuario | OUT nuevo_id, codigo_estado, mensaje',

            'retorno': 'ID generado, código de estado (EXITO / ERROR_SQL) y mensaje',

            'justificacion': 'Cumple con el estándar de atomicidad e integridad referencial ACID exigido en sistemas empresariales de bases de datos.'

        },

        'sp_ficha_resumen_beneficiario': {

            'titulo': 'Consulta Optimizada Ficha 360°',

            'categoria': 'Consultas Relacionales',

            'icono': 'bi-person-badge-fill',

            'color': 'info',

            'descripcion': 'Retorna el perfil consolidado del beneficiario junto con conteos relacionales de participaciones en programas y atenciones prestadas.',

            'parametros': 'IN p_beneficiario_id (INT)',

            'retorno': 'Fila única con datos demográficos y conteos consolidados',

            'justificacion': 'Elimina el problema de consultas N+1 en el backend al realizar la agregación directamente en el motor relacional.'

        },

        'sp_alertas_prioritarias_ivs': {

            'titulo': 'Filtro del Sistema de Alertas Tempranas (SAT)',

            'categoria': 'Focalización Social',

            'icono': 'bi-exclamation-triangle-fill',

            'color': 'danger',

            'descripcion': 'Filtra en el motor MySQL los casos más urgentes de vulnerabilidad (víctimas de conflicto, personas con discapacidad y hogares sin atención previa) en Urabá.',

            'parametros': 'IN p_municipio (VARCHAR o NULL para todos)',

            'retorno': 'Lista priorizada de hasta 50 beneficiarios de máxima atención',

            'justificacion': 'Aplica indexación y ordenamiento condicional server-side para optimizar el tiempo de respuesta del sistema SAT.'

        },



        # --- Procedimientos de Búsqueda y Filtrado en la App ---

        'sp_buscar_beneficiarios': {

            'titulo': 'Buscador y Filtros Avanzados de Beneficiarios',

            'categoria': 'Buscador & Filtros',

            'icono': 'bi-people-fill',

            'color': 'primary',

            'descripcion': 'Motor de búsqueda multi-criterio para beneficiarios (documento, nombres, apellidos, código) combinado con filtros de municipio, sexo y condición poblacional con paginación server-side.',

            'parametros': 'IN q, municipio, sexo, condicion, limit, offset | OUT total',

            'retorno': 'Página de beneficiarios y conteo total de coincidencias',

            'justificacion': 'Traslada el cómputo de búsqueda y paginación directamente al motor SQL, eliminando transferencia innecesaria de datos.'

        },

        'sp_buscar_atenciones': {

            'titulo': 'Buscador y Filtros de Atenciones y Ayudas',

            'categoria': 'Buscador & Filtros',

            'icono': 'bi-heart-pulse-fill',

            'color': 'success',

            'descripcion': 'Búsqueda de atenciones por beneficiario, funcionario, descripción o resultado con filtro por tipo de atención y paginación en MySQL.',

            'parametros': 'IN q, tipo, limit, offset | OUT total',

            'retorno': 'Página de atenciones relacionadas con beneficiario y total',

            'justificacion': 'Realiza el JOIN relacional entre atenciones y beneficiarios en el motor con cálculo de paginador.'

        },

        'sp_buscar_seguimientos': {

            'titulo': 'Buscador y Filtros de Seguimientos',

            'categoria': 'Buscador & Filtros',

            'icono': 'bi-clock-history',

            'color': 'warning',

            'descripcion': 'Búsqueda de compromisos y tareas de seguimiento por beneficiario, avance o próxima acción con filtro por estado (Pendiente, En proceso, Finalizada).',

            'parametros': 'IN q, estado, limit, offset | OUT total',

            'retorno': 'Página de seguimientos y conteo total',

            'justificacion': 'Optimiza la vista Kanban y la tabla de seguimientos delegando el filtro de estados al optimizador de consultas MySQL.'

        },

        'sp_buscar_participaciones': {

            'titulo': 'Buscador y Filtros de Participaciones en Programas',

            'categoria': 'Buscador & Filtros',

            'icono': 'bi-diagram-3-fill',

            'color': 'info',

            'descripcion': 'Búsqueda en programas sociales por beneficiario, línea de trabajo o nombre del programa con filtros combinados y paginación.',

            'parametros': 'IN q, programa, estado, limit, offset | OUT total',

            'retorno': 'Página de vinculaciones a programas sociales',

            'justificacion': 'Indexa las vinculaciones territoriales y previene escaneos completos de tablas (full table scan).'

        },

        'sp_buscar_auditoria': {

            'titulo': 'Buscador y Filtros de Auditoría Forense (ISO 27001)',

            'categoria': 'Buscador & Filtros',

            'icono': 'bi-shield-check',

            'color': 'danger',

            'descripcion': 'Búsqueda en la bitácora de trazabilidad por usuario, detalle, IP o acción con filtro por nivel de severidad (INFO, ALERTA, CRITICO).',

            'parametros': 'IN q, nivel, accion, limit, offset | OUT total',

            'retorno': 'Página de eventos de auditoría y total de registros',

            'justificacion': 'Garantiza búsquedas eficientes en registros forenses de gran volumen conforme a la Ley de Habeas Data.'

        },

        'sp_busqueda_global_spotlight': {

            'titulo': 'Búsqueda Global Rápida (Spotlight / Topbar)',

            'categoria': 'Buscador Global',

            'icono': 'bi-search',

            'color': 'primary',

            'descripcion': 'Búsqueda instantánea en tiempo real invocada por la barra superior y tecla rápida Ctrl+K para localizar beneficiarios y expedientes.',

            'parametros': 'IN q, limit',

            'retorno': 'Lista rápida de hasta 8 coincidencias con enlace directo a la ficha',

            'justificacion': 'Responde en menos de 5 ms para autocompletado en tiempo real en la barra de navegación.'

        }

    }



    lista_detallada = []

    for p in procedures_raw:

        nom = p['nombre']

        info = meta_procs.get(nom, {

            'titulo': nom,

            'categoria': 'Procedimiento Almacenado',

            'icono': 'bi-gear-fill',

            'color': 'secondary',

            'descripcion': 'Procedimiento almacenado en uraba_pais_db',

            'parametros': 'Consultar DDL',

            'retorno': 'Dataset / Valores OUT',

            'justificacion': 'Lógica compilada en MySQL'

        })



        try:

            cur.execute(f"SHOW CREATE PROCEDURE `{nom}`")

            row_ddl = cur.fetchone()

            ddl = row_ddl.get('Create Procedure') or list(row_ddl.values())[2]

        except Exception:

            ddl = "-- No disponible"



        lista_detallada.append({**p, **info, 'ddl': ddl})



    conn.close()

    return render_template('stored_procedures.html', procedures=lista_detallada, total_sp=len(lista_detallada))



@app.route('/api/stored-procedures/ejecutar/<nombre>', methods=['POST'])

@login_required

def api_ejecutar_sp(nombre):

    nombre = nombre.strip()

    permitidos = [

        'sp_resumen_indicadores_subregion',

        'sp_registrar_atencion_transaccional',

        'sp_ficha_resumen_beneficiario',

        'sp_alertas_prioritarias_ivs',

        'sp_buscar_beneficiarios',

        'sp_buscar_atenciones',

        'sp_buscar_seguimientos',

        'sp_buscar_participaciones',

        'sp_buscar_auditoria',

        'sp_busqueda_global_spotlight'

    ]

    if nombre not in permitidos:

        return jsonify({'status': 'error', 'mensaje': 'Procedimiento no autorizado o inexistente'}), 400



    t0 = time.time()

    try:

        conn = get_db_connection()

        cur = conn.cursor()



        resultado = []

        if nombre == 'sp_resumen_indicadores_subregion':

            cur.callproc('sp_resumen_indicadores_subregion')

            resultado = cur.fetchall()

        elif nombre == 'sp_ficha_resumen_beneficiario':

            cur.execute("SELECT id FROM beneficiarios LIMIT 1")

            b_row = cur.fetchone()

            b_id = b_row['id'] if b_row else 1

            cur.callproc('sp_ficha_resumen_beneficiario', [b_id])

            resultado = cur.fetchall()

        elif nombre == 'sp_alertas_prioritarias_ivs':

            cur.callproc('sp_alertas_prioritarias_ivs', ['Apartadó'])

            resultado = cur.fetchall()

        elif nombre == 'sp_registrar_atencion_transaccional':

            cur.execute("SELECT id FROM beneficiarios LIMIT 1")

            b_row = cur.fetchone()

            b_id = b_row['id'] if b_row else 1

            cur.execute("""

                CALL sp_registrar_atencion_transaccional(

                    %s, 'Orientación Psicosocial (Consola SP)', CURDATE(), 'Funcionario Evaluador SP',

                    'Atención de prueba ejecutada desde la consola interactiva de Stored Procedures',

                    'Atendido exitosamente', %s,

                    @p_id, @p_estado, @p_msg

                )

            """, (b_id, session.get('usuario', 'admin')))

            cur.execute("SELECT @p_id as nuevo_id, @p_estado as estado, @p_msg as mensaje")

            resultado = [cur.fetchone()]

        elif nombre == 'sp_buscar_beneficiarios':

            cur.execute("CALL sp_buscar_beneficiarios(%s, %s, %s, %s, %s, %s, @p_total)", ('', '', '', '', 5, 0))

            resultado = cur.fetchall()

        elif nombre == 'sp_buscar_atenciones':

            cur.execute("CALL sp_buscar_atenciones(%s, %s, %s, %s, @p_total)", ('', '', 5, 0))

            resultado = cur.fetchall()

        elif nombre == 'sp_buscar_seguimientos':

            cur.execute("CALL sp_buscar_seguimientos(%s, %s, %s, %s, @p_total)", ('', '', 5, 0))

            resultado = cur.fetchall()

        elif nombre == 'sp_buscar_participaciones':

            cur.execute("CALL sp_buscar_participaciones(%s, %s, %s, %s, %s, @p_total)", ('', '', '', 5, 0))

            resultado = cur.fetchall()

        elif nombre == 'sp_buscar_auditoria':

            cur.execute("CALL sp_buscar_auditoria(%s, %s, %s, %s, %s, @p_total)", ('', '', '', 5, 0))

            resultado = cur.fetchall()

        elif nombre == 'sp_busqueda_global_spotlight':

            cur.callproc('sp_busqueda_global_spotlight', ['Apartadó', 5])

            resultado = cur.fetchall()



        elapsed_ms = round((time.time() - t0) * 1000, 2)

        conn.close()

        return jsonify({

            'status': 'ok',

            'procedimiento': nombre,

            'tiempo_ms': elapsed_ms,

            'filas_retornadas': len(resultado) if resultado else 0,

            'datos': resultado

        })

    except Exception as e:

        return jsonify({'status': 'error', 'mensaje': str(e)}), 500



@app.route('/stored-procedures/reinstalar', methods=['POST'])

@login_required

@admin_required

def reinstalar_stored_procedures_route():

    try:

        from scripts.instalar_procedures import instalar_todos_los_procedures

        instalar_todos_los_procedures()

        flash('Los 10 Stored Procedures han sido reinstalados y verificados en MySQL correctamente.', 'success')

    except Exception as e:

        flash(f'Error al reinstalar stored procedures: {str(e)}', 'danger')

    return redirect(url_for('stored_procedures_view'))





# ====================================================================
# MÓDULO DE AGENDA DE CITAS Y PROGRAMACIÓN OPERATIVA (URABÁ-PAÍS 2026)
# ====================================================================

@app.route('/agenda')
@login_required
def agenda_citas():
    from datetime import date, timedelta
    fecha_param = request.args.get('fecha', '')
    municipio_f = request.args.get('municipio', '')

    if fecha_param:
        try:
            fecha_ref = datetime.strptime(fecha_param, '%Y-%m-%d').date()
        except Exception:
            fecha_ref = date.today()
    else:
        fecha_ref = date.today()

    # Calcular lunes y domingo de la semana actual
    dia_semana = fecha_ref.weekday()
    lunes = fecha_ref - timedelta(days=dia_semana)
    domingo = lunes + timedelta(days=6)

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT c.*, b.codigo_interno
        FROM citas c
        LEFT JOIN beneficiarios b ON c.beneficiario_id = b.id
        WHERE c.fecha_cita BETWEEN %s AND %s
    """
    params = [lunes, domingo]

    if municipio_f:
        query += " AND c.municipio = %s"
        params.append(municipio_f)

    query += " ORDER BY c.fecha_cita ASC, c.hora_cita ASC"
    cursor.execute(query, params)
    citas_raw = cursor.fetchall()

    # Agrupar por fecha
    citas_por_dia = {}
    for i in range(7):
        d = lunes + timedelta(days=i)
        citas_por_dia[d.isoformat()] = []

    for c in citas_raw:
        fd = c['fecha_cita']
        if hasattr(fd, 'isoformat'):
            key = fd.isoformat()
        else:
            key = str(fd)
        if key in citas_por_dia:
            citas_por_dia[key].append(c)
        else:
            citas_por_dia[key] = [c]

    # Obtener municipios para filtro
    cursor.execute("SELECT DISTINCT municipio FROM beneficiarios WHERE municipio IS NOT NULL AND municipio != '' ORDER BY municipio")
    municipios = [r['municipio'] for r in cursor.fetchall()]

    # Contadores KPI
    total_semana = len(citas_raw)
    atendidas = sum(1 for c in citas_raw if c['estado'] == 'Atendida')
    pendientes = sum(1 for c in citas_raw if c['estado'] in ('Programada', 'Confirmada'))
    hoy_count = sum(1 for c in citas_raw if str(c['fecha_cita']) == date.today().isoformat())

    conn.close()

    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    semana_data = []
    for i in range(7):
        d = lunes + timedelta(days=i)
        semana_data.append({
            'fecha': d.isoformat(),
            'dia_nombre': dias_semana[i],
            'dia_num': d.day,
            'mes': d.strftime('%b'),
            'es_hoy': d == date.today(),
            'citas': citas_por_dia.get(d.isoformat(), [])
        })

    sem_anterior = (lunes - timedelta(days=7)).isoformat()
    sem_siguiente = (lunes + timedelta(days=7)).isoformat()

    registrar_auditoria('CONSULTA_AGENDA', 'Acceso al módulo de Agenda de Citas y Programación', 'INFO')

    return render_template('agenda.html',
        semana_data=semana_data,
        lunes=lunes,
        domingo=domingo,
        sem_anterior=sem_anterior,
        sem_siguiente=sem_siguiente,
        total_semana=total_semana,
        atendidas=atendidas,
        pendientes=pendientes,
        hoy_count=hoy_count,
        municipios=municipios,
        municipio_filtro=municipio_f,
        todas_citas=citas_raw
    )

@app.route('/agenda/crear', methods=['POST'])
@login_required
def crear_cita():
    from datetime import date
    nombre = request.form.get('nombre_ciudadano', '').strip()
    num_doc = request.form.get('num_doc', '').strip()
    telefono = request.form.get('telefono', '').strip()
    municipio = request.form.get('municipio', '').strip()
    tipo_cita = request.form.get('tipo_cita', 'Atención Social')
    fecha_cita = request.form.get('fecha_cita', '')
    hora_cita = request.form.get('hora_cita', '')
    funcionario = request.form.get('funcionario_asignado', '').strip()
    observaciones = request.form.get('observaciones', '').strip()

    if not nombre or not fecha_cita or not hora_cita:
        flash('El nombre del ciudadano, fecha y hora son obligatorios.', 'danger')
        return redirect(url_for('agenda_citas'))

    # Buscar si hay beneficiario con ese documento
    ben_id = None
    if num_doc:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM beneficiarios WHERE num_doc = %s LIMIT 1", (num_doc,))
        ben = cursor.fetchone()
        if ben:
            ben_id = ben['id']
        conn.close()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO citas (beneficiario_id, nombre_ciudadano, num_doc, telefono, municipio,
                          tipo_cita, fecha_cita, hora_cita, funcionario_asignado, estado, observaciones, creado_por)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Programada', %s, %s)
    """, (ben_id, nombre, num_doc, telefono, municipio, tipo_cita, fecha_cita, hora_cita,
          funcionario or session.get('usuario', 'Funcionario'), observaciones, session.get('usuario', 'Sistema')))
    conn.close()
    flash('Cita programada exitosamente.', 'success')
    return redirect(url_for('agenda_citas', fecha=fecha_cita))

@app.route('/agenda/<int:id>/estado', methods=['POST'])
@login_required
def cambiar_estado_cita(id):
    nuevo_estado = request.form.get('estado', '')
    estados_validos = ['Programada', 'Confirmada', 'En Atención', 'Atendida', 'No Asistió', 'Cancelada']
    if nuevo_estado not in estados_validos:
        return jsonify({'ok': False, 'mensaje': 'Estado no válido'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE citas SET estado = %s WHERE id = %s", (nuevo_estado, id))
    conn.close()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': True, 'mensaje': f'Estado actualizado a {nuevo_estado}'})
    flash(f'Estado de la cita actualizado a "{nuevo_estado}".', 'success')
    return redirect(url_for('agenda_citas'))

@app.route('/agenda/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_cita(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM citas WHERE id = %s", (id,))
    conn.close()
    flash('Cita eliminada correctamente.', 'info')
    return redirect(url_for('agenda_citas'))

@app.route('/api/consultar-cita-publica', methods=['POST'])
def consultar_cita_publica():
    num_doc = request.form.get('num_doc', '').strip()
    if not num_doc or len(num_doc) < 4:
        return jsonify({'ok': False, 'mensaje': 'Ingrese un número de documento válido (mínimo 4 dígitos).'})
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.fecha_cita, c.hora_cita, c.tipo_cita, c.municipio, c.estado, c.funcionario_asignado
        FROM citas c
        WHERE c.num_doc = %s AND c.fecha_cita >= CURDATE() AND c.estado NOT IN ('Cancelada','No Asistió')
        ORDER BY c.fecha_cita ASC, c.hora_cita ASC
        LIMIT 5
    """, (num_doc,))
    citas = cursor.fetchall()
    conn.close()
    if not citas:
        return jsonify({'ok': True, 'citas': [], 'mensaje': 'No se encontraron citas programadas con este documento.'})
    resultado = []
    for c in citas:
        resultado.append({
            'fecha': str(c['fecha_cita']),
            'hora': str(c['hora_cita']),
            'tipo': c['tipo_cita'],
            'municipio': c['municipio'] or 'Urabá',
            'estado': c['estado'],
            'funcionario': c['funcionario_asignado'] or 'Por asignar'
        })
    return jsonify({'ok': True, 'citas': resultado})


if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000, debug=True)

