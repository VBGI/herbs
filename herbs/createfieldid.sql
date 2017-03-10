BEGIN;
CREATE TABLE `herbs_subdivision` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(300) NOT NULL,
    `description` varchar(1000) NOT NULL,
    `allowed_users` varchar(1000) NOT NULL
) DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
ALTER TABLE `herbs_herbitem` ADD COLUMN `fieldid` varchar(20) NOT NULL;
ALTER TABLE `herbs_herbitem` ADD COLUMN `subdivision_id` integer;
ALTER TABLE `herbs_herbitem` ADD CONSTRAINT `subdivision_id_refs_id_3cb3b961` FOREIGN KEY (`subdivision_id`) REFERENCES `herbs_subdivision` (`id`);
CREATE INDEX `herbs_herbitem_a29c6eea` ON `herbs_herbitem` (`subdivision_id`);
COMMIT;
