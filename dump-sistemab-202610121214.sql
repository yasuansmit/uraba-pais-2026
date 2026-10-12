-- MySQL dump 10.13  Distrib 8.0.19, for Win64 (x86_64)
--
-- Host: localhost    Database: sistemab
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `atenciones`
--

DROP TABLE IF EXISTS `atenciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `atenciones` (
  `id_atencion` int NOT NULL AUTO_INCREMENT,
  `id_beneficiario` int NOT NULL,
  `tipo` varchar(100) NOT NULL,
  `fecha` date NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `responsable` varchar(100) DEFAULT NULL,
  `resultado` varchar(255) DEFAULT NULL,
  `remision` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_atencion`),
  KEY `id_beneficiario` (`id_beneficiario`),
  CONSTRAINT `atenciones_ibfk_1` FOREIGN KEY (`id_beneficiario`) REFERENCES `beneficiarios` (`id_beneficiario`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `atenciones`
--

LOCK TABLES `atenciones` WRITE;
/*!40000 ALTER TABLE `atenciones` DISABLE KEYS */;
INSERT INTO `atenciones` VALUES (1,1,'Orientación familiar','2026-08-10','Orientación sobre beneficios del programa','Trabajadora social','Se brindó orientación','No aplica'),(2,1,'Apoyo educativo','2026-08-15','Información sobre acceso a programas educativos','Coordinador educativo','Se realizó inscripción','Programa Educación'),(3,2,'Orientación laboral','2026-08-18','Orientación para búsqueda de empleo','Gestor laboral','Se entregaron recomendaciones','No aplica'),(4,3,'Apoyo educativo','2026-08-22','Información sobre oportunidades de estudio','Coordinadora educativa','Se inició proceso de inscripción','Programa Educación'),(5,4,'Apoyo alimentario','2026-08-25','Entrega de apoyo alimentario','Trabajador social','Apoyo entregado','No aplica'),(6,5,'Orientación laboral','2026-09-01','Orientación para mejorar oportunidades laborales','Gestora laboral','Se realizó orientación','No aplica');
/*!40000 ALTER TABLE `atenciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `beneficiarios`
--

DROP TABLE IF EXISTS `beneficiarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `beneficiarios` (
  `id_beneficiario` int NOT NULL AUTO_INCREMENT,
  `codigo_interno` varchar(50) NOT NULL,
  `nombres` varchar(50) NOT NULL,
  `apellidos` varchar(50) NOT NULL,
  `tipo_documento` varchar(20) DEFAULT NULL,
  `numero_documento` varchar(30) DEFAULT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `edad` int DEFAULT NULL,
  `municipio` varchar(100) NOT NULL,
  `contacto_telefono` varchar(20) DEFAULT NULL,
  `contacto_email` varchar(100) DEFAULT NULL,
  `datos_sociodemograficos` text,
  `autorizacion_tratamiento_datos` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_beneficiario`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `beneficiarios`
--

LOCK TABLES `beneficiarios` WRITE;
/*!40000 ALTER TABLE `beneficiarios` DISABLE KEYS */;
INSERT INTO `beneficiarios` VALUES (1,'B001','María Fernanda','Rentería Mosquera','CC','1039456781','1990-03-14',36,'Apartadó','3101234567','maria.renteria@example.com','Mujer; estrato 2; bachiller; madre cabeza de hogar',1),(2,'B002','Carlos Andrés','Pérez López','CC','1045678912','1985-07-22',41,'Turbo','3112345678','carlos.perez@example.com','Hombre; estrato 2; técnico; trabajador independiente',1),(3,'B003','Laura Daniela','Mena Córdoba','CC','1056789123','1998-11-05',27,'Apartadó','3123456789','laura.mena@example.com','Mujer; estrato 3; universitaria; soltera',1),(4,'B004','José Manuel','Palacios Ríos','CC','1067891234','1978-02-18',48,'Carepa','3134567890','jose.palacios@example.com','Hombre; estrato 1; primaria; agricultor',1),(5,'B005','Ana María','Córdoba Valencia','CC','1078912345','1993-09-30',32,'Chigorodó','3145678901','ana.cordoba@example.com','Mujer; estrato 2; bachiller; comerciante',1);
/*!40000 ALTER TABLE `beneficiarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `familia`
--

DROP TABLE IF EXISTS `familia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `familia` (
  `id_familia` int NOT NULL AUTO_INCREMENT,
  `id_beneficiario` int NOT NULL,
  `nombre_integrante` varchar(100) NOT NULL,
  `parentesco` varchar(50) DEFAULT NULL,
  `edad` int DEFAULT NULL,
  `ocupacion` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_familia`),
  KEY `id_beneficiario` (`id_beneficiario`),
  CONSTRAINT `familia_ibfk_1` FOREIGN KEY (`id_beneficiario`) REFERENCES `beneficiarios` (`id_beneficiario`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `familia`
--

LOCK TABLES `familia` WRITE;
/*!40000 ALTER TABLE `familia` DISABLE KEYS */;
INSERT INTO `familia` VALUES (1,1,'Juan David Rentería','Hijo',12,'Estudiante'),(2,1,'Sofía Rentería','Hija',8,'Estudiante'),(3,2,'Diana López','Esposa',38,'Comerciante'),(4,2,'Mateo Pérez','Hijo',15,'Estudiante'),(5,3,'Rosa Mena','Madre',55,'Ama de casa'),(6,4,'Pedro Palacios','Hijo',20,'Estudiante'),(7,5,'Miguel Córdoba','Esposo',35,'Comerciante');
/*!40000 ALTER TABLE `familia` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `participaciones`
--

DROP TABLE IF EXISTS `participaciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `participaciones` (
  `id_participacion` int NOT NULL AUTO_INCREMENT,
  `id_beneficiario` int NOT NULL,
  `id_programa` int NOT NULL,
  `fecha_vinculacion` date NOT NULL,
  `estado` varchar(20) NOT NULL,
  PRIMARY KEY (`id_participacion`),
  KEY `id_beneficiario` (`id_beneficiario`),
  KEY `id_programa` (`id_programa`),
  CONSTRAINT `participaciones_ibfk_1` FOREIGN KEY (`id_beneficiario`) REFERENCES `beneficiarios` (`id_beneficiario`),
  CONSTRAINT `participaciones_ibfk_2` FOREIGN KEY (`id_programa`) REFERENCES `programas` (`id_programa`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `participaciones`
--

LOCK TABLES `participaciones` WRITE;
/*!40000 ALTER TABLE `participaciones` DISABLE KEYS */;
INSERT INTO `participaciones` VALUES (1,1,1,'2026-08-05','En proceso'),(2,1,3,'2026-08-10','Inscrito'),(3,2,2,'2026-08-12','En proceso'),(4,3,3,'2026-08-15','En proceso'),(5,4,4,'2026-08-20','Finalizado'),(6,5,5,'2026-08-25','Inscrito');
/*!40000 ALTER TABLE `participaciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `programas`
--

DROP TABLE IF EXISTS `programas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `programas` (
  `id_programa` int NOT NULL AUTO_INCREMENT,
  `nombre_programa` varchar(100) NOT NULL,
  `linea_trabajo` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_programa`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `programas`
--

LOCK TABLES `programas` WRITE;
/*!40000 ALTER TABLE `programas` DISABLE KEYS */;
INSERT INTO `programas` VALUES (1,'Apoyo Familiar','Bienestar'),(2,'Emprendimiento','Generación de ingresos'),(3,'Educación','Formación'),(4,'Apoyo Alimentario','Seguridad alimentaria'),(5,'Orientación Laboral','Empleo');
/*!40000 ALTER TABLE `programas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `seguimientos`
--

DROP TABLE IF EXISTS `seguimientos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seguimientos` (
  `id_seguimiento` int NOT NULL AUTO_INCREMENT,
  `id_atencion` int NOT NULL,
  `fecha` date NOT NULL,
  `avance` varchar(255) DEFAULT NULL,
  `novedad` varchar(255) DEFAULT NULL,
  `observacion` varchar(255) DEFAULT NULL,
  `accion_pendiente` varchar(255) DEFAULT NULL,
  `proximo_contacto` date DEFAULT NULL,
  PRIMARY KEY (`id_seguimiento`),
  KEY `id_atencion` (`id_atencion`),
  CONSTRAINT `seguimientos_ibfk_1` FOREIGN KEY (`id_atencion`) REFERENCES `atenciones` (`id_atencion`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seguimientos`
--

LOCK TABLES `seguimientos` WRITE;
/*!40000 ALTER TABLE `seguimientos` DISABLE KEYS */;
INSERT INTO `seguimientos` VALUES (1,1,'2026-08-20','Avance en el proceso familiar','La beneficiaria continúa participando','Se observa buena participación','Verificar documentación','2026-10-05'),(2,2,'2026-08-25','Inscripción realizada','La beneficiaria inició el proceso','Debe continuar con las actividades','Confirmar asistencia','2026-10-10'),(3,3,'2026-08-30','Búsqueda de empleo iniciada','El beneficiario está buscando opciones','Se recomienda seguimiento','Consultar nuevas ofertas','2026-10-15'),(4,4,'2026-09-01','Proceso de inscripción iniciado','Pendiente documentación','Falta entregar documentos','Recibir documentos','2026-10-01'),(5,5,'2026-09-05','Apoyo recibido','No se presentaron novedades','Caso cerrado','No aplica','2026-12-01'),(6,6,'2026-09-10','Orientación completada','La beneficiaria continúa buscando empleo','Se requiere nuevo seguimiento','Verificar avances','2026-10-20');
/*!40000 ALTER TABLE `seguimientos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'sistemab'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-12 12:14:05
