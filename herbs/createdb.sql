BEGIN;
CREATE TABLE `herbs_additionals` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `herbitem_id` integer NOT NULL,
    `identifiedby` varchar(500) NOT NULL,
    `identified_s` date,
    `identified_e` date,
    `species_id` integer
)  DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_additionals` ADD CONSTRAINT `species_id_refs_id_8c3d2afc` FOREIGN KEY (`species_id`) REFERENCES `herbs_species` (`id`);
ALTER TABLE `herbs_additionals` ADD CONSTRAINT `herbitem_id_refs_id_8387f8df` FOREIGN KEY (`herbitem_id`) REFERENCES `herbs_herbitem` (`id`);
CREATE INDEX `herbs_additionals_40acd659` ON `herbs_additionals` (`herbitem_id`);
CREATE INDEX `herbs_additionals_e1800d51` ON `herbs_additionals` (`species_id`);
COMMIT;
