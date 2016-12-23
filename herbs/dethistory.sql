CREATE TABLE `herbs_dethistory` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `herbitem_id` integer NOT NULL,
    `identifiedby` varchar(500) NOT NULL,
    `identified_s` date,
    `identified_e` date,
    `species_id` integer
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_dethistory` ADD CONSTRAINT `species_id_refs_id_3219d53b` FOREIGN KEY (`species_id`) REFERENCES `herbs_species` (`id`);
ALTER TABLE `herbs_dethistory` ADD CONSTRAINT `herbitem_id_refs_id_c31377b3` FOREIGN KEY (`herbitem_id`) REFERENCES `herbs_herbitem` (`id`);
CREATE INDEX `herbs_dethistory_40acd659` ON `herbs_dethistory` (`herbitem_id`);
CREATE INDEX `herbs_dethistory_e1800d51` ON `herbs_dethistory` (`species_id`);
 
