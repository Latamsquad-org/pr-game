from collections import OrderedDict
NONE = 0
AIR = 1
LAND = 2
SEA = 3
SUP = 4
SPEC = 5
OFFIC = 6
ENG = 7
CMDR = 8
DOWNWARDS = -1
UPWARDS = 1
Top = 0
Middle = 1
Bottom = 2
DRIVER = 0
GUNNER = 1
PASSENGER = 2
COMMANDER = 1
SQUADLEADER = 2
SQUADMEMBER = 3
LONEWOLF = 4
TAKEOVERTYPE_CAPTURE = 1
TAKEOVERTYPE_NEUTRALIZE = 2
HUGE_TTS = 6000
TINY = 0
SMALL = 1
MEDIUM = 2
BIG = 3
HUGE = 4
INSANE = 5
ASSET_DUMMY_TTL = 3
DISTANCE_PICKUP = 5
DISTANCE_SPAWN = 10
DEPOT_KIT_DISTANCE = 10
DEPOT_KIT_DISTANCE_WW2 = 15
DISTANCE_CLOSE_OUTPOST = 90
DISTANCE_NEAR = 25
DISTANCE_CLOSE = 50
DISTANCE_AREA = 100
DISTANCE_AREA_SMALL = 40
DISTANCE_AREA_BIG = 75
DISTANCE_AREA_HUGE = 150
DISTANCE_AREA_ZOOM_FACTOR = 0.4
DISTANCE_WIDE = 200
DISTANCE_HUGE = 300
VEHICLE_TYPE_UNKNOWN = 0
VEHICLE_TYPE_ARMOR = 1
VEHICLE_TYPE_AAV = 2
VEHICLE_TYPE_APC = 3
VEHICLE_TYPE_IFV = 4
VEHICLE_TYPE_JET = 5
VEHICLE_TYPE_HELI = 6
VEHICLE_TYPE_HELIATTACK = 7
VEHICLE_TYPE_TRANSPORT = 8
VEHICLE_TYPE_RECON = 9
VEHICLE_TYPE_STATIC = 10
VEHICLE_TYPE_SOLDIER = 11
VEHICLE_TYPE_ASSET = 12
VEHICLE_TYPE_OBJECTIVE = 13
VEHICLE_TYPE_TURBOPROP = 14
VEHICLE_TYPE_AFV = 15
VEHICLE_TYPE_ALC = 16
VEHICLE_TYPE_UAV = 17
VEHICLE_TYPE_FREE = 18
WEAPON_TYPE_ASSAULT = 0
WEAPON_TYPE_ASSAULTGRN = 1
WEAPON_TYPE_CARBINE = 2
WEAPON_TYPE_LMG = 3
WEAPON_TYPE_SNIPER = 4
WEAPON_TYPE_PISTOL = 5
WEAPON_TYPE_ATAA = 6
WEAPON_TYPE_SMG = 7
WEAPON_TYPE_SHOTGUN = 8
WEAPON_TYPE_KNIFE = 10
WEAPON_TYPE_C4 = 11
WEAPON_TYPE_CLAYMORE = 12
WEAPON_TYPE_HANDGRENADE = 13
WEAPON_TYPE_SHOCKPAD = 14
WEAPON_TYPE_ATMINE = 15
WEAPON_TYPE_TARGETING = 16
WEAPON_TYPE_GRAPPLINGHOOK = 17
WEAPON_TYPE_ZIPLINE = 18
WEAPON_TYPE_TACTICAL = 19
NUM_WEAPON_TYPES = 20
WEAPON_TYPE_UNKNOWN = NUM_WEAPON_TYPES
KIT_TYPE_AT = 0
KIT_TYPE_ASSAULT = 1
KIT_TYPE_ENGINEER = 2
KIT_TYPE_MEDIC = 3
KIT_TYPE_SPECOPS = 4
KIT_TYPE_SUPPORT = 5
KIT_TYPE_SNIPER = 6
KIT_TYPE_AA = KIT_TYPE_AT
KIT_TYPE_PILOT = KIT_TYPE_ENGINEER
KIT_TYPE_CREWMAN = KIT_TYPE_ENGINEER
KIT_TYPE_OFFICER = KIT_TYPE_ASSAULT
KIT_TYPE_MARKSMAN = KIT_TYPE_SNIPER
NUM_KIT_TYPES = 7
KIT_TYPE_UNKNOWN = NUM_KIT_TYPES
ARMY_USA = 0
ARMY_MEC = 1
ARMY_CHINESE = 2
ARMY_SEALS = 3
ARMY_SAS = 4
ARMY_SPETZNAS = 5
ARMY_MECSF = 6
ARMY_REBELS = 7
ARMY_INSURGENTS = 8
ARMY_EURO = 9
ARMY_BRITS = 10
ARMY_CANADA = 11
ARMY_GERMAN = 12
NUM_ARMIES = 13
ARMY_UNKNOWN = NUM_ARMIES
GPM_CQ = 0
GPM_SL = 1
GPM_AAS = 2
GPM_SOBJ = 3
GPM_XTRACT = 4
GPM_SCENARIO = 5
GPM_INSURGENCY = 6
GPM_COUNTER = 7
GPM_SKIRMISH = 8
GPM_TRAINING = 9
GPM_CNC = 10
UNKNOWN_GAMEMODE = 99
vehicleTypeMap = OrderedDict([('cargoship_atlantic_conveyor', VEHICLE_TYPE_OBJECTIVE),
 ('_obj_', VEHICLE_TYPE_OBJECTIVE),
 ('_jet_a1h', VEHICLE_TYPE_TURBOPROP),
 ('_jet_bf109g6', VEHICLE_TYPE_TURBOPROP),
 ('_jet_p51d', VEHICLE_TYPE_TURBOPROP),
 ('_jet_i16', VEHICLE_TYPE_TURBOPROP),
 ('_jet_il2', VEHICLE_TYPE_TURBOPROP),
 ('_jet_il2m', VEHICLE_TYPE_TURBOPROP),
 ('_jet_la5fn', VEHICLE_TYPE_TURBOPROP),
 ('_atm_technical', VEHICLE_TYPE_APC),
 ('_apc_mtlb_30mm', VEHICLE_TYPE_APC),
 ('_apc_fuchs', VEHICLE_TYPE_AFV),
 ('_apc_mtlb', VEHICLE_TYPE_APC),
 ('_apc_boragh', VEHICLE_TYPE_AFV),
 ('_apc_m113', VEHICLE_TYPE_AFV),
 ('_apc_m3', VEHICLE_TYPE_AFV),
 ('_apc_m113_logistics', VEHICLE_TYPE_ALC),
 ('_apc_mtplb', VEHICLE_TYPE_ALC),
 ('_apc_acav', VEHICLE_TYPE_AFV),
 ('_apc_ypr50', VEHICLE_TYPE_AFV),
 ('_apc_vab', VEHICLE_TYPE_AFV),
 ('_apc_wz551a', VEHICLE_TYPE_AFV),
 ('_apc_251c', VEHICLE_TYPE_AFV),
 ('_ifv_scimitar', VEHICLE_TYPE_APC),
 ('_ifv_scorpion', VEHICLE_TYPE_APC),
 ('_ifv_coyote', VEHICLE_TYPE_APC),
 ('_jep_vn3', VEHICLE_TYPE_APC),
 ('_jep_fennek', VEHICLE_TYPE_APC),
 ('_shp_pbr', VEHICLE_TYPE_APC),
 ('_tnk_', VEHICLE_TYPE_ARMOR),
 ('_aav_', VEHICLE_TYPE_AAV),
 ('_apc_', VEHICLE_TYPE_APC),
 ('_ifv_', VEHICLE_TYPE_IFV),
 ('_atm_', VEHICLE_TYPE_IFV),
 ('_jet_', VEHICLE_TYPE_JET),
 ('_the_', VEHICLE_TYPE_HELI),
 ('_ahe_', VEHICLE_TYPE_HELIATTACK),
 ('_jep_', VEHICLE_TYPE_TRANSPORT),
 ('_jep_brdm2', VEHICLE_TYPE_TRANSPORT),
 ('_trk_', VEHICLE_TYPE_TRANSPORT),
 ('_civ_', VEHICLE_TYPE_TRANSPORT),
 ('_bik_', VEHICLE_TYPE_TRANSPORT),
 ('_shp_', VEHICLE_TYPE_TRANSPORT),
 ('boat', VEHICLE_TYPE_FREE),
 ('soldier', VEHICLE_TYPE_SOLDIER),
 ('commandpost', VEHICLE_TYPE_ASSET),
 ('rallypoint', VEHICLE_TYPE_ASSET),
 ('firebase', VEHICLE_TYPE_ASSET),
 ('bunker', VEHICLE_TYPE_ASSET),
 ('hideout', VEHICLE_TYPE_ASSET),
 ('acv', VEHICLE_TYPE_ASSET),
 ('ru_ship_andreev_lpd_atc', VEHICLE_TYPE_ASSET),
 ('deployable', VEHICLE_TYPE_STATIC),
 ('ats', VEHICLE_TYPE_STATIC),
 ('bipod', VEHICLE_TYPE_STATIC),
 ('hmg', VEHICLE_TYPE_STATIC),
 ('djigit', VEHICLE_TYPE_STATIC),
 ('stinger', VEHICLE_TYPE_STATIC),
 ('zis', VEHICLE_TYPE_STATIC),
 ('zpu', VEHICLE_TYPE_STATIC),
 ('uav', VEHICLE_TYPE_UAV)])
weaponTypeMap = {'50cal_bullets_vab': WEAPON_TYPE_LMG,
 '50cal_gau16': WEAPON_TYPE_LMG,
 '50cal_m2hb': WEAPON_TYPE_LMG,
 '50cal_m2hb_crows': WEAPON_TYPE_LMG,
 '50cal_m3m': WEAPON_TYPE_LMG,
 'aa_m167_barrells_genericfirearm': WEAPON_TYPE_ATAA,
 'aa_m167_m61': WEAPON_TYPE_ATAA,
 'aas_phalanx': WEAPON_TYPE_ATAA,
 'aas_seasparrow': WEAPON_TYPE_ATAA,
 'agl_mk19_ammo': WEAPON_TYPE_ASSAULTGRN,
 'ammo_belt_50cal': WEAPON_TYPE_LMG,
 'ammo_belt_7-62mm_long': WEAPON_TYPE_LMG,
 'ammo_belt_7-62mm_long_gwagon': WEAPON_TYPE_LMG,
 'ammokit': WEAPON_TYPE_TACTICAL,
 'argmin_fmk1': WEAPON_TYPE_CLAYMORE,
 'argmin_fmk_linked': WEAPON_TYPE_CLAYMORE,
 'argmin_fmk3': WEAPON_TYPE_ATMINE,
 'argmin_fmk3_projectile': WEAPON_TYPE_ATMINE,
 'argrif_fmfal': WEAPON_TYPE_CARBINE,
 'argrif_ml63': WEAPON_TYPE_SMG,
 'ars_d30_barrel': WEAPON_TYPE_ATAA,
 'artillery_team1_barrel': WEAPON_TYPE_ATAA,
 'artillery_team2_barrel': WEAPON_TYPE_ATAA,
 'arty_ied': WEAPON_TYPE_C4,
 'at_mine': WEAPON_TYPE_ATMINE,
 'at_mine_projectile': WEAPON_TYPE_ATMINE,
 'ats_hj8_launcher': WEAPON_TYPE_ATAA,
 'ats_spg9_launcher_frag': WEAPON_TYPE_ATAA,
 'ats_spg9_vehicle_launcher_frag': WEAPON_TYPE_ATAA,
 'ats_tow_launcher': WEAPON_TYPE_ATAA,
 'auxgun': WEAPON_TYPE_LMG,
 'binocular': WEAPON_TYPE_TARGETING,
 'binocular_green': WEAPON_TYPE_TARGETING,
 'binocular_officer': WEAPON_TYPE_TACTICAL,
 'bipod_gpmg_c6_weapon': WEAPON_TYPE_LMG,
 'bipod_gpmg_l7a2_weapon': WEAPON_TYPE_LMG,
 'bipod_gpmg_m240b_elcan_weapon': WEAPON_TYPE_LMG,
 'bipod_gpmg_m240b_weapon': WEAPON_TYPE_LMG,
 'bow_mg_bmp3': WEAPON_TYPE_LMG,
 'brdmcoax': WEAPON_TYPE_LMG,
 'brrif_fnfal': WEAPON_TYPE_ASSAULT,
 'c4_carbomber': WEAPON_TYPE_C4,
 'c4_explosives': WEAPON_TYPE_C4,
 'c4_large': WEAPON_TYPE_C4,
 'c4_large_idx6': WEAPON_TYPE_C4,
 'c4_large_ru': WEAPON_TYPE_C4,
 'c4_large_ru_idx6': WEAPON_TYPE_C4,
 'c4_smallexplosives': WEAPON_TYPE_C4,
 'c4_smallexplosives_q4': WEAPON_TYPE_C4,
 'cfhgr_c13': WEAPON_TYPE_HANDGRENADE,
 'cfhgr_c13_q4': WEAPON_TYPE_HANDGRENADE,
 'cflat_m72a7': WEAPON_TYPE_ATAA,
 'cflmg_c9': WEAPON_TYPE_LMG,
 'cflmg_c9_stationary': WEAPON_TYPE_LMG,
 'cflmg_c9deployed': WEAPON_TYPE_LMG,
 'cflmg_c9elcan': WEAPON_TYPE_LMG,
 'cflmg_c9elcandeployed': WEAPON_TYPE_LMG,
 'cfmmg_c6': WEAPON_TYPE_LMG,
 'cfrgl_c7scopeugl': WEAPON_TYPE_ASSAULTGRN,
 'cfrgl_c7scopeugl_smoke': WEAPON_TYPE_ASSAULTGRN,
 'cfrgl_c8a3eotechugl': WEAPON_TYPE_ASSAULTGRN,
 'cfrgl_c8a3eotechugl_smoke': WEAPON_TYPE_ASSAULTGRN,
 'cfrif_ar10t': WEAPON_TYPE_SNIPER,
 'cfrif_ar10tdeployed': WEAPON_TYPE_SNIPER,
 'cfrif_ar10telcan': WEAPON_TYPE_SNIPER,
 'cfrif_ar10telcandeployed': WEAPON_TYPE_SNIPER,
 'cfrif_c7eotech': WEAPON_TYPE_ASSAULT,
 'cfrif_c7eotech_6': WEAPON_TYPE_ASSAULT,
 'cfrif_c7iron': WEAPON_TYPE_ASSAULT,
 'cfrif_c7iron_6': WEAPON_TYPE_ASSAULT,
 'cfrif_c7scope': WEAPON_TYPE_ASSAULT,
 'cfrif_c7scopeugl': WEAPON_TYPE_ASSAULT,
 'cfrif_c8a3eotech': WEAPON_TYPE_ASSAULT,
 'cfrif_c8a3eotech_6': WEAPON_TYPE_ASSAULT,
 'cfrif_c8a3eotechugl': WEAPON_TYPE_ASSAULT,
 'cfrif_c8a3scope': WEAPON_TYPE_ASSAULT,
 'cfrif_c8a3scope_6': WEAPON_TYPE_ASSAULT,
 'cfsni_c14': WEAPON_TYPE_SNIPER,
 'chaa_qw2': WEAPON_TYPE_ATAA,
 'chat_eryx': WEAPON_TYPE_ATAA,
 'chat_pf98': WEAPON_TYPE_ATAA,
 'chhgr_type82': WEAPON_TYPE_HANDGRENADE,
 'chhgr_type82_projectile': WEAPON_TYPE_HANDGRENADE,
 'chhgr_type82_q4': WEAPON_TYPE_HANDGRENADE,
 'chhmg_kord': WEAPON_TYPE_LMG,
 'chhmg_kord_air': WEAPON_TYPE_LMG,
 'chhmg_type85': WEAPON_TYPE_LMG,
 'chhmg_type85_air': WEAPON_TYPE_LMG,
 'chhmg_type85_type98': WEAPON_TYPE_LMG,
 'chkni_qbz95ironbayonet': WEAPON_TYPE_KNIFE,
 'chkni_qbz95scopebayonet': WEAPON_TYPE_KNIFE,
 'chlat_pf89': WEAPON_TYPE_ATAA,
 'chlat_pf89_projectile': WEAPON_TYPE_ATAA,
 'chlmg_qbb95': WEAPON_TYPE_LMG,
 'chlmg_qbb95deployed': WEAPON_TYPE_LMG,
 'chlmg_qbb95scope': WEAPON_TYPE_LMG,
 'chlmg_qbb95scopedeployed': WEAPON_TYPE_LMG,
 'chlmg_type95_stationary': WEAPON_TYPE_ATAA,
 'chmin_type66': WEAPON_TYPE_CLAYMORE,
 'chmin_type66_sec': WEAPON_TYPE_ATMINE,
 'chpis_qsz92': WEAPON_TYPE_PISTOL,
 'chrgl_qbz95ironugl': WEAPON_TYPE_ASSAULTGRN,
 'chrgl_qbz95ironugl_smoke': WEAPON_TYPE_ASSAULTGRN,
 'chrgl_qbz95ugl': WEAPON_TYPE_ASSAULTGRN,
 'chrgl_qbz95ugl_smoke': WEAPON_TYPE_ASSAULTGRN,
 'chrif_qbu88': WEAPON_TYPE_SNIPER,
 'chrif_qbu88deployed': WEAPON_TYPE_SNIPER,
 'chrif_qbu88iron': WEAPON_TYPE_SNIPER,
 'chrif_qbu88irondeployed': WEAPON_TYPE_SNIPER,
 'chrif_qbz95b': WEAPON_TYPE_ASSAULT,
 'chrif_qbz95iron': WEAPON_TYPE_ASSAULT,
 'chrif_qbz95iron_6': WEAPON_TYPE_ASSAULT,
 'chrif_qbz95ironugl': WEAPON_TYPE_ASSAULT,
 'chrif_qbz95scope': WEAPON_TYPE_ASSAULT,
 'chrif_qbz95ugl': WEAPON_TYPE_ASSAULT,
 'chrif_type56': WEAPON_TYPE_ASSAULT,
 'chrif_type56_1': WEAPON_TYPE_ASSAULT,
 'chrif_type56_1_4': WEAPON_TYPE_ASSAULT,
 'chrif_type56_1_tracer': WEAPON_TYPE_ASSAULT,
 'chrif_type56_tracer': WEAPON_TYPE_ASSAULT,
 'chsht_norinco982': WEAPON_TYPE_SHOTGUN,
 'coaxial_browning': WEAPON_TYPE_LMG,
 'coaxial_browning_amx10rc': WEAPON_TYPE_LMG,
 'coaxial_browning_apc': WEAPON_TYPE_LMG,
 'coaxial_browning_apc_warrior': WEAPON_TYPE_LMG,
 'coaxial_browning_challenger': WEAPON_TYPE_LMG,
 'coaxial_browning_coyote': WEAPON_TYPE_LMG,
 'coaxial_browning_lav25': WEAPON_TYPE_LMG,
 'coaxial_browning_laviii': WEAPON_TYPE_LMG,
 'coaxial_browning_m2a2': WEAPON_TYPE_LMG,
 'coaxial_browning_merkava': WEAPON_TYPE_LMG,
 'coaxial_browning_scimitar': WEAPON_TYPE_LMG,
 'coaxial_m73_m48a1': WEAPON_TYPE_LMG,
 'coaxial_mg_bmp2': WEAPON_TYPE_LMG,
 'coaxial_mg_bmp3': WEAPON_TYPE_LMG,
 'coaxial_mg_china': WEAPON_TYPE_LMG,
 'coaxial_mg_china_apc': WEAPON_TYPE_LMG,
 'coaxial_mg_mec': WEAPON_TYPE_LMG,
 'coaxial_mg_mec_apc': WEAPON_TYPE_LMG,
 'coaxial_mg_pt76': WEAPON_TYPE_LMG,
 'coaxial_mg_scorpion': WEAPON_TYPE_LMG,
 'coaxial_mg_t62': WEAPON_TYPE_LMG,
 'coaxial_mg_t90': WEAPON_TYPE_LMG,
 'coaxial_mg3_nato': WEAPON_TYPE_LMG,
 'coaxial_mg4': WEAPON_TYPE_LMG,
 'csb_drop_truck_arg': WEAPON_TYPE_TACTICAL,
 'csb_drop_truck_cf': WEAPON_TYPE_TACTICAL,
 'csb_drop_truck_ch': WEAPON_TYPE_TACTICAL,
 'csb_drop_truck_fr': WEAPON_TYPE_TACTICAL,
 'csb_drop_truck_gb': WEAPON_TYPE_TACTICAL,
 'csb_drop_truck_ger': WEAPON_TYPE_TACTICAL,
 'csb_drop_truck_idf': WEAPON_TYPE_TACTICAL,
 'csb_drop_truck_mec': WEAPON_TYPE_TACTICAL,
 'csb_drop_truck_nl': WEAPON_TYPE_TACTICAL,
 'csb_drop_truck_pl': WEAPON_TYPE_TACTICAL,
 'csb_drop_truck_ru': WEAPON_TYPE_TACTICAL,
 'csb_drop_truck_us': WEAPON_TYPE_TACTICAL,
 'decoy_flare_launcher': WEAPON_TYPE_TACTICAL,
 'decoy_flare_launcher_group': WEAPON_TYPE_TACTICAL,
 'dynamite': WEAPON_TYPE_C4,
 'dynamite_detonator': WEAPON_TYPE_C4,
 'dynamite_small': WEAPON_TYPE_C4,
 'dynamite_small_q4': WEAPON_TYPE_C4,
 'emptyhands': WEAPON_TYPE_TACTICAL,
 'epipen': WEAPON_TYPE_SHOCKPAD,
 'epipen_idx6': WEAPON_TYPE_SHOCKPAD,
 'f1grenade': WEAPON_TYPE_HANDGRENADE,
 'f1grenade_projectile': WEAPON_TYPE_HANDGRENADE,
 'f1grenade_q1': WEAPON_TYPE_HANDGRENADE,
 'f1grenade_q4': WEAPON_TYPE_HANDGRENADE,
 'f1grenade_q6': WEAPON_TYPE_HANDGRENADE,
 'firingport_ak': WEAPON_TYPE_ASSAULT,
 'firingport_m231': WEAPON_TYPE_LMG,
 'flaregun': WEAPON_TYPE_PISTOL,
 'fr_ats_milan_launcher': WEAPON_TYPE_ATAA,
 'frclmg_m60_m548a1': WEAPON_TYPE_LMG,
 'frclmg_m60_rib': WEAPON_TYPE_LMG,
 'frcmg_m60': WEAPON_TYPE_LMG,
 'frcmg_m60_stationary_ammoboxless': WEAPON_TYPE_LMG,
 'frhgr_of37': WEAPON_TYPE_HANDGRENADE,
 'frhgr_of37_projectile': WEAPON_TYPE_HANDGRENADE,
 'frhgr_smoke': WEAPON_TYPE_HANDGRENADE,
 'frhgr_smoke_projectile': WEAPON_TYPE_HANDGRENADE,
 'frhgr_smoke_q4': WEAPON_TYPE_HANDGRENADE,
 'frkni_bayonet': WEAPON_TYPE_KNIFE,
 'frkni_famasaimpointbayonet': WEAPON_TYPE_KNIFE,
 'frkni_famasironbayonet': WEAPON_TYPE_KNIFE,
 'frkni_famasscopebayonet': WEAPON_TYPE_KNIFE,
 'frlat_abl': WEAPON_TYPE_ATAA,
 'frlmg_anf1': WEAPON_TYPE_LMG,
 'frlmg_anf1_mounted': WEAPON_TYPE_LMG,
 'frlmg_minimieotech': WEAPON_TYPE_LMG,
 'frlmg_minimieotechdeployed': WEAPON_TYPE_LMG,
 'frlmg_minimij4': WEAPON_TYPE_LMG,
 'frlmg_minimij4deployed': WEAPON_TYPE_LMG,
 'frpis_pamasg1': WEAPON_TYPE_PISTOL,
 'frrgl_famas_ap': WEAPON_TYPE_ASSAULTGRN,
 'frrgl_famas_ap_projectile': WEAPON_TYPE_ASSAULTGRN,
 'frrgl_famas_at': WEAPON_TYPE_ASSAULTGRN,
 'frrgl_famas_at_projectile': WEAPON_TYPE_ASSAULTGRN,
 'frrgl_famas_smoke': WEAPON_TYPE_ASSAULTGRN,
 'frrgl_famas_smoke_projectile': WEAPON_TYPE_ASSAULTGRN,
 'frrif_famasaimpoint': WEAPON_TYPE_ASSAULT,
 'frrif_famasaimpoint_6': WEAPON_TYPE_ASSAULT,
 'frrif_famaseotech': WEAPON_TYPE_ASSAULT,
 'frrif_famasiron': WEAPON_TYPE_ASSAULT,
 'frrif_famasiron_6': WEAPON_TYPE_ASSAULT,
 'frrif_famasironugl': WEAPON_TYPE_ASSAULT,
 'frrif_famasscope': WEAPON_TYPE_ASSAULT,
 'frrif_hk417': WEAPON_TYPE_SNIPER,
 'frrif_hk417deployed': WEAPON_TYPE_SNIPER,
 'frrif_hk417eotech': WEAPON_TYPE_SNIPER,
 'frrif_hk417eotechdeployed': WEAPON_TYPE_SNIPER,
 'frsht_mossberg590': WEAPON_TYPE_SHOTGUN,
 'frsni_frf2': WEAPON_TYPE_SNIPER,
 'fusrodah': WEAPON_TYPE_UNKNOWN,
 'gbaa_blowpipe': WEAPON_TYPE_ATAA,
 'gbat_law66': WEAPON_TYPE_ATAA,
 'gbat_nlaw': WEAPON_TYPE_ATAA,
 'gbhgr_l109': WEAPON_TYPE_HANDGRENADE,
 'gbhgr_l109_projectile': WEAPON_TYPE_HANDGRENADE,
 'gbhgr_l109_q4': WEAPON_TYPE_HANDGRENADE,
 'gblat_l2a1': WEAPON_TYPE_ATAA,
 'gbhgr_l2a2': WEAPON_TYPE_HANDGRENADE,
 'gbkni_l85a2acogbayonet': WEAPON_TYPE_KNIFE,
 'gbkni_l85a2ironbayonet': WEAPON_TYPE_KNIFE,
 'gbkni_l85a2susatbayonet': WEAPON_TYPE_KNIFE,
 'gblmg_l4bren': WEAPON_TYPE_LMG,
 'gblmg_l4brendeployed': WEAPON_TYPE_LMG,
 'gblmg_minimi': WEAPON_TYPE_LMG,
 'gblmg_minimi_stationary': WEAPON_TYPE_LMG,
 'gblmg_minimideployed': WEAPON_TYPE_LMG,
 'gblmg_minimisusat': WEAPON_TYPE_LMG,
 'gblmg_minimisusatdeployed': WEAPON_TYPE_LMG,
 'gbmmg_gpmg': WEAPON_TYPE_LMG,
 'gbpis_glock17': WEAPON_TYPE_PISTOL,
 'gbpis_l9': WEAPON_TYPE_PISTOL,
 'gbrgl_l85a2ag36': WEAPON_TYPE_ASSAULTGRN,
 'gbrgl_l85a2ag36_smoke': WEAPON_TYPE_ASSAULTGRN,
 'gbrgl_l85a2ironag36': WEAPON_TYPE_ASSAULTGRN,
 'gbrgl_l85a2ironag36_smoke': WEAPON_TYPE_ASSAULTGRN,
 'gbrif_enfieldno1mk3': WEAPON_TYPE_CARBINE,
 'gbrif_enfieldno4': WEAPON_TYPE_CARBINE,
 'gbrif_l1a1': WEAPON_TYPE_ASSAULT,
 'gbrif_l1a1suit': WEAPON_TYPE_ASSAULT,
 'gbrif_l22a2susat': WEAPON_TYPE_ASSAULT,
 'gbrif_l85a2acog': WEAPON_TYPE_ASSAULT,
 'gbrif_l85a2ag36': WEAPON_TYPE_ASSAULT,
 'gbrif_l85a2iron': WEAPON_TYPE_ASSAULT,
 'gbrif_l85a2iron_6': WEAPON_TYPE_ASSAULT,
 'gbrif_l85a2ironag36': WEAPON_TYPE_ASSAULT,
 'gbrif_l85a2susat': WEAPON_TYPE_ASSAULT,
 'gbrif_l85a2susat_6': WEAPON_TYPE_ASSAULT,
 'gbrif_l86': WEAPON_TYPE_SNIPER,
 'gbrif_l86deployed': WEAPON_TYPE_SNIPER,
 'gbrif_l86iron': WEAPON_TYPE_SNIPER,
 'gbrif_l86irondeployed': WEAPON_TYPE_SNIPER,
 'gbrif_sterling': WEAPON_TYPE_SMG,
 'gbsht_l128a1': WEAPON_TYPE_SHOTGUN,
 'gbsht_l128a1slug': WEAPON_TYPE_SHOTGUN,
 'gbsni_enfieldno1mk3': WEAPON_TYPE_SNIPER,
 'gbsni_enfieldno4': WEAPON_TYPE_SNIPER,
 'gbsni_l115a3': WEAPON_TYPE_SNIPER,
 'gbsni_l42a1': WEAPON_TYPE_SNIPER,
 'ger_at_pars3lr': WEAPON_TYPE_ATAA,
 'ger_at_pars3lr_laser': WEAPON_TYPE_ATAA,
 'ger_at_pars3lr_tv': WEAPON_TYPE_ATAA,
 'ger_at_spike': WEAPON_TYPE_ATAA,
 'ger_bipod': WEAPON_TYPE_LMG,
 'gerat_pzf3': WEAPON_TYPE_ATAA,
 'gerat_pzf3_rocket': WEAPON_TYPE_ATAA,
 'gergl_g36ugl': WEAPON_TYPE_ASSAULTGRN,
 'gergl_g36ugl_flare': WEAPON_TYPE_ASSAULTGRN,
 'gergl_g36ugl_smoke': WEAPON_TYPE_ASSAULTGRN,
 'gerhgr_dm51': WEAPON_TYPE_HANDGRENADE,
 'gerhgr_dm51_projectile': WEAPON_TYPE_HANDGRENADE,
 'gerhgr_dm51_q4': WEAPON_TYPE_HANDGRENADE,
 'gerkni_km2000': WEAPON_TYPE_KNIFE,
 'gerlat_pzf3': WEAPON_TYPE_ATAA,
 'gerlat_pzf3_rocket': WEAPON_TYPE_ATAA,
 'gerlmg_mg3_mounted': WEAPON_TYPE_LMG,
 'gerlmg_mg3_nostock': WEAPON_TYPE_LMG,
 'gerlmg_mg3_stationary': WEAPON_TYPE_LMG,
 'gerlmg_mg4': WEAPON_TYPE_LMG,
 'gerlmg_mg4deployed': WEAPON_TYPE_LMG,
 'gerlmg_mg4zpoint': WEAPON_TYPE_LMG,
 'gerlmg_mg4zpointdeployed': WEAPON_TYPE_LMG,
 'germmg_mg3': WEAPON_TYPE_LMG,
 'gerpis_p8': WEAPON_TYPE_PISTOL,
 'gerrif_g3zpoint': WEAPON_TYPE_ASSAULT,
 'gerrif_g3zpoint_4': WEAPON_TYPE_ASSAULT,
 'gerrif_g36kscope': WEAPON_TYPE_ASSAULT,
 'gerrif_g36kscope_6': WEAPON_TYPE_ASSAULT,
 'gerrif_g36scope': WEAPON_TYPE_ASSAULT,
 'gerrif_g36scope_6': WEAPON_TYPE_ASSAULT,
 'gerrif_g36scopeugl': WEAPON_TYPE_ASSAULT,
 'gerrif_mp7': WEAPON_TYPE_SMG,
 'gerrif_stg44': WEAPON_TYPE_ASSAULT,
 'gersni_g22': WEAPON_TYPE_SNIPER,
 'gpmg_c6': WEAPON_TYPE_LMG,
 'gpmg_c6_spade': WEAPON_TYPE_LMG,
 'gpmg_l7a2': WEAPON_TYPE_LMG,
 'gpmg_m60d': WEAPON_TYPE_LMG,
 'gpmg_m240b': WEAPON_TYPE_LMG,
 'gpmg_m240b_hmmwv': WEAPON_TYPE_LMG,
 'gpmg_m240d': WEAPON_TYPE_LMG,
 'hf7d_rocket': WEAPON_TYPE_ATAA,
 'hf25_rocket': WEAPON_TYPE_ATAA,
 'hgr_rdg2': WEAPON_TYPE_HANDGRENADE,
 'hgr_rdg2_idx4': WEAPON_TYPE_HANDGRENADE,
 'hgr_rdg2_q1': WEAPON_TYPE_HANDGRENADE,
 'hgr_rdg2_q4': WEAPON_TYPE_HANDGRENADE,
 'hgr_rkg3': WEAPON_TYPE_HANDGRENADE,
 'hgr_rkg3_idx5': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_idx4': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_ninja': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_ninja_projectile': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_ninja2': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_ninja2_projectile': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_projectile': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_q4': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_signal': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_signal_projectile': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_signalblue': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_signalbrown': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_signalgreen': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_signalorange': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_signalpurple': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_signalyellow': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_vietnam': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_vietnam_projectile': WEAPON_TYPE_HANDGRENADE,
 'hgr_smoke_vietnam_q4': WEAPON_TYPE_HANDGRENADE,
 'hmg_m134_chinook_gun': WEAPON_TYPE_LMG,
 'hmg_m134_gun': WEAPON_TYPE_LMG,
 'hmg_m134_huey_gun': WEAPON_TYPE_LMG,
 'hmg_m134_stationary_gun': WEAPON_TYPE_LMG,
 'hmg_m2hb': WEAPON_TYPE_LMG,
 'hmg_m2hb_ammo': WEAPON_TYPE_LMG,
 'hmg_nsvt': WEAPON_TYPE_LMG,
 'hmg_qjc88': WEAPON_TYPE_LMG,
 'hmg_qjc88_type99': WEAPON_TYPE_LMG,
 'hydra_70': WEAPON_TYPE_ATAA,
 'insgr_hgr_trap_projectile': WEAPON_TYPE_CLAYMORE,
 'plaa_grom': WEAPON_TYPE_ATAA,
 'plat_rpg7wmt_ko7m': WEAPON_TYPE_ATAA,
 'plat_rpg7wmt_pg7mt': WEAPON_TYPE_ATAA,
 'plat_spike': WEAPON_TYPE_ATAA,
 'plhgr_rgo88': WEAPON_TYPE_HANDGRENADE,
 'plhgr_rgo88_projectile': WEAPON_TYPE_HANDGRENADE,
 'plhgr_ugd200': WEAPON_TYPE_HANDGRENADE,
 'plhgr_ugd200_projectile': WEAPON_TYPE_HANDGRENADE,
 'plhgr_ugd200red': WEAPON_TYPE_HANDGRENADE,
 'plhgr_ugd200red_projectile': WEAPON_TYPE_HANDGRENADE,
 'plkni_wz92': WEAPON_TYPE_KNIFE,
 'pllat_rpg7w2_pg7m': WEAPON_TYPE_ATAA,
 'plmg_ukm2000': WEAPON_TYPE_LMG,
 'plmg_ukm2000scope': WEAPON_TYPE_LMG,
 'plpis_wist94': WEAPON_TYPE_PISTOL,
 'plrgl_berylgbpo40eotech': WEAPON_TYPE_ASSAULTGRN,
 'plrgl_berylgbpo40eotech_flare': WEAPON_TYPE_ASSAULTGRN,
 'plrgl_berylgbpo40eotech_smoke': WEAPON_TYPE_ASSAULTGRN,
 'plrgl_berylpalladeomgn': WEAPON_TYPE_ASSAULTGRN,
 'plrif_beryl_mini': WEAPON_TYPE_ASSAULT,
 'plrif_beryleomgn': WEAPON_TYPE_ASSAULT,
 'plrif_beryleomgn_fgrip': WEAPON_TYPE_ASSAULT,
 'plrif_berylgbpo40eotech': WEAPON_TYPE_ASSAULT,
 'plrif_beryliron': WEAPON_TYPE_ASSAULT,
 'plrif_berylironnoris': WEAPON_TYPE_ASSAULT,
 'plrif_berylpalladeomgn': WEAPON_TYPE_ASSAULT,
 'plsni_alex': WEAPON_TYPE_SNIPER,
 'plsni_trg22': WEAPON_TYPE_SNIPER,
 'rusht_saiga12': WEAPON_TYPE_SHOTGUN,
 'tripflare': WEAPON_TYPE_CLAYMORE,
 'tripflare_idx4': WEAPON_TYPE_CLAYMORE,
 'tripflare_idx6': WEAPON_TYPE_CLAYMORE,
 'us_agl_mk19': WEAPON_TYPE_ASSAULTGRN,
 'us_agl_mk19_stationary': WEAPON_TYPE_ASSAULTGRN,
 'usaa_fm92a': WEAPON_TYPE_ATAA,
 'usaas_stinger_launcher': WEAPON_TYPE_ATAA,
 'usart_lw155_barrel': WEAPON_TYPE_ATAA,
 'usat_m20': WEAPON_TYPE_ATAA,
 'usat_m20_q1': WEAPON_TYPE_ATAA,
 'usat_smaw': WEAPON_TYPE_ATAA,
 'usat_smaw_hedp': WEAPON_TYPE_ATAA,
 'usat_smaw_sight': WEAPON_TYPE_ATAA,
 'usatp_predator': WEAPON_TYPE_ATAA,
 'usgms_tow2_hmmwv_barrel': WEAPON_TYPE_ATAA,
 'ushgr_m61': WEAPON_TYPE_HANDGRENADE,
 'ushgr_m67': WEAPON_TYPE_HANDGRENADE,
 'ushgr_m67_projectile': WEAPON_TYPE_HANDGRENADE,
 'ushgr_m67_q4': WEAPON_TYPE_HANDGRENADE,
 'uslat_at4': WEAPON_TYPE_ATAA,
 'uslat_at4_projectile': WEAPON_TYPE_ATAA,
 'uslat_m72': WEAPON_TYPE_ATAA,
 'uslat_m72_projectile': WEAPON_TYPE_ATAA,
 'uslmg_m1918': WEAPON_TYPE_LMG,
 'uslmg_m1918_alt': WEAPON_TYPE_LMG,
 'uslmg_m1918deployed': WEAPON_TYPE_LMG,
 'uslmg_m1918deployed_alt': WEAPON_TYPE_LMG,
 'uslmg_m249': WEAPON_TYPE_LMG,
 'uslmg_m249_ammobox': WEAPON_TYPE_LMG,
 'uslmg_m249acog': WEAPON_TYPE_LMG,
 'uslmg_m249acogdeployed': WEAPON_TYPE_LMG,
 'uslmg_m249deployed': WEAPON_TYPE_LMG,
 'uslmg_m249elcan': WEAPON_TYPE_LMG,
 'uslmg_m249elcandeployed': WEAPON_TYPE_LMG,
 'uslmg_m249saw_stationary': WEAPON_TYPE_LMG,
 'usmin_claymore': WEAPON_TYPE_C4,
 'usmin_claymore_detonator': WEAPON_TYPE_C4,
 'usmin_claymore_detonator_sec': WEAPON_TYPE_C4,
 'usmin_claymore_sec': WEAPON_TYPE_C4,
 'usmmg_m240b': WEAPON_TYPE_LMG,
 'usmmg_m240belcan': WEAPON_TYPE_LMG,
 'usmmg_m240g': WEAPON_TYPE_LMG,
 'usmmg_m240gacog': WEAPON_TYPE_LMG,
 'usmmg_m60': WEAPON_TYPE_LMG,
 'uspis_92fs': WEAPON_TYPE_PISTOL,
 'uspis_colt1911': WEAPON_TYPE_PISTOL,
 'uspis_colt1911_idx3': WEAPON_TYPE_PISTOL,
 'uspis_p226': WEAPON_TYPE_PISTOL,
 'usrgl_m16a1ironugl': WEAPON_TYPE_ASSAULTGRN,
 'usrgl_m16a1ironugl_flare': WEAPON_TYPE_ASSAULTGRN,
 'usrgl_m16a1ironugl_smoke': WEAPON_TYPE_ASSAULTGRN,
 'usrgl_m16a4ironugl': WEAPON_TYPE_ASSAULTGRN,
 'usrgl_m16a4ironugl_smoke': WEAPON_TYPE_ASSAULTGRN,
 'usrgl_m16a4ugl': WEAPON_TYPE_ASSAULTGRN,
 'usrgl_m16a4ugl_smoke': WEAPON_TYPE_ASSAULTGRN,
 'usrgl_m4eotechugl': WEAPON_TYPE_ASSAULTGRN,
 'usrgl_m4eotechugl_smoke': WEAPON_TYPE_ASSAULTGRN,
 'usrgl_m4ugl': WEAPON_TYPE_ASSAULTGRN,
 'usrgl_m4ugl_flare': WEAPON_TYPE_ASSAULTGRN,
 'usrgl_m4ugl_smoke': WEAPON_TYPE_ASSAULTGRN,
 'usrif_greasegun': WEAPON_TYPE_SMG,
 'usrif_m14': WEAPON_TYPE_SNIPER,
 'usrif_m14_wood': WEAPON_TYPE_SNIPER,
 'usrif_m14_wood_vn': WEAPON_TYPE_SNIPER,
 'usrif_m14_wood_vndeployed': WEAPON_TYPE_SNIPER,
 'usrif_m14ebr': WEAPON_TYPE_SNIPER,
 'usrif_m14ebracog': WEAPON_TYPE_SNIPER,
 'usrif_m14ebracogdeployed': WEAPON_TYPE_SNIPER,
 'usrif_m14ebrdeployed': WEAPON_TYPE_SNIPER,
 'usrif_m14iron': WEAPON_TYPE_SNIPER,
 'usrif_m14iron_wood': WEAPON_TYPE_SNIPER,
 'usrif_m14iron_wood_vn': WEAPON_TYPE_SNIPER,
 'usrif_m16a1dmr': WEAPON_TYPE_ASSAULT,
 'usrif_m16a1iron': WEAPON_TYPE_ASSAULT,
 'usrif_m16a1iron_20rnd': WEAPON_TYPE_ASSAULT,
 'usrif_m16a1ironugl': WEAPON_TYPE_ASSAULT,
 'usrif_m16a2': WEAPON_TYPE_ASSAULT,
 'usrif_m16a4': WEAPON_TYPE_ASSAULT,
 'usrif_m16a4_6': WEAPON_TYPE_ASSAULT,
 'usrif_m16a4aimpoint': WEAPON_TYPE_ASSAULT,
 'usrif_m16a4aimpoint_6': WEAPON_TYPE_ASSAULT,
 'usrif_m16a4iron': WEAPON_TYPE_ASSAULT,
 'usrif_m16a4ironugl': WEAPON_TYPE_ASSAULT,
 'usrif_m16a4ugl': WEAPON_TYPE_ASSAULT,
 'usrif_m24': WEAPON_TYPE_SNIPER,
 'usrif_m4aimpoint': WEAPON_TYPE_CARBINE,
 'usrif_m4aimpoint_6': WEAPON_TYPE_CARBINE,
 'usrif_m4eotech': WEAPON_TYPE_ASSAULT,
 'usrif_m4eotech_6': WEAPON_TYPE_ASSAULT,
 'usrif_m4eotechugl': WEAPON_TYPE_ASSAULT,
 'usrif_m4iron': WEAPON_TYPE_CARBINE,
 'usrif_m4iron_6': WEAPON_TYPE_CARBINE,
 'usrif_m4scope': WEAPON_TYPE_CARBINE,
 'usrif_m4scope_6': WEAPON_TYPE_CARBINE,
 'usrif_m4scope_dmr': WEAPON_TYPE_SNIPER,
 'usrif_m4scope_dmrdeployed': WEAPON_TYPE_SNIPER,
 'usrif_m4ugl': WEAPON_TYPE_CARBINE,
 'usrif_mk12spr': WEAPON_TYPE_SNIPER,
 'usrif_mk12sprdeployed': WEAPON_TYPE_SNIPER,
 'usrif_mk12sprsup': WEAPON_TYPE_SNIPER,
 'usrif_mk12sprsupdeployed': WEAPON_TYPE_SNIPER,
 'usrif_mp5_a3': WEAPON_TYPE_SMG,
 'usrif_remington11-87': WEAPON_TYPE_SHOTGUN,
 'ussalute': WEAPON_TYPE_TACTICAL,
 'ussht_m1014': WEAPON_TYPE_SHOTGUN,
 'ussht_mossberg590': WEAPON_TYPE_SHOTGUN,
 'ussht_remington870': WEAPON_TYPE_SHOTGUN,
 'ussht_remington870_idx3': WEAPON_TYPE_SHOTGUN,
 'ussni_m24': WEAPON_TYPE_SNIPER,
 'ussni_m40a3': WEAPON_TYPE_SNIPER,
 'vnat_type36': WEAPON_TYPE_ATAA,
 'vnhgr_betty': WEAPON_TYPE_CLAYMORE,
 'vnhgr_betty_idx7': WEAPON_TYPE_CLAYMORE,
 'vnhgr_f1grenade': WEAPON_TYPE_HANDGRENADE,
 'vnhgr_type67': WEAPON_TYPE_HANDGRENADE,
 'vnhgr_type67_idx6': WEAPON_TYPE_HANDGRENADE,
 'vnlmg_rpk': WEAPON_TYPE_LMG,
 'vnlmg_rpkdeployed': WEAPON_TYPE_LMG,
 'vnmmg_dp28': WEAPON_TYPE_LMG,
 'vnmmg_pkm': WEAPON_TYPE_LMG,
 'vnpis_tt33': WEAPON_TYPE_PISTOL,
 'vnpis_tt33_idx3': WEAPON_TYPE_PISTOL,
 'vnrif_mat49': WEAPON_TYPE_ATAA,
 'vnrif_nagant': WEAPON_TYPE_SNIPER,
 'vnrif_nagant_obrez': WEAPON_TYPE_SNIPER,
 'vnrif_nagantzf': WEAPON_TYPE_SNIPER,
 'wave': WEAPON_TYPE_UNKNOWN,
 'wave_idx4': WEAPON_TYPE_UNKNOWN,
 'wrench': WEAPON_TYPE_TACTICAL,
 'wrench_idx6_sp': WEAPON_TYPE_TACTICAL,
 'ziptie': WEAPON_TYPE_KNIFE,
 'zis3_ap_cannon': WEAPON_TYPE_ATAA,
 'zis3_he_cannon': WEAPON_TYPE_ATAA,
 'zis3_smoke_cannon': WEAPON_TYPE_ATAA,
 'zis3_sp_ap_cannon': WEAPON_TYPE_ATAA,
 'zombie': WEAPON_TYPE_TACTICAL,
 'zpu4_barrell': WEAPON_TYPE_ATAA,
 'zpu4_mounted_barrell': WEAPON_TYPE_LMG,
 'zpu4_turret_barrell': WEAPON_TYPE_LMG}
PROJECTILE_TYPE_UNKNOWN = 0
PROJECTILE_TYPE_MINE_VICTIM_AT = 1
PROJECTILE_TYPE_MINE_VICTIM_AP = 2
PROJECTILE_TYPE_MINE_REMOTE_AT = 3
PROJECTILE_TYPE_MINE_REMOTE_AP = 4
PROJECTILE_TYPE_C4_SMALL = 5
PROJECTILE_TYPE_C4_LARGE = 6
mineTypeMap = {'c4_large_projectile': PROJECTILE_TYPE_C4_LARGE,
 'c4_explosives_projectile': PROJECTILE_TYPE_C4_SMALL,
 'argmin_fmk1_projectile': PROJECTILE_TYPE_MINE_VICTIM_AP,
 'argmin_fmk3_projectile': PROJECTILE_TYPE_MINE_VICTIM_AT,
 'at_mine_projectile': PROJECTILE_TYPE_MINE_VICTIM_AT,
 'at_mine_tm35_projectile': PROJECTILE_TYPE_MINE_VICTIM_AT,
 'dynamite_projectile': PROJECTILE_TYPE_C4_SMALL,
 'germin_dynamite_projectile': PROJECTILE_TYPE_C4_SMALL,
 'insrg_dynamite_ied_projectile': PROJECTILE_TYPE_MINE_REMOTE_AT,
 'insrg_mine_ied_projectile': PROJECTILE_TYPE_MINE_REMOTE_AT,
 'insrg_mortar_ied_projectile': PROJECTILE_TYPE_MINE_REMOTE_AT,
 'insrg_tnt_ied_projectile': PROJECTILE_TYPE_MINE_REMOTE_AT,
 'insgr_hgr_trap_projectile': PROJECTILE_TYPE_MINE_VICTIM_AP,
 'insrg_watercontainer_ied_projectile': PROJECTILE_TYPE_MINE_VICTIM_AP,
 'rumin_mon50_projectile': PROJECTILE_TYPE_MINE_REMOTE_AP,
 'rumin_mon50_sec_projectile': PROJECTILE_TYPE_MINE_REMOTE_AP,
 'rumin_pomz_projectile': PROJECTILE_TYPE_MINE_VICTIM_AP,
 'rumin_tm35_projectile': PROJECTILE_TYPE_MINE_VICTIM_AT,
 'tm62m_mine_projectile': PROJECTILE_TYPE_MINE_VICTIM_AT,
 'tnt_projectile': PROJECTILE_TYPE_C4_SMALL,
 'tnt_ww2_projectile': PROJECTILE_TYPE_C4_SMALL,
 'tripflare_projectile': PROJECTILE_TYPE_MINE_VICTIM_AP,
 'usmin_claymore_projectile': PROJECTILE_TYPE_MINE_REMOTE_AP,
 'usmin_claymore_sec_projectile': PROJECTILE_TYPE_MINE_REMOTE_AP,
 'usmin_m1a1_projectile': PROJECTILE_TYPE_MINE_VICTIM_AT,
 'usmin_m2a3_projectile': PROJECTILE_TYPE_MINE_VICTIM_AP,
 'vnhgr_betty_projectile': PROJECTILE_TYPE_MINE_VICTIM_AP,
 'c4_smallexplosives_timed_projectile': PROJECTILE_TYPE_C4_SMALL,
 'dynamite_small_timed_projectile': PROJECTILE_TYPE_C4_SMALL,
 'tnt_small_timed_projectile': PROJECTILE_TYPE_C4_SMALL}
PROJECTILE_TYPE_AT_LIGHT = 32
PROJECTILE_TYPE_AT_HEAVY = 33
PROJECTILE_TYPE_ATGM = 34
PROJECTILE_TYPE_AA = 35
PROJECTILE_TYPE_GRENADIER = 36
PROJECTILE_TYPE_MORTAR = 37
PROJECTILE_TYPE_GRENADEFRAG = 38
PROJECTILE_TYPE_SMOKE = 39
PROJECTILE_TYPE_TANKSHELL = 40
PROJECTILE_TYPE_SMOKE_IR = 41
rocketTypeMap = {'uslat_m72_projectile': PROJECTILE_TYPE_AT_LIGHT,
 'igla_9k38': PROJECTILE_TYPE_AA,
 'eryx': PROJECTILE_TYPE_AT_HEAVY,
 'pf98_missile': PROJECTILE_TYPE_AT_HEAVY,
 'chlat_pf89_projectile': PROJECTILE_TYPE_AT_LIGHT,
 'blowpipe_missile': PROJECTILE_TYPE_AA,
 'at_predator': PROJECTILE_TYPE_AT_HEAVY,
 'gerat_panzerfaust100_projectile': PROJECTILE_TYPE_AT_LIGHT,
 'gerat_panzerfaust60_projectile': PROJECTILE_TYPE_AT_LIGHT,
 'gerat_panzerschreck_projectile': PROJECTILE_TYPE_AT_HEAVY,
 'gerat_pzf3_rocket': PROJECTILE_TYPE_AT_HEAVY,
 'gerlat_pzf3_rocket': PROJECTILE_TYPE_AT_LIGHT,
 'at_matador': PROJECTILE_TYPE_AT_HEAVY,
 'rpg7_warhead_iranian_tandem_ins': PROJECTILE_TYPE_AT_HEAVY,
 'rpg7_warhead_pg7v_ins': PROJECTILE_TYPE_AT_HEAVY,
 'rpg7_warhead_pg7vl_ins': PROJECTILE_TYPE_AT_HEAVY,
 'rpg7_warhead_pg7vm': PROJECTILE_TYPE_AT_HEAVY,
 'rpg7_warhead_pg7vr_ins': PROJECTILE_TYPE_AT_HEAVY,
 'rpg7_warhead_cobrra': PROJECTILE_TYPE_AT_HEAVY,
 'rpg7_warhead_dzgi40': PROJECTILE_TYPE_AT_LIGHT,
 'rpg7_warhead_f7': PROJECTILE_TYPE_AT_LIGHT,
 'rpg7_warhead_og7vm': PROJECTILE_TYPE_AT_LIGHT,
 'rpg7_warhead_tbg7v': PROJECTILE_TYPE_AT_LIGHT,
 'sa7_missile': PROJECTILE_TYPE_AA,
 'at_latprojectile': PROJECTILE_TYPE_AT_LIGHT,
 'rpg7_warhead_iranian_tandem_con': PROJECTILE_TYPE_AT_HEAVY,
 'rpg7_warhead_pg7v_con': PROJECTILE_TYPE_AT_LIGHT,
 'rpg7_warhead_ko7m': PROJECTILE_TYPE_AT_LIGHT,
 'rpg7_warhead_pg7mt': PROJECTILE_TYPE_AT_HEAVY,
 'rpg7_warhead_pg7m': PROJECTILE_TYPE_AT_LIGHT,
 'ger_at_spike': PROJECTILE_TYPE_AT_HEAVY,
 'rpg7_warhead_og7v': PROJECTILE_TYPE_AT_LIGHT,
 'rpg7_warhead_pg7vl_con': PROJECTILE_TYPE_AT_HEAVY,
 'rpg7_warhead_pg7vr_con': PROJECTILE_TYPE_AT_HEAVY,
 'rpg7_warhead_pg7vs': PROJECTILE_TYPE_AT_LIGHT,
 'stinger_missile': PROJECTILE_TYPE_AA,
 'usat_m1bazooka_projectile': PROJECTILE_TYPE_AT_LIGHT,
 'm20_rocket': PROJECTILE_TYPE_AT_HEAVY,
 'at_smaw': PROJECTILE_TYPE_AT_HEAVY,
 'at_smaw_hedp': PROJECTILE_TYPE_AT_HEAVY,
 'uslat_at4_projectile': PROJECTILE_TYPE_AT_HEAVY,
 'seacat_missile': PROJECTILE_TYPE_GRENADIER,
 'riflegrenade_at_projectile': PROJECTILE_TYPE_GRENADIER,
 'riflegrenade_he_projectile': PROJECTILE_TYPE_GRENADIER,
 'riflegrenade_smoke_projectile': PROJECTILE_TYPE_GRENADIER,
 'riflegrenade_smoke_projectile_sp': PROJECTILE_TYPE_GRENADIER,
 '40mm_hegrenade_projectile': PROJECTILE_TYPE_GRENADIER,
 '40mm_mk19mod3_projectile': PROJECTILE_TYPE_GRENADIER,
 '40mm_smoke_projectile': PROJECTILE_TYPE_GRENADIER,
 '40mm_smoke_projectile_sp': PROJECTILE_TYPE_GRENADIER,
 'ch_at_hj8': PROJECTILE_TYPE_ATGM,
 'ru_at_9m133fm': PROJECTILE_TYPE_ATGM,
 'milan_missile': PROJECTILE_TYPE_ATGM,
 'spg-9_og-9_hef': PROJECTILE_TYPE_ATGM,
 'spg-9_pg-9_heat': PROJECTILE_TYPE_ATGM,
 'tow2_missile': PROJECTILE_TYPE_ATGM,
 'm252_mortar_he_shell': PROJECTILE_TYPE_MORTAR,
 'm252_mortar_prx_shell': PROJECTILE_TYPE_MORTAR,
 'm252_mortar_frag_shell': PROJECTILE_TYPE_MORTAR,
 'm252_mortar_smoke_shell': PROJECTILE_TYPE_MORTAR,
 'sa19_grison_saclos': PROJECTILE_TYPE_AA,
 'starstreak_hvm': PROJECTILE_TYPE_AA,
 'seacat_missile_aclos': PROJECTILE_TYPE_AA,
 'sa3_missile': PROJECTILE_TYPE_AA,
 'sa19_grison': PROJECTILE_TYPE_AA,
 'ru_aa_9m333': PROJECTILE_TYPE_AA,
 'gbaa_blowpipe': PROJECTILE_TYPE_AA,
 'aa11_archer': PROJECTILE_TYPE_AA,
 'aim9': PROJECTILE_TYPE_AA,
 'aim120_amraam': PROJECTILE_TYPE_AA,
 'ru_aa_r60m': PROJECTILE_TYPE_AA,
 'aim9b_sidewinder': PROJECTILE_TYPE_AA,
 'matra_r550_magic1': PROJECTILE_TYPE_AA,
 'matra_r530': PROJECTILE_TYPE_AA,
 'aim9l_sidewinder': PROJECTILE_TYPE_AA,
 'ru_aa_r27re': PROJECTILE_TYPE_AA,
 'at5_spandrel': PROJECTILE_TYPE_ATGM,
 'ru_at_9m14': PROJECTILE_TYPE_ATGM,
 'at11_sniper': PROJECTILE_TYPE_ATGM,
 'tnk_125_apfsds_g': PROJECTILE_TYPE_TANKSHELL,
 'tnk_125_frag_g': PROJECTILE_TYPE_TANKSHELL,
 'tnk_125_heat_g': PROJECTILE_TYPE_TANKSHELL,
 'tnk_120_smoke_r': PROJECTILE_TYPE_TANKSHELL,
 'tnk_120_hesh_r': PROJECTILE_TYPE_TANKSHELL,
 'tnk_120_heat_r': PROJECTILE_TYPE_TANKSHELL,
 'tnk_120_apfsds_r': PROJECTILE_TYPE_TANKSHELL,
 'tnk_115_apfsds': PROJECTILE_TYPE_TANKSHELL,
 'tnk_115_frag': PROJECTILE_TYPE_TANKSHELL,
 'tnk_115_heat': PROJECTILE_TYPE_TANKSHELL,
 'at10_stabber': PROJECTILE_TYPE_ATGM,
 'm82_brightir': PROJECTILE_TYPE_SMOKE_IR,
 'm82': PROJECTILE_TYPE_SMOKE,
 'ru_at_9m114': PROJECTILE_TYPE_ATGM,
 'f1grenade_projectile': PROJECTILE_TYPE_GRENADEFRAG,
 'frhgr_of37_projectile': PROJECTILE_TYPE_GRENADEFRAG,
 'frhgr_smoke_projectile': PROJECTILE_TYPE_SMOKE,
 'gbhgr_l109_projectile': PROJECTILE_TYPE_GRENADEFRAG,
 'gerhgr_dm51_projectile': PROJECTILE_TYPE_GRENADEFRAG,
 'hgr_smoke_projectile': PROJECTILE_TYPE_SMOKE,
 'hgr_smoke_signal_projectile': PROJECTILE_TYPE_SMOKE,
 'hgr_smoke_vietnam_projectile': PROJECTILE_TYPE_SMOKE,
 'plhgr_rgo88_projectile': PROJECTILE_TYPE_GRENADEFRAG,
 'plhgr_ugd200_projectile': PROJECTILE_TYPE_SMOKE,
 'plhgr_ugd200red_projectile': PROJECTILE_TYPE_SMOKE,
 'ushgr_m67_projectile': PROJECTILE_TYPE_GRENADEFRAG,
 'technical_rocket_s5': PROJECTILE_TYPE_AT_LIGHT}

def getProjectileType(templateName):
    templateName = templateName.lower()
    if templateName in mineTypeMap:
        return mineTypeMap[templateName]
    if templateName in rocketTypeMap:
        return rocketTypeMap[templateName]
    return PROJECTILE_TYPE_UNKNOWN


kitTypeMap = {'aa': KIT_TYPE_AA,
 'assault': KIT_TYPE_ASSAULT,
 'at': KIT_TYPE_AT,
 'engineer': KIT_TYPE_ENGINEER,
 'insurgent': KIT_TYPE_ASSAULT,
 'marksman': KIT_TYPE_MARKSMAN,
 'medic': KIT_TYPE_MEDIC,
 'mg': KIT_TYPE_ASSAULT,
 'officer': KIT_TYPE_OFFICER,
 'pilot': KIT_TYPE_PILOT,
 'rifleman': KIT_TYPE_ASSAULT,
 'riflemanap': KIT_TYPE_ASSAULT,
 'riflemanat': KIT_TYPE_AT,
 'sapper': KIT_TYPE_ENGINEER,
 'sniper': KIT_TYPE_SNIPER,
 'specialist': KIT_TYPE_ASSAULT,
 'specops': KIT_TYPE_SPECOPS,
 'spotter': KIT_TYPE_SUPPORT,
 'support': KIT_TYPE_SUPPORT,
 'tanker': KIT_TYPE_CREWMAN,
 'unarmed': KIT_TYPE_ASSAULT,
 'vip': KIT_TYPE_OFFICER}
mapMap = {}
UNKNOWN_MAP = 99
armyMap = {'cf': ARMY_CANADA,
 'ch': ARMY_CHINESE,
 'chinsurgent': ARMY_REBELS,
 'eu': ARMY_EURO,
 'gb': ARMY_BRITS,
 'ger': ARMY_GERMAN,
 'mec': ARMY_MEC,
 'mecsf': ARMY_MECSF,
 'meinsurgent': ARMY_INSURGENTS,
 'sas': ARMY_SAS,
 'seal': ARMY_SEALS,
 'spetz': ARMY_SPETZNAS,
 'us': ARMY_USA,
 'usa': ARMY_USA}
gameModeMap = {'gpm_aas': GPM_AAS,
 'gpm_cnc': GPM_CNC,
 'gpm_counter': GPM_COUNTER,
 'gpm_cq': GPM_CQ,
 'gpm_insurgency': GPM_INSURGENCY,
 'gpm_scenario': GPM_SCENARIO,
 'gpm_skirmish': GPM_SKIRMISH,
 'gpm_sl': GPM_SL,
 'gpm_sobj': GPM_SOBJ,
 'gpm_training': GPM_TRAINING,
 'gpm_xtract': GPM_XTRACT}
_vehicleTypeCache = OrderedDict()

def getVehicleType(templateName):
    templateName = templateName.lower()
    try:
        return _vehicleTypeCache[templateName]
    except KeyError:
        for vtype in vehicleTypeMap:
            if templateName.find(vtype) != -1:
                _vehicleTypeCache[templateName] = vehicleTypeMap[vtype]
                return vehicleTypeMap[vtype]

        _vehicleTypeCache[templateName] = VEHICLE_TYPE_UNKNOWN
        return VEHICLE_TYPE_UNKNOWN


def getWeaponType(templateName):
    try:
        return weaponTypeMap[templateName.lower()]
    except KeyError:
        return WEAPON_TYPE_UNKNOWN


def getKitType(templateName):
    try:
        templateName = templateName.split('_')[1]
    except:
        pass

    for t, v in kitTypeMap.items():
        if templateName.find(t) != -1:
            return v

    return KIT_TYPE_UNKNOWN


def getArmy(templateName):
    try:
        return armyMap[templateName.lower()]
    except KeyError:
        return ARMY_UNKNOWN


def getMapId(mapName):
    try:
        return mapMap[mapName.lower()]
    except KeyError:
        return UNKNOWN_MAP


def getGameModeId(gameMode):
    try:
        return gameModeMap[gameMode.lower()]
    except KeyError:
        return UNKNOWN_GAMEMODE


def getRootParent(obj):
    parent = obj.getParent()
    if parent is None:
        return obj
    else:
        return getRootParent(parent)


VEC_FORWARD = (0.0, 0.0, 1.0)
VEC_UP = (0.0, 1.0, 0.0)
TICK_RATE = 30
FRAME_TIME = 1.0 / TICK_RATE
print 'Project Reality constants loaded'