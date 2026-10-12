-- MySQL dump 10.13  Distrib 8.0.19, for Win64 (x86_64)
--
-- Host: localhost    Database: uraba_pais_db
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
  `id` int NOT NULL AUTO_INCREMENT,
  `beneficiario_id` int DEFAULT NULL,
  `tipo` varchar(255) DEFAULT NULL,
  `fecha` varchar(100) DEFAULT NULL,
  `descripcion` text,
  `responsable` varchar(255) DEFAULT NULL,
  `remision` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `beneficiario_id` (`beneficiario_id`),
  CONSTRAINT `atenciones_ibfk_1` FOREIGN KEY (`beneficiario_id`) REFERENCES `beneficiarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `atenciones`
--

LOCK TABLES `atenciones` WRITE;
/*!40000 ALTER TABLE `atenciones` DISABLE KEYS */;
INSERT INTO `atenciones` VALUES (2,11,'Revision','2026-10-08','El autorr tatatatata','Jhean Ortiz','Entregado');
/*!40000 ALTER TABLE `atenciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `beneficiarios`
--

DROP TABLE IF EXISTS `beneficiarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `beneficiarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo_interno` varchar(100) DEFAULT NULL,
  `tipo_doc` varchar(100) DEFAULT NULL,
  `num_doc` varchar(100) DEFAULT NULL,
  `nombres` varchar(255) DEFAULT NULL,
  `apellidos` varchar(255) DEFAULT NULL,
  `fecha_nacimiento` varchar(100) DEFAULT NULL,
  `sexo` varchar(50) DEFAULT NULL,
  `telefono` varchar(100) DEFAULT NULL,
  `municipio` varchar(255) DEFAULT NULL,
  `condicion_poblacional` varchar(255) DEFAULT NULL,
  `discapacidad` varchar(255) DEFAULT NULL,
  `habeas_data` int DEFAULT '1',
  `fecha_registro` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `num_doc` (`num_doc`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `beneficiarios`
--

LOCK TABLES `beneficiarios` WRITE;
/*!40000 ALTER TABLE `beneficiarios` DISABLE KEYS */;
INSERT INTO `beneficiarios` VALUES (1,'BEN-4012','Cédula de Ciudadanía','1045500887','Yasuan','Caicedo','2011-09-21','Masculino','3216139972','Turbo','Sisben','Ninguna',1,'2026-09-30 18:04:37'),(2,'BEN-4492','Cédula de Ciudadanía','1045487391','Julian','Restrepo Ramirez','2026-09-10','Masculino','3216139972','Apartadó','Nada','Ninguna',0,'2026-09-30 18:17:07'),(3,'BEN-9983','Cédula de Ciudadanía','4552632288','jhean franco','velasquez','2026-09-30','Masculino','3699996655','Apartadó','sisben','Tuerto ',1,'2026-09-30 18:19:10'),(4,'BEN-1641','Cédula de Ciudadanía','10235487','Juan Esteban','Patiño Echavez','2005-07-11','Masculino','31285894','Chigorodó','Sisben','No ve',1,'2026-10-01 01:04:47'),(5,'BEN-9139','Cédula de Ciudadanía','105898693','Juan Carlos','Abenaño Perez','2007-04-26','Masculino','3216548578','Apartadó','Sisben','Visual',1,'2026-10-05 07:35:48'),(6,'BEN-3618','Cédula de Ciudadanía','123456789','Luisa Castro','Castro Luisa','2055-12-13','Masculino','3698755','Apartadó','Desplazado','Tuerto',1,'2026-10-05 13:23:10'),(8,'BEN-4741','Cédula de Ciudadanía','114547884','CARLOS ALBERTO','MURILLO','2026-10-07','Masculino','366589754','Carepa','Refugiado/a o solicitante de asilo','Visual',1,'2026-10-05 17:37:47'),(9,'BEN-1778','Cédula de Ciudadanía','1045875698','Jhon Wilmar','Becerra Mosquera','2005-08-12','Masculino','325874125','Apartadó','Migrante','Auditiva',1,'2026-10-07 17:43:32'),(10,'BEN-4703','Tarjeta de Identidad','102545478','Karly Johana','Torres Castro','2009-04-29','Femenino','3265886544','Necoclí','Migrante','Física',1,'2026-10-07 19:41:30'),(11,'BEN-3760','Cédula de Ciudadanía','26286824','Doris','Sanchez Cordoba','1989-07-13','Femenino','3215698547','Turbo','Población local','Auditiva',1,'2026-10-08 10:44:38'),(12,'BEN-9276','Cédula de Ciudadanía','147896325','Luis Alfonso','Martinez Bedoya','2007-03-09','Masculino','3216139972','San Pedro de Urabá','Migrante','Psicosocial',1,'2026-10-11 20:25:46');
/*!40000 ALTER TABLE `beneficiarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `nucleo_familiar`
--

DROP TABLE IF EXISTS `nucleo_familiar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nucleo_familiar` (
  `id` int NOT NULL AUTO_INCREMENT,
  `beneficiario_id` int DEFAULT NULL,
  `nombre_completo` varchar(255) DEFAULT NULL,
  `parentesco` varchar(100) DEFAULT NULL,
  `edad` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `beneficiario_id` (`beneficiario_id`),
  CONSTRAINT `nucleo_familiar_ibfk_1` FOREIGN KEY (`beneficiario_id`) REFERENCES `beneficiarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `nucleo_familiar`
--

LOCK TABLES `nucleo_familiar` WRITE;
/*!40000 ALTER TABLE `nucleo_familiar` DISABLE KEYS */;
INSERT INTO `nucleo_familiar` VALUES (1,11,'VILMA ROSA FLOREZ','HERMANA',55);
/*!40000 ALTER TABLE `nucleo_familiar` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `participaciones`
--

DROP TABLE IF EXISTS `participaciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `participaciones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `beneficiario_id` int DEFAULT NULL,
  `programa_nombre` varchar(255) DEFAULT NULL,
  `linea_trabajo` varchar(255) DEFAULT NULL,
  `fecha_vinculacion` varchar(100) DEFAULT NULL,
  `estado` varchar(100) DEFAULT 'Activo',
  PRIMARY KEY (`id`),
  KEY `beneficiario_id` (`beneficiario_id`),
  CONSTRAINT `participaciones_ibfk_1` FOREIGN KEY (`beneficiario_id`) REFERENCES `beneficiarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `participaciones`
--

LOCK TABLES `participaciones` WRITE;
/*!40000 ALTER TABLE `participaciones` DISABLE KEYS */;
INSERT INTO `participaciones` VALUES (1,2,'Formación Juvenil','Capital Semilla','2026-09-30','inscrito'),(2,11,'Formación Juvenil','Capital Semilla','2026-10-08','inscrito'),(3,10,'Atención Psicosocial Comunitaria','Salud y Bienestar','2026-10-09','inscrito'),(4,4,'Emprendimiento Urabá','Capital Semilla','2026-10-13','inscrito');
/*!40000 ALTER TABLE `participaciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `seguimientos`
--

DROP TABLE IF EXISTS `seguimientos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seguimientos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `beneficiario_id` int DEFAULT NULL,
  `fecha` varchar(100) DEFAULT NULL,
  `avance` text,
  `proxima_accion` text,
  `fecha_proximo_contacto` varchar(100) DEFAULT NULL,
  `estado_accion` varchar(100) DEFAULT 'Pendiente',
  PRIMARY KEY (`id`),
  KEY `beneficiario_id` (`beneficiario_id`),
  CONSTRAINT `seguimientos_ibfk_1` FOREIGN KEY (`beneficiario_id`) REFERENCES `beneficiarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seguimientos`
--

LOCK TABLES `seguimientos` WRITE;
/*!40000 ALTER TABLE `seguimientos` DISABLE KEYS */;
INSERT INTO `seguimientos` VALUES (1,5,'2026-10-08','Buen avance','LLamada','2026-10-17','Pendiente'),(2,11,'2026-10-08','SISISIS','LLamada','2026-10-19','Pendiente');
/*!40000 ALTER TABLE `seguimientos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tblcondicionp`
--

DROP TABLE IF EXISTS `tblcondicionp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tblcondicionp` (
  `idcondicion` int NOT NULL AUTO_INCREMENT,
  `condicion` enum('Migrante','Refugiado/a o solicitante de asilo','Retornado/a','Desplazado/a','Población local') NOT NULL,
  PRIMARY KEY (`idcondicion`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tblcondicionp`
--

LOCK TABLES `tblcondicionp` WRITE;
/*!40000 ALTER TABLE `tblcondicionp` DISABLE KEYS */;
INSERT INTO `tblcondicionp` VALUES (1,'Migrante'),(2,'Refugiado/a o solicitante de asilo'),(3,'Retornado/a'),(4,'Desplazado/a'),(5,'Población local');
/*!40000 ALTER TABLE `tblcondicionp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbldiscapacidad`
--

DROP TABLE IF EXISTS `tbldiscapacidad`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbldiscapacidad` (
  `iddiscapacidad` int NOT NULL AUTO_INCREMENT,
  `discapacidad` enum('Ninguna','Física','Visual','Auditiva','Intelectual','Psicosocial','Múltiple','Sordoceguera') NOT NULL,
  PRIMARY KEY (`iddiscapacidad`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbldiscapacidad`
--

LOCK TABLES `tbldiscapacidad` WRITE;
/*!40000 ALTER TABLE `tbldiscapacidad` DISABLE KEYS */;
INSERT INTO `tbldiscapacidad` VALUES (1,'Ninguna'),(2,'Física'),(3,'Visual'),(4,'Auditiva'),(5,'Intelectual'),(6,'Psicosocial'),(7,'Múltiple'),(8,'Sordoceguera');
/*!40000 ALTER TABLE `tbldiscapacidad` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(255) DEFAULT NULL,
  `correo` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `rol` varchar(50) DEFAULT 'funcionario',
  PRIMARY KEY (`id`),
  UNIQUE KEY `correo` (`correo`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'Administrador','admin@uraba.gov.co','scrypt:32768:8:1$NraNQs7MJJIjT2sE$f1f2a0969d7e7ec3f59c5cc61a443e8e82430632abed3c1c6257f3f220ec50521d0cd9f9a2dcb3a95d6a90a39c13202c39cb48cc239d62592ceda173e0d90e1a','administrador'),(2,'Funcionario','funcionario@uraba.gov.co','scrypt:32768:8:1$I6BKwWvyxSmTbpou$9c4dc71f97cdbf5cc800976bd665a782df038d5d5e70af54ea36e63e1f6da512f3298248f2451902909bb05cfc3a17680cb27f4460fee360fc76e5192bc83711','funcionario');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'uraba_pais_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-12 12:12:12
