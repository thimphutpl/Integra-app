/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.6.22-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: _2b54387f591a8b64
-- ------------------------------------------------------
-- Server version	10.6.22-MariaDB-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `tabEmployee Separation`
--

DROP TABLE IF EXISTS `tabEmployee Separation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tabEmployee Separation` (
  `name` varchar(140) NOT NULL,
  `creation` datetime(6) DEFAULT NULL,
  `modified` datetime(6) DEFAULT NULL,
  `modified_by` varchar(140) DEFAULT NULL,
  `owner` varchar(140) DEFAULT NULL,
  `docstatus` int(1) NOT NULL DEFAULT 0,
  `idx` int(8) NOT NULL DEFAULT 0,
  `employee` varchar(140) DEFAULT NULL,
  `employee_name` varchar(140) DEFAULT NULL,
  `resignation_letter_date` date DEFAULT NULL,
  `reason_for_separation` text DEFAULT NULL,
  `boarding_status` varchar(140) DEFAULT NULL,
  `notify_users_by_email` int(1) NOT NULL DEFAULT 0,
  `types_of_separation` varchar(140) DEFAULT NULL,
  `serve_notice_period` varchar(140) DEFAULT NULL,
  `employee_separation_template` varchar(140) DEFAULT NULL,
  `project` varchar(140) DEFAULT NULL,
  `department` varchar(140) DEFAULT NULL,
  `designation` varchar(140) DEFAULT NULL,
  `employee_grade` varchar(140) DEFAULT NULL,
  `employee_benefit_claim_status` varchar(140) DEFAULT 'Not Claimed',
  `benefit_claim_reference` varchar(140) DEFAULT NULL,
  `exit_interview` longtext DEFAULT NULL,
  `clearance_acquired` int(1) NOT NULL DEFAULT 0,
  `approver` varchar(140) DEFAULT NULL,
  `approver_name` varchar(140) DEFAULT NULL,
  `approver_designation` varchar(140) DEFAULT NULL,
  `resignation` int(1) NOT NULL DEFAULT 0,
  `superannuation` int(1) NOT NULL DEFAULT 0,
  `workflow_state` varchar(140) DEFAULT NULL,
  `company` varchar(140) DEFAULT NULL,
  `amended_from` varchar(140) DEFAULT NULL,
  `_user_tags` text DEFAULT NULL,
  `_comments` text DEFAULT NULL,
  `_assign` text DEFAULT NULL,
  `_liked_by` text DEFAULT NULL,
  PRIMARY KEY (`name`),
  KEY `modified` (`modified`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tabEmployee Separation`
--

LOCK TABLES `tabEmployee Separation` WRITE;
/*!40000 ALTER TABLE `tabEmployee Separation` DISABLE KEYS */;
INSERT INTO `tabEmployee Separation` VALUES ('HR-EMP-SEP-2025-00007','2025-11-13 22:45:15.066262','2025-12-05 16:28:18.818478','Administrator','phuntsho@bhutantrustfund.bt',2,53,'BTF201412002','Phuntsho Choden','2025-12-31','dd','Pending',0,'Voluntary Resignation','Yes',NULL,'','Managing Director - BTF','Program Officer','O-II','Not Claimed',NULL,NULL,1,'thinley@bhutantrustfund.bt',NULL,NULL,0,0,'Cancelled','Bhutan Trust Fund for Environmental Conservation',NULL,NULL,NULL,NULL,NULL),('HR-EMP-SEP-2025-00007-1','2025-12-05 16:28:26.363446','2026-07-23 09:28:41.649394','Administrator','Administrator',1,9,'BTF201412002','Phuntsho Choden','2025-12-31','dd','Pending',0,'Voluntary Resignation','Yes',NULL,'PROJ-0006','Managing Director - BTF','Program Officer','O-II','Not Claimed',NULL,NULL,1,'thinley@bhutantrustfund.bt',NULL,NULL,0,0,'Approved','Bhutan Trust Fund for Environmental Conservation','HR-EMP-SEP-2025-00007',NULL,NULL,NULL,NULL),('HR-EMP-SEP-2026-00001','2026-09-30 15:33:13.067598','2026-09-30 15:37:16.124067','Administrator','Administrator',1,9,'BTF201409002','Thinley Wangdi','2026-09-30','test','Pending',0,'Voluntary Resignation','Yes',NULL,'PROJ-0007','Managing Director - BTF','IT Officer','O-II','Not Claimed',NULL,NULL,1,'kinzang@bhutantrustfund.bt',NULL,NULL,0,0,'Approved','Bhutan Trust Fund for Environmental Conservation',NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `tabEmployee Separation` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-01 16:55:34
