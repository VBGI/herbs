BEGIN;
CREATE TABLE `herbs_speciessynonym` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `json_content` longtext NOT NULL,
    `string_content` longtext NOT NULL,
    `rebuild_scheduled` bool NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;


ALTER TABLE `herbs_species` ADD COLUMN `synonym_id` integer;
ALTER TABLE `herbs_species` ADD COLUMN  `updated` date;

ALTER TABLE `herbs_species` ADD CONSTRAINT `synonym_id_refs_id_d1828e1f` FOREIGN KEY (`synonym_id`) REFERENCES `herbs_species` (`id`);
CREATE INDEX `herbs_species_ea815230` ON `herbs_species` (`synonym_id`);
COMMIT;


