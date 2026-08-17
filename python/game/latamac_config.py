# -*- coding: utf-8 -*-
# latamac_config.py - parametros latamac (recargable con !ac reload)
#
# Unica fuente de settings de !ac fool / !ac bait. Editar y !ac reload.

# --- !ac fool: grilla de kits bajo tierra (sin caja orbitando) ---
# Legacy (ya no se usan para fool; se mantienen por compat / hide de kits):
LATAMAC_FOOL_TEMPLATE = 'light_supply_crate'
LATAMAC_FOOL_HEAD_OFFSET_Y = 2.05
LATAMAC_FOOL_RADIUS = 1.5
LATAMAC_FOOL_SPIN_DEG_PER_SEC = 120.0
LATAMAC_FOOL_FOLLOW_SEC = 0.05
LATAMAC_FOOL_HIDE_Y = 9000.0
LATAMAC_FOOL_SPAWN_MODE = 'spawner'
LATAMAC_FOOL_SPAWN_COOLDOWN_SEC = 2.0
LATAMAC_FOOL_RESPAWN_SEC = 10.0
# Grilla de kits bajo tierra al !ac fool (no siguen al jugador).
LATAMAC_FOOL_KIT_GRID = True
# Cantidad de kits por bando (aliados y enemigos).
LATAMAC_FOOL_KIT_COUNT = 20
# Separacion entre kits en la grilla (metros).
LATAMAC_FOOL_KIT_SPACING = 2.5
# Profundidad bajo el jugador (metros).
LATAMAC_FOOL_KIT_BURY_Y = 30.0
# Columnas de la grilla (filas = ceil(count/cols)).
LATAMAC_FOOL_KIT_COLS = 5
# Separacion horizontal entre grilla aliada y enemiga (metros).
LATAMAC_FOOL_KIT_SIDE_GAP = 8.0
# Segundos hasta borrar los kits (0 = no expiran).
LATAMAC_FOOL_KIT_TTL_SEC = 30.0

# --- !ac bait: el admin sigue al sospechoso (honeypot ESP) ---
# under = bajo tierra (el motor suele empujar a superficie; se fuerza con rcon).
# sky   = arriba en el cielo (mas estable si under no aguanta).
LATAMAC_BAIT_MODE = 'under'
# Metros bajo el tramposo (modo under).
LATAMAC_BAIT_BURY_Y = 30.0
# Metros sobre el tramposo (modo sky).
LATAMAC_BAIT_SKY_Y = 80.0
# Intervalo de teletransporte forzado (mas bajo = pelea mejor al snap del terreno).
LATAMAC_BAIT_FOLLOW_SEC = 0.05
# Cuantas veces martillar setPosition+rcon por tick.
LATAMAC_BAIT_FORCE_HITS = 4
# Tolerancia de yaw al mirar al admin-cebo (grados).
LATAMAC_BAIT_LOOK_DEG = 18.0
# Segundos mirando el cebo antes de sumar score.
LATAMAC_BAIT_LOOK_HOLD_SEC = 0.8
# Cooldown entre scores bait_look del mismo jugador.
LATAMAC_BAIT_LOOK_COOLDOWN_SEC = 15.0
# Puntos AC al detectar mirada al cebo.
LATAMAC_BAIT_POINTS = 35
