--
-- Table structure for table `woodstove_job`
--

CREATE TABLE `woodstove_job` (
      `uuid` varchar(36) NOT NULL DEFAULT '',
      `state` int(11) DEFAULT NULL,
      `output` mediumtext,
      `start_time` int(11) DEFAULT NULL,
      `end_time` int(11) DEFAULT NULL,
      `user_id` int(11) unsigned DEFAULT NULL,
      `queue_time` int(11) DEFAULT NULL,
      `path` varchar(255) DEFAULT NULL,
      `func` varchar(255) DEFAULT NULL,
      `module` varchar(255) DEFAULT NULL,
      `args` text,
      `kwargs` text,
      `parent_uuid` varchar(36) DEFAULT NULL,
      PRIMARY KEY (`uuid`),
      KEY `uuid` (`uuid`),
      KEY `user_id` (`user_id`),
      KEY `parent_uuid` (`parent_uuid`),
      CONSTRAINT `woodstove_job_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `woodstove_user` (`user_id`) ON DELETE SET NULL ON UPDATE CASCADE,
      CONSTRAINT `woodstove_job_ibfk_2` FOREIGN KEY (`parent_uuid`) REFERENCES `woodstove_job` (`uuid`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

--
-- Table structure for table `woodstove_ownership`
--

CREATE TABLE `woodstove_ownership` (
      `ownership_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
      `user_id` int(10) unsigned DEFAULT NULL,
      `group_name` varchar(255) DEFAULT NULL,
      `klass` blob,
      `object_id` blob,
      `object_id_name` varchar(1024) DEFAULT NULL,
      `private` text,
      PRIMARY KEY (`ownership_id`)
) ENGINE=InnoDB;

--
-- Table structure for table `woodstove_user`
--

CREATE TABLE `woodstove_user` (
      `user_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
      `name` varchar(63) NOT NULL,
      `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
      `private` text,
      `active` tinyint(4) DEFAULT '1',
      PRIMARY KEY (`user_id`),
      UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB;
