BEGIN;
CREATE TABLE `herbs_country` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name_ru` varchar(150) NOT NULL,
    `name_en` varchar(150) NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
CREATE TABLE `herbs_herbacronym` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(10) NOT NULL,
    `institute` varchar(300) NOT NULL,
    `address` varchar(100) NOT NULL,
    `allowed_users` varchar(1000) NOT NULL
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
CREATE TABLE `herbs_family` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(70) NOT NULL,
    `authorship` varchar(250) NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
CREATE TABLE `herbs_genus` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(70) NOT NULL,
    `authorship` varchar(250) NOT NULL,
    `family_id` integer,
    `gcode` varchar(6) NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_genus` ADD CONSTRAINT `family_id_refs_id_a95e05dd` FOREIGN KEY (`family_id`) REFERENCES `herbs_family` (`id`);
CREATE TABLE `herbs_species` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(70) NOT NULL,
    `authorship` varchar(250) NOT NULL,
    `genus_id` integer
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_species` ADD CONSTRAINT `genus_id_refs_id_43fd2a3a` FOREIGN KEY (`genus_id`) REFERENCES `herbs_genus` (`id`);
CREATE TABLE `herbs_herbitem` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `species_id` integer,
    `itemcode` varchar(15),
    `acronym_id` integer,
    `devstage` varchar(1),
    `country_id` integer,
    `region` varchar(150) NOT NULL,
    `district` varchar(150) NOT NULL,
    `detailed` varchar(300) NOT NULL,
    `coordinates` varchar(42) NOT NULL,
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
ALTER TABLE `herbs_herbitem` ADD CONSTRAINT `country_id_refs_id_8f50534e` FOREIGN KEY (`country_id`) REFERENCES `herbs_country` (`id`);
ALTER TABLE `herbs_herbitem` ADD CONSTRAINT `createdby_id_refs_id_3c32b0f2` FOREIGN KEY (`createdby_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `herbs_herbitem` ADD CONSTRAINT `updatedby_id_refs_id_3c32b0f2` FOREIGN KEY (`updatedby_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `herbs_herbitem` ADD CONSTRAINT `user_id_refs_id_3c32b0f2` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `herbs_herbitem` ADD CONSTRAINT `species_id_refs_id_b9d4fed3` FOREIGN KEY (`species_id`) REFERENCES `herbs_species` (`id`);
ALTER TABLE `herbs_herbitem` ADD CONSTRAINT `acronym_id_refs_id_015802ea` FOREIGN KEY (`acronym_id`) REFERENCES `herbs_herbacronym` (`id`);
ALTER TABLE `herbs_herbimage` ADD CONSTRAINT `herbitem_id_refs_id_92bffe2c` FOREIGN KEY (`herbitem_id`) REFERENCES `herbs_herbitem` (`id`);
CREATE INDEX `herbs_herbimage_6340c63c` ON `herbs_herbimage` (`user_id`);
CREATE INDEX `herbs_herbimage_40acd659` ON `herbs_herbimage` (`herbitem_id`);
CREATE INDEX `herbs_genus_a1b9975e` ON `herbs_genus` (`family_id`);
CREATE INDEX `herbs_species_bd17be42` ON `herbs_species` (`genus_id`);
CREATE INDEX `herbs_herbitem_e1800d51` ON `herbs_herbitem` (`species_id`);
CREATE INDEX `herbs_herbitem_8abec25e` ON `herbs_herbitem` (`acronym_id`);
CREATE INDEX `herbs_herbitem_d860be3c` ON `herbs_herbitem` (`country_id`);
CREATE INDEX `herbs_herbitem_44c0abc5` ON `herbs_herbitem` (`createdby_id`);
CREATE INDEX `herbs_herbitem_fae345b2` ON `herbs_herbitem` (`updatedby_id`);
CREATE INDEX `herbs_herbitem_6340c63c` ON `herbs_herbitem` (`user_id`);
COMMIT; 
