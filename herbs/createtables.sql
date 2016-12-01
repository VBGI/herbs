BEGIN;
CREATE TABLE `herbs_herbacronym` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(10) NOT NULL,
    `institute` varchar(300) NOT NULL,
    `address` varchar(100) NOT NULL,
    `allowed_users` varchar(1000) NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
CREATE TABLE `herbs_author` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(150) NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
CREATE TABLE `herbs_herbimage` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer,
    `image` varchar(100) NOT NULL,
    `type` varchar(1) NOT NULL,
    `created` date NOT NULL,
    `updated` date NOT NULL,
    `herbitem_id` integer NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_herbimage` ADD CONSTRAINT `user_id_refs_id_d3d4f9e5` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `herbs_familyauthorship` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `author_id` integer,
    `priority` integer NOT NULL,
    `family_id` integer NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_familyauthorship` ADD CONSTRAINT `author_id_refs_id_e704a699` FOREIGN KEY (`author_id`) REFERENCES `herbs_author` (`id`);
CREATE TABLE `herbs_genusauthorship` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `author_id` integer,
    `priority` integer NOT NULL,
    `genus_id` integer NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_genusauthorship` ADD CONSTRAINT `author_id_refs_id_d5ed8337` FOREIGN KEY (`author_id`) REFERENCES `herbs_author` (`id`);
CREATE TABLE `herbs_family` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(30) NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_familyauthorship` ADD CONSTRAINT `family_id_refs_id_f0b1cdd5` FOREIGN KEY (`family_id`) REFERENCES `herbs_family` (`id`);
CREATE TABLE `herbs_genus` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(30) NOT NULL,
    `family_id` integer,
    `gcode` varchar(6) NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_genus` ADD CONSTRAINT `family_id_refs_id_a95e05dd` FOREIGN KEY (`family_id`) REFERENCES `herbs_family` (`id`);
ALTER TABLE `herbs_genusauthorship` ADD CONSTRAINT `genus_id_refs_id_a20331ca` FOREIGN KEY (`genus_id`) REFERENCES `herbs_genus` (`id`);
CREATE TABLE `herbs_speciesauthorship` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `author_id` integer,
    `priority` integer NOT NULL,
    `species_id` integer NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_speciesauthorship` ADD CONSTRAINT `author_id_refs_id_8ae79b1a` FOREIGN KEY (`author_id`) REFERENCES `herbs_author` (`id`);
CREATE TABLE `herbs_species` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(30) NOT NULL,
    `genus_id` integer
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_species` ADD CONSTRAINT `genus_id_refs_id_43fd2a3a` FOREIGN KEY (`genus_id`) REFERENCES `herbs_genus` (`id`);
ALTER TABLE `herbs_speciesauthorship` ADD CONSTRAINT `species_id_refs_id_d2d4a07f` FOREIGN KEY (`species_id`) REFERENCES `herbs_species` (`id`);
CREATE TABLE `herbs_herbitem` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `family_id` integer,
    `genus_id` integer,
    `species_id` integer,
    `itemcode` varchar(15) NOT NULL,
    `acronym_id` integer,
    `country` varchar(255) NOT NULL,
    `region` varchar(150) NOT NULL,
    `district` varchar(150) NOT NULL,
    `detailed` varchar(300) NOT NULL,
    `coordinates` varchar(42) NOT NULL,
    `place` varchar(30) NOT NULL,
    `altitude` varchar(50) NOT NULL,
    `ecodescr` varchar(300) NOT NULL,
    `collectedby` varchar(500) NOT NULL,
    `collected_s` date,
    `collected_e` date,
    `identifiedby` varchar(500) NOT NULL,
    `identified_s` date,
    `identified_e` date,
    `note` varchar(1000) NOT NULL,
    `uhash` varchar(32) NOT NULL,
    `created` date NOT NULL,
    `updated` date NOT NULL,
    `createdby_id` integer,
    `updatedby_id` integer,
    `public` bool NOT NULL,
    `user_id` integer
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_herbitem` ADD CONSTRAINT `acronym_id_refs_id_015802ea` FOREIGN KEY (`acronym_id`) REFERENCES `herbs_herbacronym` (`id`);
ALTER TABLE `herbs_herbitem` ADD CONSTRAINT `genus_id_refs_id_7882c0d7` FOREIGN KEY (`genus_id`) REFERENCES `herbs_genus` (`id`);
ALTER TABLE `herbs_herbitem` ADD CONSTRAINT `family_id_refs_id_7eb07050` FOREIGN KEY (`family_id`) REFERENCES `herbs_family` (`id`);
ALTER TABLE `herbs_herbitem` ADD CONSTRAINT `species_id_refs_id_b9d4fed3` FOREIGN KEY (`species_id`) REFERENCES `herbs_species` (`id`);
ALTER TABLE `herbs_herbitem` ADD CONSTRAINT `createdby_id_refs_id_3c32b0f2` FOREIGN KEY (`createdby_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `herbs_herbitem` ADD CONSTRAINT `updatedby_id_refs_id_3c32b0f2` FOREIGN KEY (`updatedby_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `herbs_herbitem` ADD CONSTRAINT `user_id_refs_id_3c32b0f2` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `herbs_herbimage` ADD CONSTRAINT `herbitem_id_refs_id_92bffe2c` FOREIGN KEY (`herbitem_id`) REFERENCES `herbs_herbitem` (`id`);
CREATE TABLE `herbs_pendingherbs` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `family_id` integer,
    `genus_id` integer,
    `species_id` integer,
    `itemcode` varchar(15) UNIQUE,
    `acronym_id` integer,
    `country` varchar(255) NOT NULL,
    `region` varchar(150) NOT NULL,
    `district` varchar(150) NOT NULL,
    `detailed` varchar(300) NOT NULL,
    `coordinates` varchar(42) NOT NULL,
    `place` varchar(30) NOT NULL,
    `altitude` varchar(50) NOT NULL,
    `ecodescr` varchar(300) NOT NULL,
    `collectedby` varchar(500) NOT NULL,
    `collected_s` date,
    `collected_e` date,
    `identifiedby` varchar(500) NOT NULL,
    `identified_s` date,
    `identified_e` date,
    `note` varchar(1000) NOT NULL,
    `uhash` varchar(32) NOT NULL,
    `created` date NOT NULL,
    `updated` date NOT NULL,
    `createdby_id` integer,
    `updatedby_id` integer,
    `public` bool NOT NULL,
    `checked` bool NOT NULL,
    `err_msg` longtext NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_pendingherbs` ADD CONSTRAINT `acronym_id_refs_id_9bed4492` FOREIGN KEY (`acronym_id`) REFERENCES `herbs_herbacronym` (`id`);
ALTER TABLE `herbs_pendingherbs` ADD CONSTRAINT `genus_id_refs_id_50ad42be` FOREIGN KEY (`genus_id`) REFERENCES `herbs_genus` (`id`);
ALTER TABLE `herbs_pendingherbs` ADD CONSTRAINT `family_id_refs_id_c51c79c3` FOREIGN KEY (`family_id`) REFERENCES `herbs_family` (`id`);
ALTER TABLE `herbs_pendingherbs` ADD CONSTRAINT `species_id_refs_id_69cc49eb` FOREIGN KEY (`species_id`) REFERENCES `herbs_species` (`id`);
ALTER TABLE `herbs_pendingherbs` ADD CONSTRAINT `createdby_id_refs_id_2d5ed6ed` FOREIGN KEY (`createdby_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `herbs_pendingherbs` ADD CONSTRAINT `updatedby_id_refs_id_2d5ed6ed` FOREIGN KEY (`updatedby_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `herbs_loadedfiles` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `datafile` varchar(100) NOT NULL,
    `created` date NOT NULL,
    `status` bool NOT NULL,
    `createdby_id` integer
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_loadedfiles` ADD CONSTRAINT `createdby_id_refs_id_a705f8e9` FOREIGN KEY (`createdby_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `herbs_errorlog` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `message` longtext NOT NULL,
    `who` varchar(255) NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
CREATE INDEX `herbs_herbimage_6340c63c` ON `herbs_herbimage` (`user_id`);
CREATE INDEX `herbs_herbimage_40acd659` ON `herbs_herbimage` (`herbitem_id`);
CREATE INDEX `herbs_familyauthorship_e969df21` ON `herbs_familyauthorship` (`author_id`);
CREATE INDEX `herbs_familyauthorship_a1b9975e` ON `herbs_familyauthorship` (`family_id`);
CREATE INDEX `herbs_genusauthorship_e969df21` ON `herbs_genusauthorship` (`author_id`);
CREATE INDEX `herbs_genusauthorship_bd17be42` ON `herbs_genusauthorship` (`genus_id`);
CREATE INDEX `herbs_genus_a1b9975e` ON `herbs_genus` (`family_id`);
CREATE INDEX `herbs_speciesauthorship_e969df21` ON `herbs_speciesauthorship` (`author_id`);
CREATE INDEX `herbs_speciesauthorship_e1800d51` ON `herbs_speciesauthorship` (`species_id`);
CREATE INDEX `herbs_species_bd17be42` ON `herbs_species` (`genus_id`);
CREATE INDEX `herbs_herbitem_a1b9975e` ON `herbs_herbitem` (`family_id`);
CREATE INDEX `herbs_herbitem_bd17be42` ON `herbs_herbitem` (`genus_id`);
CREATE INDEX `herbs_herbitem_e1800d51` ON `herbs_herbitem` (`species_id`);
CREATE INDEX `herbs_herbitem_8abec25e` ON `herbs_herbitem` (`acronym_id`);
CREATE INDEX `herbs_herbitem_44c0abc5` ON `herbs_herbitem` (`createdby_id`);
CREATE INDEX `herbs_herbitem_fae345b2` ON `herbs_herbitem` (`updatedby_id`);
CREATE INDEX `herbs_herbitem_6340c63c` ON `herbs_herbitem` (`user_id`);
CREATE INDEX `herbs_pendingherbs_a1b9975e` ON `herbs_pendingherbs` (`family_id`);
CREATE INDEX `herbs_pendingherbs_bd17be42` ON `herbs_pendingherbs` (`genus_id`);
CREATE INDEX `herbs_pendingherbs_e1800d51` ON `herbs_pendingherbs` (`species_id`);
CREATE INDEX `herbs_pendingherbs_8abec25e` ON `herbs_pendingherbs` (`acronym_id`);
CREATE INDEX `herbs_pendingherbs_44c0abc5` ON `herbs_pendingherbs` (`createdby_id`);
CREATE INDEX `herbs_pendingherbs_fae345b2` ON `herbs_pendingherbs` (`updatedby_id`);
CREATE INDEX `herbs_loadedfiles_44c0abc5` ON `herbs_loadedfiles` (`createdby_id`);
COMMIT;
 
