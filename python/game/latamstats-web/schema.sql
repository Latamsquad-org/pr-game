CREATE TABLE IF NOT EXISTS players (
  id INT AUTO_INCREMENT PRIMARY KEY,
  player_id VARCHAR(64) NOT NULL,
  player_name VARCHAR(128) NOT NULL DEFAULT '',
  player_clan VARCHAR(64) NOT NULL DEFAULT '',
  score INT NOT NULL DEFAULT 0,
  kills INT NOT NULL DEFAULT 0,
  deaths INT NOT NULL DEFAULT 0,
  rounds INT NOT NULL DEFAULT 0,
  treasures INT NOT NULL DEFAULT 0,
  created VARCHAR(32) NULL,
  seen VARCHAR(32) NULL,
  server_id VARCHAR(64) NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_player_id (player_id)
);

CREATE TABLE IF NOT EXISTS discord_users (
    discord_id VARCHAR(32) NOT NULL PRIMARY KEY,
    username VARCHAR(64) NOT NULL DEFAULT '',
    global_name VARCHAR(128) NOT NULL DEFAULT '',
    avatar_hash VARCHAR(128) NOT NULL DEFAULT '',
    access_token TEXT NULL,
    refresh_token TEXT NULL,
    token_expires_at INT NULL,
    is_staff TINYINT(1) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS player_links (
    id INT AUTO_INCREMENT PRIMARY KEY,
    discord_id VARCHAR(32) NOT NULL,
    player_id VARCHAR(64) NOT NULL,
    server_id VARCHAR(64) NOT NULL DEFAULT 'pr-1',
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_discord_server (discord_id, server_id),
    UNIQUE KEY uq_player_server_link (player_id, server_id),
    KEY idx_player_links_discord (discord_id)
);

CREATE TABLE IF NOT EXISTS link_codes (
    code VARCHAR(16) NOT NULL PRIMARY KEY,
    discord_id VARCHAR(32) NOT NULL,
    expires_at INT NOT NULL,
    created_at INT NOT NULL,
    KEY idx_link_codes_discord (discord_id)
);

CREATE TABLE IF NOT EXISTS player_profiles (
    player_id VARCHAR(64) NOT NULL,
    server_id VARCHAR(64) NOT NULL DEFAULT 'pr-1',
    bio VARCHAR(500) NOT NULL DEFAULT '',
    banner_path VARCHAR(255) NOT NULL DEFAULT '',
    show_discord TINYINT(1) NOT NULL DEFAULT 1,
    socials JSON NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, server_id)
);

CREATE TABLE IF NOT EXISTS clan_blurbs (
    clan_name VARCHAR(64) NOT NULL,
    server_id VARCHAR(64) NOT NULL DEFAULT 'pr-1',
    description TEXT NOT NULL,
    updated_by_discord_id VARCHAR(32) NOT NULL DEFAULT '',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (clan_name, server_id)
);

CREATE TABLE IF NOT EXISTS clan_editors (
    clan_name VARCHAR(64) NOT NULL,
    server_id VARCHAR(64) NOT NULL DEFAULT 'pr-1',
    discord_id VARCHAR(32) NOT NULL,
    granted_by VARCHAR(32) NOT NULL DEFAULT '',
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (clan_name, server_id, discord_id)
);
