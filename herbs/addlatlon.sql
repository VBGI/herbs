BEGIN;
ALTER TABLE `herbs_herbitem` ADD COLUMN `latitude` double precision;
ALTER TABLE `herbs_herbitem` ADD COLUMN `longitude` double precision;
COMMIT;
