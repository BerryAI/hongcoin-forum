

CREATE TABLE `user` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(80) NULL,
  `username` VARCHAR(45) NULL,
  `password_hash` VARCHAR(255) NULL,
  `creation_datetime` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `username_UNIQUE` (`username` ASC));

CREATE TABLE `user_address` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NULL,
  `wallet_address` VARCHAR(62) NULL,
  PRIMARY KEY (`id`));

CREATE TABLE `category` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NULL,
  `category_slug` VARCHAR(45) NULL,
  `description` VARCHAR(255) NULL,
  `rank` INT NULL,
  `is_public` TINYINT NULL,
  `fa_icon` VARCHAR(45) NULL,
  `icon_color` VARCHAR(50) NULL,
  PRIMARY KEY (`id`));

INSERT INTO `category` (`name`,`category_slug`,`description`,`rank`,`is_public`,`fa_icon`,`icon_color`) VALUES ('Announcement','announcement','Announcement from the Team',1,0,'fa-fw fa-bullhorn','#cf3a3a');
INSERT INTO `category` (`name`,`category_slug`,`description`,`rank`,`is_public`,`fa_icon`,`icon_color`) VALUES ('Forum Function','forum-function','Improve this forum together',2,1,'fa-fw fa-comment','#dea133');
INSERT INTO `category` (`name`,`category_slug`,`description`,`rank`,`is_public`,`fa_icon`,`icon_color`) VALUES ('Fund','fund','Ask fund-related question',3,1,'fa-fw fa-money','#5a81ef');
INSERT INTO `category` (`name`,`category_slug`,`description`,`rank`,`is_public`,`fa_icon`,`icon_color`) VALUES ('Future Projects','future-projects','Share with us any project you like!',4,1,'fa-fw fa-pagelines','#1a8d68');


CREATE TABLE `thread` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(255) NULL,
  `author_id` INT NULL,
  `category_id` INT NULL,
  `datetime` DATETIME NULL,
  `is_pinned` TINYINT NULL,
  `is_reported` TINYINT NULL,
  `is_closed` TINYINT NULL,
  `is_hidden` TINYINT NULL,
  PRIMARY KEY (`id`));

CREATE TABLE `post` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `author_id` INT NULL,
  `datetime` DATETIME NULL,
  `thread_id` INT NULL,
  `content` LONGTEXT NULL,
  `is_pinned` TINYINT NULL,
  `is_reported` TINYINT NULL,
  `is_hidden` TINYINT NULL,
  PRIMARY KEY (`id`));
