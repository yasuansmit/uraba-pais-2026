CREATE DATABASE IF NOT EXISTS uraba_pais DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE uraba_pais;


CREATE TABLE IF NOT EXISTS beneficiario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_interno VARCHAR(36) NOT NULL UNIQUE,
    nombres VARCHAR(150) NOT NULL,
    tipo_doc VARCHAR(20),
    num_doc VARCHAR(30),
    fecha_nacimiento DATE,
    municipio VARCHAR(100) NOT NULL,
    contacto VARCHAR(100),
    autorizacion_datos TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_documento (tipo_doc, num_doc)
);

CREATE TABLE IF NOT EXISTS familia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    beneficiario_id INT NOT NULL,
    nombres VARCHAR(150) NOT NULL,
    parentesco VARCHAR(50) NOT NULL,
    edad INT,
    FOREIGN KEY (beneficiario_id) REFERENCES beneficiario(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS programa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    linea_intervencion VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS participacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    beneficiario_id INT NOT NULL,
    programa_id INT NOT NULL,
    fecha_vinculacion DATE NOT NULL,
    estado ENUM('inscrito', 'en proceso', 'finalizado', 'retirado') DEFAULT 'inscrito',
    FOREIGN KEY (beneficiario_id) REFERENCES beneficiario(id) ON DELETE CASCADE,
    FOREIGN KEY (programa_id) REFERENCES programa(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS atencion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    beneficiario_id INT NOT NULL,
    tipo VARCHAR(100) NOT NULL,
    fecha DATE NOT NULL,
    descripcion TEXT NOT NULL,
    responsable VARCHAR(150) NOT NULL,
    resultado VARCHAR(150),
    FOREIGN KEY (beneficiario_id) REFERENCES beneficiario(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS seguimiento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    beneficiario_id INT NOT NULL,
    fecha DATE NOT NULL,
    avance_novedad TEXT NOT NULL,
    observacion TEXT,
    accion_pendiente TEXT,
    FOREIGN KEY (beneficiario_id) REFERENCES beneficiario(id) ON DELETE CASCADE
);