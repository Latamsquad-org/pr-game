from realitytutorial import *
import realitykits as rkits
import realityconfig_local as cfg


# Entry point for the definitions. load() must be defined.
def load():
    basics()
    advanced()
    sandbox()

def basics():
    # This creates the first section of the tutorial menu on index 0 (top left button).
    # The name of the button will be BASICS. Clicking on it will show the chapters defined inside it.
    SetMainMenuButtonText(0, "BASICS")
    # This creates a new chapter, on index 0 of the main menu, and index 1 of the secondary menu.
    # The name on the button will be VOICE
    # This function sets the current "active" chapter, like when creating objects in .con files.
    CreateChapter("VOICE", 0, 0, True)
    CreateTask("About Mumble\n")
    TaskObjectives(
        "Mumble is a separate application responsible for voice chat. It launches automatically and runs in the background.\n\n\r"
        "Click CONTINUE to launch Mumble."
    )
    ClickContinueObjective()

    CreateTask("Configure Mumble\n")
    TaskObjectives(
        "Make sure your INPUT and OUTPUT devices are configured correctly before joining a live server.\n\n\r"
        "Objective - Click CONTINUE to proceed."
    )
    OpenMumbleProcess()
    ClickContinueObjective()

    CreateTask("Excellent work!\n\n")
    TaskObjectives(
        "You have completed this chapter! Press CAPS LOCK to start the next chapter."
    )
    ChapterCompletedSound()


    CreateChapter("SPAWN SCREEN", 0, 1, True)

    CreateTask("Squad Menu - List\n")
    TaskObjectives(
        "In the SQUAD menu you can view, create or join squads. Note - This is not possible when wounded/dead.\n\n\r"
        "Objective - Press CREATE to create a squad."
    )
    JoinSquadObjective()

    CreateTask("Squad Menu - Map")
    TaskObjectives(
        "The map in this tab shows all currently deployed units of your team.\n\r"
        "On this map you can change the zoom level by pressing the N keybind and click the map to move around.\n\n\r"
        "Objective - Click CONTINUE to proceed.\n"
    )
    ClickContinueObjective()

    CreateTask("Kit Selection\n")
    TaskObjectives(
        "Press ENTER to toggle the KIT menu to choose your default kit. Select the RIFLEMAN kit.\n\n\r"
        "The map in this tab displays all available spawn points. Click the WHITE DOT in the top left corner and click SPAWN / press ENTER.\n\n\r"
        "Objective - Spawn in."
    )
    VoiceOverAtStart(
        "voicefile.wav",
        1.0,
        "Note - More specialized kits, like MARKSMAN, or COMBAT ENGINEER are not available on the spawn screen.",
        20.0
    )
    SpawnInObjective()

    CreateTask("Excellent work!\n\n")
    TaskObjectives(
        "You have completed this chapter! Press CAPS LOCK to start the next chapter."
    )
    ChapterCompletedSound()


    CreateChapter("UI & CONTROLS", 0, 2)

    CreateTask("Equipment\n")
    TaskObjectives(
        "Use your scroll wheel or weapon slot keybinds [1-8] to switch between your equipment.\n\n\r"
        "Objective - Explore all slots in your equipment."
    )
    SwitchWeaponObjective("dressing")

    CreateTask("Compass\n")
    TaskObjectives(
        "Your compass is at the bottom of your screen. Use it to navigate and call our targets.\n\n\r"
        "The arrow below your compass is the current objective of your squad.\n\n\r"
        "Objective - Press CONTINUE to proceed."
    )
    SetMarker((-400.0, 26.0, 50.0), "observe")
    ClickContinueObjective()

    CreateTask("Map\n")
    TaskObjectives(
        "Press M to open your map. Change the zoom level by pressing N.\n\n\r"
        "Objective - Move to the marker to proceed."
    )
    CreateSquad()
    SetMarker((-383.0, 26.0, 18.6), "move")
    MoveToPositionObjective((-383.0, 26.0, 18.6), 3)

    CreateTask("Map grid\n")
    TaskObjectives(
        "The map is divided into grids. Each grid is named after the intersecting column (A-M) and row (1-13).\n\r"
        "For example - The top left grid is Alpha 1 (A1). This grid contains a hint for keypads.\n\n\r"
        "Objective - Press CONTINUE to proceed."
    )
    ClickContinueObjective()

    CreateTask("Map grid\n")
    TaskObjectives(
        "Each grid is split into 9 keypads to specify more precise locations.\n\n\r"
        "You are currently located in Bravo 7 keypad 8 (B7kp8).\n\n\r"
        "Objective - Press CONTINUE to proceed."
    )
    ClickContinueObjective()

    CreateTask("Objective markers\n")
    TaskObjectives(
        "There are 6 marker types: MOVE, TARGET, OBSERVE, DEFEND, DESTROY, BUILD.\n\n\r"
        "To place markers, use the SECONDARY RADIO [T] or right-click the SQUAD menu map.\n\n\r"
        "Objective - Press CONTINUE to proceed."
    )
    ClickContinueObjective()

    CreateTask("Accuracy deviation\n")
    TaskObjectives(
        "While aiming, you will see two dots above your compass, representing your accuracy. If the dots are disconnected, your shots will be less accurate.\n\n\r"
        "Objective - Aim down sights [RMB].\n\n\r"
    )
    TeleportAtStart((-383.0, 26.0, 18.6))
    SwitchWeapon(3)
    ZoomInObjective()

    CreateTask("Accuracy deviation\n")
    TaskObjectives(
        "Wait until the dots connect between your shots to hit the target consistently.\n\n\r"
        "Objective - Hit the target."
    )
    CreateSquad()
    target = ObjectSpawnerTemplate("target_pr_dynamic", (-284.0, 24.990, 18.6), rot=ROT_WEST, team=TEAM_ENEMY)
    SpawnObject(target)
    SetMarker((-284.0, 24.990, 18.6), "attack")
    DamageTargetObjective(target, 100)

    CreateTask("Accuracy deviation\n")
    TaskObjectives(
        "Movement (running, jumping, going prone, looking around) increases your deviation.\n\n\r"
        "Switch to a crouching [CTRL] stance for better accuracy.\n\n\r"
        "Objective - Press CONTINUE to proceed."
    )
    ClickContinueObjective()
    #CrouchObjective()

    CreateTask("Fire mode selector\n")
    TaskObjectives(
        "To switch your fire mode, press your weapon slot keybind [3]. Check your current fire mode in the bottom right corner.\n\n\r"
        "Try to hit the target using the burst fire mode [3] and control the recoil. Press R to reload your weapon.\n\n\r"
        "Objective - Hit the target."
    )
    CreateSquad()
    TeleportAtStart((-383.0, 26.0, 18.6))
    SwitchWeapon(3)
    UnspawnObject(target)
    target = ObjectSpawnerTemplate("target_pr_dynamic", (-334.0, 24.990, 18.6), rot=ROT_WEST, team=TEAM_ENEMY)
    SpawnObject(target)
    SetMarker((-334.0, 24.990, 18.6), "attack")
    DamageTargetObjective(target, 500)

    CreateTask("Ammunition management\n")
    TaskObjectives(
        "In the bottom right corner you can also see how many spare magazines/rounds you have for your weapon.\n\r"
        "To inspect your current magazine, hold the MAIN RADIO [Q].\n\n\r"
        "Objective - Press CONTINUE to proceed."
    )
    ClickContinueObjective()

    CreateTask("Switching kits\n")
    TaskObjectives(
        "To pick up a nearby kit, press your PICKUP KIT keybind [G].\n\n\r"
        "Objective - Pick up the kit on the marker."
    )
    CreateSquad()
    SetMarker((-383.0, 26.0, 15.0), "observe")
    SpawnObject(ObjectSpawnerTemplate("ger_rifleman", (-383.0, 25.4, 15.0)))
    GetKitObjective("ger_rifleman")

    CreateTask("Back-up iron sights\n")
    TaskObjectives(
        "Some weapons have backup iron sights (BUIS) for close distance engagements.\n\r"
        "Press the CYCLE CAMERA keybind [C] to switch between your sights. You can see your selected sight in the bottom right corner.\n\n\r"
        "Objective - Hit the far target."
    )
    CreateSquad()
    UnspawnObject(target)
    target = ObjectSpawnerTemplate("target_pr_dynamic", (-284.0, 24.990, 15), rot=ROT_WEST, team=TEAM_ENEMY)
    SpawnObject(target)
    SetMarker((-284.0, 24.990, 15), "attack")
    DamageTargetObjective(target, 100)

    CreateTask("Back-up iron sights\n")
    TaskObjectives(
        "Note - It is easier to acquire a new target using BUIS.\n\n\r"
        "Objective - Hit the closer target."
    )
    UnspawnObject(target)
    target = ObjectSpawnerTemplate("target_pr_dynamic", (-374.0, 24.990, 3.0), rot=ROT_NORTH, team=TEAM_ENEMY)
    SpawnObject(target)
    SetMarker((-374.0, 24.990, 3.0), "attack")
    DamageTargetObjective(target, 100)

    CreateTask("Stamina management\n")
    TaskObjectives(
        "Objective - Move to the entrance to proceed."
    )
    UnspawnObject(target)
    SetMarker((-400.0, 26.0, 4.0), "move")
    MoveToPositionObjective((-400.0, 26.0, 4.0), 3)

    CreateTask("Stamina management\n")
    TaskObjectives(
        "Hold the sprint keybind [SHIFT] or double-tap the forward keybind [W] to sprint.\n\n\r"
        "Objective - Sprint towards the marker to proceed."
    )
    SetMarker((-400.0, 26.0, -125.0), "move")
    SoldierSprintObjective()

    CreateTask("Stamina management\n")
    TaskObjectives(
        "Your stamina bar is located in the bottom left corner of your screen.\n\n\r"
        "Objective - Run towards the marker until you fully deplete your stamina."
    )
    SoldierStaminaLowObjective()

    CreateTask("Stamina management\n")
    TaskObjectives(
        "Note - You cannot start running if your stamina is below 50%.\n"
        "It is good practice to keep it above 50% unless crossing open fields.\n\n\r"
        "Objective - Move to the marker."
    )
    SetMarker((-445.0, 26.0, -106.0), "move")
    MoveToPositionObjective((-445.0, 26.0, -106.0), 3)

    CreateTask("Crawling\n")
    TaskObjectives(
        "To crawl, press the PRONE keybind [Z].\n\n\r"
        "Objective - Crawl to the marker."
    )
    SetMarker((-445.0, 26.0, -78.0), "move")
    MoveToPositionObjective((-445.0, 26.0, -92.0), 3)

    CreateTask("Crawling\n")
    TaskObjectives(
        "To crawl, press the PRONE keybind [Z].\n\n\r"
        "Objective - Crawl to the marker."
    )
    MoveToPositionObjective((-445.0, 26.0, -78.0), 2)

    CreateTask("Excellent work!\n\n")
    TaskObjectives(
        "You have completed this chapter! Press CAPS LOCK to start the next chapter."
    )
    ChapterCompletedSound()


    CreateChapter("SPAWN POINTS", 0, 3, False)

    CreateTask("Enter the logistics truck\n")
    TaskObjectives(
        "The logistics truck is a crucial asset and should not be used for transport. It carries supply crates, repair stations and support bridges.\n\n\r"
        "To enter vehicles you need to be close to their door/hatch and press the ENTER/EXIT keybind [E].\n\n\r"
        "Objective - Get in the logistics truck driver seat.\n"
    )
    VoiceOverAtStart(
        "voicefile.wav",
        1.0,
        "There are two types of spawn points you can deploy as a Squad Leader - Forward Operating Bases (FOBs) and Rally Points (RPs).\nFollow the instructions to learn how to deploy spawn points on the battlefield.",
        20.0
    )
    LeaveVehicleButton()
    TeleportAtStart((-402.0, 26.0, -21.0))
    SetMarker((-400.0, 26.0, -29.0), type="observe")
    logi = ObjectSpawnerTemplate("us_trk_logistics", POS_PLAYERFRONT, rot=ROT_SOUTH)
    SpawnObject(logi)
    GetInSeatObjective("us_trk_logistics")

    CreateTask("Deliver supplies\n")
    TaskObjectives(
        "Use your [W, S, A, D] keys to drive the truck to Bravo 13 keypad 4. Press the CYCLE CAMERA keybind [C] to look back.\n\n\r"
        "Objective - Deliver supplies to the marker."
    )
    pos = (-390.0, 26.0, -450.0)
    SetMarker(pos, "move")
    MoveToPositionObjective(pos, 10)

    CreateTask("Drop one supply crate\n")
    TaskObjectives(
        "Supply crates are used to build FOBs, resupply ammunition, and request kits.\n\n\r"
        "While in the truck, use your scroll wheel or weapon slot [2] to select the SUPPLY CRATE, then press [RMB] to drop it.\n\n\r"
        "Objective - Drop the supply crate."
    )
    BeAroundObjectObjective("pr_supply_crate_us", 1)

    CreateTask("Get an Officer kit\n")
    TaskObjectives(
        "Objective - Request an OFFICER kit from the supply crate.\n\n\r"
        "1. Hold the SECONDARY RADIO [T].\r\n"
        "2. Press [LMB] on the REQUEST button.\r\n"
        "3. Choose the OFFICER kit and pick it up [G]."
    )
    VoiceOverAtStart(
        "voicefile.wav",
        1.0,
        "You can request kits from large supply crates, medium supply crates, or armoured personnel carriers (APCs).",
        20.0
    )
    GetKitObjective("us_officer")

    pos = (-390.0, 26.0, -445.0)
    CreateTask("Deploy a FOB\n")
    SetMarker(pos, "build")
    TaskObjectives(
        "Objective - Deploy a Forward Operating Base\n\n\r"
        "1. Select the RADIO [6] and press [RMB] to activate it.\r\n"
        "2. Hold the SECONDARY RADIO [T].\r\n"
        "3. Press [LMB] on the DEPLOY button and choose FORWARD OUTPOST."
    )
    VoiceOverAtStart(
        "voicefile.wav",
        1.0,
        "FOBs can be deployed only if there is a large supply crate nearby. Two medium supply crates act as one large supply crate.",
        20.0
    )
    DeployAssetObjective("outpost")

    CreateTask("Shovel\n")
    TaskObjectives(
        "Most standard kits include a shovel. It is used to build FOBs and other emplacements.\n\n\r"
        "Request the RIFLEMAN kit from the crate and equip your shovel [2].\n\n\r"
        "Objective - Equip the shovel."
    )
    ammokit = ObjectSpawnerTemplate("us_rifleman", POS_PLAYERFRONT)
    SpawnObject(ammokit)
    PickupKit(ammokit)
    SwitchWeaponObjective("klappspaten")

    CreateTask("Build the FOB\n")
    TaskObjectives(
        "Hold [LMB] with your shovel on the FOB to build it. Watch the progress bar above your compass.\n\n\r"
        "Press M to see the FOB on the map. It appears as a green triangle and will activate a spawn point.\n\n\r"
        "Objective - Build the firebase.\n\n\r"
    )
    VoiceOverAtStart(
        "voicefile.wav",
        1.0,
        "Forward Operating Bases become unspawnable if there are are 2 or more enemies next to it.",
        20.0
    )
    SwitchWeapon(2)
    BuildAssetObjective("outpost")

    CreateTask("Drop the second supply crate\n")
    TaskObjectives(
        "Enter the truck [E] and use your scroll wheel or weapon slot [2] to select the SUPPLY CRATE, then press [RMB] to drop it.\n\n\r"
        "Objective - Drop the second supply crate."
    )
    VoiceOverAtStart(
        "voicefile.wav",
        1.0,
                "With a second large supply crate you can build more emplacements - anti-tank launchers, anti-air launchers, heavy machine guns, mortars, sandbags or razorwires.",
        20.0
    )
    BeAroundObjectObjective("pr_supply_crate_us", 2)

    CreateTask("Deploy an HMG\n")
    SetMarker((-390.0, 26.0, -485.0), "build")
    TaskObjectives(
        "Pick up the OFFICER kit and equip the RADIO [6]. Use your SECONDARY RADIO [T] to deploy an HMG.\n\n\r"
        "Build it on the marker while looking EAST - the spawned asset will inherit your direction.\n\n\r"
        "Objective - Deploy an HMG."
    )
    VoiceOverAtStart(
        "voicefile.wav",
        1.0,
                "Deploy the HMG. If you would like to reposition the asset, use your RADIO and select REMOVE ASSET.",
        20.0
    )
    DeployAssetObjective("hmg")

    CreateTask("Build the HMG\n")
    TaskObjectives(
        "Pick up the RIFLEMAN kit again. Select your shovel [2] and hold [LMB] on the HMG to build it. Watch the progress bar above your compass.\n\n\r"
        "Objective - Build the HMG."
    )
    ammokit = ObjectSpawnerTemplate("us_rifleman", POS_PLAYERFRONT)
    SpawnObject(ammokit)
    PickupKit(ammokit)
    SetMarker((-390.0, 26.0, -485.0), "build")
    BuildAssetObjective("hmg")

    CreateTask("Destroy the target\n")
    TaskObjectives(
        "Throw your AMMO BAG on the HMG to rearm it. Press your ENTER/EXIT keybind [E] to man the HMG.\n\n\r"
        "Press [R] to load the machine gun and destroy the marked target. Hold [SHIFT] to zoom in.\n\n\r"
        "Objective - Destroy the target."
    )
    enemytrk = ObjectSpawnerTemplate("ru_trk_logistics", (-190.0, 26.0, -490.0), rot=ROT_WEST, team=TEAM_ENEMY)
    SpawnObject(enemytrk)
    SetMarker((-190.0, 26.0, -490.0), "attack")
    DestroyTargetObjective(enemytrk)

    CreateTask("Rally Point")
    TaskObjectives(
        "Pick up / request the OFFICER kit at the crate to deploy a Rally Point.\n\n\r"
        "Objective - Pick up the OFFICER kit."
    )
    UnspawnObject(logi)
    SetMarker((-390.0, 26.0, -450.0), type="observe")
    GetKitObjective("us_officer")

    CreateTask("Rally Point\n")
    TaskObjectives(
        "The Rally Point is a temporary, squad-specific spawn point. Players from other squads will not be able to spawn on it.\n\n\r"
        "It allows fallen squad members to deploy in the field - use it if there is no FOB nearby.\n\n\r"
        "Objective - Move to the marker."
    )
    UnspawnObject(ammokit)
    SetMarker((-334.0, 26.0, -350.0), type="move")
    MoveToPositionObjective((-334.0, 26.0, -350.0), 5)

    CreateTask("Rally Point\n")
    TaskObjectives(
        "The Rally Point can be deployed with 2 or more squad members next to the Squad Leader.\n\n\r"
        "It can not be placed if there are enemies nearby. An existing RP disappears if overrun.\n\n\r"
        "Objective - Move to the marker."
    )
    SetMarker((-270.0, 26.0, -420.0), type="move")
    MoveToPositionObjective((-270.0, 26.0, -420.0), 5)

    CreateTask("Rally Point\n")
    TaskObjectives(
        "Hold the SECONDARY RADIO [T] and select PLACE RALLY POINT.\n\n\r"
        "The Rally Point takes time to rearm. If it is still unavailable, try again in a minute.\n\n\r"
        "Objective - Place a Rally Point."
    )
    slkit = ObjectSpawnerTemplate("us_officer", POS_PLAYERFRONT)
    SpawnObject(slkit)
    PickupKit(slkit)
    CreateSquad()
    DeployRallyObjective()

    CreateTask("Excellent work!\n\n")
    TaskObjectives(
        "Open your map [M] to see your Rally Point. It appears as a green orb with your squad number (1).\n\n\r"
        "You have completed this chapter! Press CAPS LOCK to start the next chapter."
    )
    UnspawnObject("hmg")
    ChapterCompletedSound()


    CreateChapter("MEDIC", 0, 4)

    CreateTask("Medic")
    TaskObjectives(
        "As a MEDIC, your role is reviving/healing squad members. Each squad can have up to 2 medics.\n\n\r"
        "It has 6 bandages, a medic bag and epipen injectors. It is the only kit capable of dragging bodies.\n\n\r"
        "Objective - Pick up the MEDIC kit [G]."
    )
    LeaveVehicleButton()
    TeleportAtStart((447.0, 25.0, -369.0))
    SetMarker((450.0, 23.7, -369.0), type="observe")
    medickit = ObjectSpawnerTemplate("us_medic_tutorial", (450.0, 23.7, -369.0))
    SpawnObject(medickit)
    body = ObjectSpawnerTemplate("dead_us_soldier_tutorial", (454.0, 23.85, -368.0), (0, 180, 0))
    SpawnObject(body)
    CreateSquad()
    GetKitObjective("us_medic_tutorial")

    CreateTask("Field dressing")
    TaskObjectives(
        "Every kit has a field dressing (weapon slot 8) - it heals 25% of your total health.\n\n\r"
        "To use it, press your [LMB]. It will fall on the ground and restore your health when consumed.\n\n\r"
        "Objective - Equip the field dressing [8] and stop the bleeding."
    )
    VoiceOverAtStart(
        "voicefile.wav",
        1.0,
                "TIP 1: Do not use the bandage if you have a medic nearby.\n\rTIP 2: You can share your bandage with a teammate by dropping it at someone's feet.",
        20.0
    )
    InjurePlayer()
    SwitchWeaponObjective("dressing")

    CreateTask("Medic bag")
    TaskObjectives(
        "Note, that bleeding won't stop if you have less than 75% of your total health.\n\n\r"
        "With the medic bag equipped [4], hold [LMB] at an injured teammate to heal them, just like with the shovel.\n\n\r"
        "Objective - Heal the body to proceed."
    )
    VoiceOverAtStart("voicefile.wav", 1.0, "Note - You can not heal yourself with the medic bag. If you're bleeding, ask another medic to patch you up.", 20.0)
    RepairTargetObjective(body, 90)

    CreateTask("Body dragging\n")
    TaskObjectives(
        "As a medic, you can drag downed teammates to safety before reviving them. To do so, crouch, point at the body and select weapon slot 2.\n\n\r"
        "Objective - Select the BODY DRAGGING slot [2]."
    )
    SwitchWeaponObjective("usrif_m4scope_bodydrag")

    CreateTask("EpiPen\n")
    TaskObjectives(
        "The EPIPEN is used to revive downed teammates. When you do, they will be in critical condition, so make sure to heal them up with the medic bag right away.\n\n\r"
        "Objective - Equip the EPIPEN [5]"
    )
    SwitchWeaponObjective("epipen")

    CreateTask("Excellent work!\n\n")
    TaskObjectives(
        "You have completed this chapter! Press CAPS LOCK to start the next chapter."
    )
    ChapterCompletedSound()



    CreateChapter("BREACHER", 0, 5)
    CreateTask("Breacher\n")
    TaskObjectives(
        "As a BREACHER, your role is to be the point man, help the squad traverse obstacles and demolish on enemy assets.\n\n\r"
        "This kit includes explosives, a grappling hook and a shotgun.\n\n\r"
        "Objective - Pick up the BREACHER kit."
    )
    LeaveVehicleButton()
    TeleportAtStart((124.0, 26.0, -60.0))
    SetMarker((124.0, 25.1, -63.0), type="observe")
    breacherkit = ObjectSpawnerTemplate("us_specialist_alt", (124.0, 25.1, -63.0))
    SpawnObject(breacherkit)
    GetKitObjective("us_specialist_alt")

    CreateTask("Grappling hook\n")
    TaskObjectives(
        "Equip your grappling hook [6].\n\n\r"
        "Press [LMB] for a full strength throw or hold [RMB] to control the strength of the throw. Press your ENTER/EXIT keybind [E] to climb.\n\n\r"
        "Objective - Climb over the fence to the marker."
    )
    CreateSquad()
    SetMarker((124.0, 26.0, -100.0), type="move")
    MoveToPositionObjective((124.0, 26.0, -100.0), 3)

    CreateTask("FOB hunt\n")
    TaskObjectives(
        "Don't forget your rope - press your pickup keybind [G] to pick it up.\n\n\r"
        "Find the enemy FOB reported in Golf 10, keypad 9 (G10kp9).\n\n\r"
        "Objective - Locate the enemy FOB."
    )
    SetMarker((27.0, 26.0, -201.0), type="observe")
    enemyfob = ObjectSpawnerTemplate("fixed_firebase", (27.0, 26.0, -201.0), ROT_NORTH, TEAM_ENEMY)
    SpawnObject(enemyfob)
    MoveToPositionObjective((27.0, 26.0, -201.0), 5)

    CreateTask("Explosives\n")
    TaskObjectives(
        "Use C4 (weapon slot 7) to demolish enemy Forward Operating Bases and other assets.\n\n\r"
        "Make sure your teammates keep clear of the C4. It has a delayed fuze time of 20 seconds.\n\n\r"
        "Objective - Place a C4 on the enemy FOB."
    )
    SetMarker((27.0, 26.0, -201.0), type="destroy")
    DamageTargetObjective(enemyfob, 200)

    CreateTask("Excellent work!\n\n")
    TaskObjectives(
        "You have completed this chapter! Press CAPS LOCK to start the next chapter."
    )
    ChapterCompletedSound()



    CreateChapter("ANTI TANK", 0, 6)
    # This creates the first task and sets it to active. The objective title will be this text.
    CreateTask("Light Anti-tank\n")
    # Teleport the player to the relevant spot at the start of the task.
    TeleportAtStart(POS_FIRINGRANGE_100M)
    # These will play a sound file, activate subtitles (on the bottom), and add text to the objective list (on the left)
    TaskObjectives(
        "The main purpose of a Light Anti-Tank (LAT) is to repel/disable enemy armour and destroy light vehicles.\n\n\r"
        "Objective - Pick up the LAT kit [G]."
    )
    LeaveVehicleButton()
    #TaskImage("Ingame\Vehicles\Icons\Minimap\mini_SquadMedium_1.dds")
    # This will define a spawner for a single object.
    # position / rotation / team can also be set. The default position is the player's.
    usatkit = ObjectSpawnerTemplate("us_riflemanat", (-404.0, 26.5, 17.0))
    # The kit will be spawned and picked up. The order of any task components does not matter.
    SpawnObject(usatkit)
    PickupKit("us_riflemanat")
    GetKitObjective("us_riflemanat")


    CreateTask("Light Anti-tank")
    TaskObjectives(
        "Use the AT4 launcher to hit the marked vehicle. Press REARM in the tutorial menu if needed.\n\n\r"
        "Note - Each launcher has a different arming distance. If you are too close, the warhead will not explode.\n\n\r"
        "Objective - Hit the target (50m)."
    )
    TeleportAtStart((-384.0, 26.5, 22.0))
    SwitchWeapon(4)
    # Define a BTR spawner at a specific position
    SetMarker((-334.0, 26.5, 22.0), type="attack")
    btr = ObjectSpawnerTemplate("ru_apc_btr60", (-334.0, 26.5, 22.0), team=TEAM_ENEMY)
    # Spawn it, but do not keep it alive if the current task ends.
    SpawnObject(btr, keep=False)
    # Our objective: Deal 200 damage to the btr.
    DamageTargetObjective(btr, 200)

    CreateTask("Light Anti-tank\n")
    TaskObjectives(
        "Hold the MAIN RADIO keybind [Q] to adjust iron sights while aiming down range.\n"
        "Hold [SHIFT] to zoom in slightly when using iron sights. Press REARM in the tutorial menu if needed.\n\n\r"
        "Objective - Hit the target (300m)."
    )
    # Rearm the player
    RearmPlayer()
    SwitchWeapon(4)
    TeleportAtStart(POS_FIRINGRANGE_300M)
    SetMarker((-90.0, 27.0, 190.0), type="attack")
    btr = ObjectSpawnerTemplate("ru_apc_btr60", POS_TARGET_300M, team=TEAM_ENEMY)
    SpawnObject(btr, keep=False)
    DamageTargetObjective(btr, 200)

    CreateTask("Light Anti-tank\n")
    TaskObjectives(
        "Pick up the new kit [G] and equip the RPG [4]. Small and medium RPG warheads are zeroed at 200m. Hit the new target.\n"
        "Press REARM in the tutorial menu if needed.\n\n\r"
        "Objective - Hit the target (50m)."
    )
    TeleportAtStart((-384.0, 27.5, 22.0))
    ruatkit = ObjectSpawnerTemplate("ru_riflemanat_alt", (-383.0, 26.5, 22.0))
    SpawnObject(ruatkit)
    PickupKit(ruatkit)
    SwitchWeapon(4)
    SetMarker((-333.0, 26.5, 22.0), type="attack")
    hmmwv = ObjectSpawnerTemplate("us_jep_hmmwv", (-333.0, 26.5, 22.0), team=TEAM_ENEMY)
    SpawnObject(hmmwv, keep=False)
    DamageTargetObjective(hmmwv, 200)

    CreateTask("Light Anti-tank\n")
    TaskObjectives(
        "Hit the new target with your second round.\n"
        "Press REARM in the tutorial menu if needed.\n\n\r"
        "Objective - Hit the target (200m)."
    )
    TeleportAtStart((-389.0, 26.0, 136.0))
    SetMarker((-190.0, 27.0, 136.0), type="attack")
    hmmwv = ObjectSpawnerTemplate("us_jep_hmmwv", POS_TARGET_200M, team=TEAM_ENEMY)
    SpawnObject(hmmwv, keep=False)
    DamageTargetObjective(hmmwv, 200)

    CreateTask("Light Anti-tank\n")
    TaskObjectives(
        "Pick up the new kit [G] and equip the Panzerfaust [4]. Some AT launchers are fitted with a fixed scope.\n"
        "Hit the target using the reticle for 200 meters. Press REARM in the tutorial menu if needed.\n\n\r"
        "Objective - Hit the target (200m)."
    )
    UnspawnObject(usatkit)
    TeleportAtStart((-389.0, 26.0, 136.0))
    geratkit = ObjectSpawnerTemplate("ger_riflemanat", (-388.0, 26.5, 136.0))
    SpawnObject(geratkit)
    PickupKit(geratkit)
    SwitchWeapon(4)
    SetMarker((-190.0, 27.0, 136.0), type="attack")
    btr = ObjectSpawnerTemplate("ru_apc_btr60", POS_TARGET_200M, team=TEAM_ENEMY)
    SpawnObject(btr, keep=False)
    DamageTargetObjective(btr, 200)

    CreateTask("Heavy Anti-tank\n")
    # Subtitles and objectives can use localization strings, Note that only "prhelp.utxt" is loaded for these.
    #VoiceOverAtStart("voicefile.wav", 1.0, "HUD_HELP_WEAPON_HANDHELD_SHOVEL_CONTROLS_BUILDING", 20.0)
    #TaskObjectives("HUD_HELP_COMMANDER_commanderApply")
    TaskObjectives(
        "Pick up the new kit [G]. Some handheld and deployable AT launchers require the user to hold the [LMB] to launch the missile and then guide it until the target is destroyed.\n\n\r"
        "Objective - Hit the moving target."
    )
    UnspawnObject(ruatkit)
    TeleportAtStart(POS_TOWER_500M)
    ushatkit = ObjectSpawnerTemplate("usa_at", (-381.0, 30.0, 260.0))
    SpawnObject(ushatkit)
    PickupKit(ushatkit)
    SwitchWeapon(4)
    btr = ObjectSpawnerTemplate("ru_apc_btr60", POS_TARGET_400M, team=TEAM_ENEMY)
    SpawnObject(btr, keep=False)
    # This tells the BTR to patrol between `points` at the speed `speed`.
    FollowPathAction(btr, points=[(0.0, 27.0, 425.0), POS_TARGET_400M], speed=4.0)
    # This time our objective is to destroy it, and not just damage it.
    DestroyTargetObjective(btr)

    CreateTask("Heavy Anti-tank\n")
    # Subtitles and objectives can use localization strings, Note that only "prhelp.utxt" is loaded for these.
    #VoiceOverAtStart("voicefile.wav", 1.0, "HUD_HELP_WEAPON_HANDHELD_SHOVEL_CONTROLS_BUILDING", 20.0)
    #TaskObjectives("HUD_HELP_COMMANDER_commanderApply")
    TaskObjectives(
        "Pick up the new kit [G]. Some handheld and deployable AT launchers come with thermal vision, or different firing modes.\n\n\r"
        "When aiming, hold your MAIN RADIO [Q] to switch firing modes. Hold your SECONDARY RADIO [T] to toggle thermals.\n\n\r"
        "Objective - Hit the moving target."
    )
    gerhatkit = ObjectSpawnerTemplate("ger_at", (-381.0, 30.0, 260.0))
    UnspawnObject(geratkit)
    SpawnObject(gerhatkit)
    PickupKit(gerhatkit)
    SwitchWeapon(4)
    btr = ObjectSpawnerTemplate("ru_apc_btr60", POS_TARGET_400M, team=TEAM_ENEMY)
    SpawnObject(btr, keep=False)
    # This tells the BTR to patrol between `points` at the speed `speed`.
    FollowPathAction(btr, points=[(0.0, 27.0, 425.0), POS_TARGET_400M], speed=4.0)
    # This time our objective is to destroy it, and not just damage it.
    DestroyTargetObjective(btr)

    CreateTask("Anti-tank vehicle - SPG")
    VoiceOverAtStart(
        "voicefile.wav",
        1.0,
        "In every armed vehicle, upon entering a gunner seat, you must wait until the gun is operational.\n",
        20.0
    )
    TaskObjectives(
        "Objective - Enter the gunner seat of the SPG technical\n\n\r"
        "1. Press your ENTER/EXIT keybind [E] to enter the vehicle\n"
        "2. While in the vehicle, switch to the gunner seat [F2].\n"
    )
    TeleportAtStart(POS_FIRINGRANGE_600M)
    spg = ObjectSpawnerTemplate("civ_atm_technical", POS_PLAYERFRONT, ROT_EAST)
    SpawnObject(spg)
    # Objective completes when the player enters a seat whose template contains this text
    GetInSeatObjective("spg")

    CreateTask("Anti-tank vehicle - SPG")
    TaskObjectives(
        "Press [RMB] to toggle the sight. Numbers on the right side represent hundreds of meters. Aim with the chevrons in the middle and lead your shot.\n\n\r"
        "Objective - Hit the moving target (500m)."
    )
    btr = ObjectSpawnerTemplate("ru_apc_btr60", POS_TARGET_500M, team=TEAM_ENEMY)
    SpawnObject(btr, keep=False)
    FollowPathAction(btr, points=[(110.0, 27.0, 430.0), POS_TARGET_500M], speed=6.0)
    DestroyTargetObjective(btr)

    CreateTask("Deployable Anti-tank Launcher")
    VoiceOverAtStart("voicefile.wav", 1.0, "", 20.0)
    TaskObjectives(
        "Equip the shovel [2] and hold [LMB] on the TOW. Build it until the progress bar disappears.\n"
        "Pick up the RIFLEMAN kit and throw the AMMO BAG onto the TOW to rearm it. Press your ENTER/EXIT keybind [E] to enter it.\n\n\r"
        "Objective - Enter the launcher."
    )
    LeaveVehicleButton()
    UnspawnObject(spg)
    tow = ObjectSpawnerTemplate("deployable_tow", POS_PLAYERFRONT, ROT_EAST)
    SpawnObject(tow, keep=False)
    ammokit = ObjectSpawnerTemplate("us_rifleman", POS_PLAYERFRONT)
    SpawnObject(ammokit)
    PickupKit(ammokit)
    SwitchWeapon(2)
    GetInVehicleBySpawnerObjective(tow)

    CreateTask("Deployable Anti-tank Launcher")
    TaskObjectives(
        "Destroy the moving target using the anti-tank launcher. To launch the missile, press and hold [LMB].\n\n\r"
        "Objective - Destroy the moving target."
    )
    SetMarker((110.0, 27.0, 280.0), type="observe")
    btr = ObjectSpawnerTemplate("ru_apc_btr60", POS_TARGET_500M, team=TEAM_ENEMY)
    SpawnObject(btr, keep=False)
    FollowPathAction(btr, points=[(110.0, 27.0, 460.0), POS_TARGET_500M], speed=6.0)
    DestroyTargetObjective(btr)

    CreateTask("Anti-tank vehicle - ATGM")
    VoiceOverAtStart("voicefile.wav", 1.0, "", 20.0)
    TaskObjectives(
        "Press your ENTER/EXIT keybind [E] to enter the vehicle. While in the vehicle, switch to the gunner seat [F2].\n\n\r"
        "Objective - Enter the gunner seat of the AT vehicle."
    )
    LeaveVehicleButton()
    UnspawnObject(tow)
    shturm = ObjectSpawnerTemplate("ru_atm_shturm", POS_PLAYERFRONT, ROT_EAST)
    SpawnObject(shturm)
    GetInSeatObjective("gunner")

    CreateTask("Anti-tank vehicle - ATGM")
    TaskObjectives(
        "Hitting the front armour is not effective. Rear/side armour is weaker - always aim for the weak spots.\n\n\r"
        "Objective - Destroy the moving target."
    )
    SetMarker((110.0, 27.0, 280.0), type="observe")
    tank = ObjectSpawnerTemplate("us_tnk_m1a2", POS_TARGET_500M, team=TEAM_ENEMY)
    SpawnObject(tank, keep=False)
    FollowPathAction(tank, points=[(-350.0, 25.5, 280.0), POS_TARGET_500M], speed=6.0)
    DestroyTargetObjective(tank)

    CreateTask("Excellent work!\n\n")
    TaskObjectives(
        "You have completed this chapter! Press CAPS LOCK to start the next chapter."
    )
    LeaveVehicleButton()
    UnspawnObject(shturm)
    ChapterCompletedSound()



    CreateChapter("AUTOMATIC RIFLEMAN", 0, 7)

    CreateTask("AR")
    TaskObjectives(
        "As the AUTOMATIC RIFLEMAN (AR), your role is to suppress enemy positions and cover the squad when it's crossing open areas.\n\n\r"
        "Objective - Pick up the AUTOMATIC RIFLEMAN kit [G]."
    )
    LeaveVehicleButton()
    TeleportAtStart(POS_FIRINGRANGE_100M)
    SetMarker((-404.0, 26.5, 17.0), type="observe")
    usarkit = ObjectSpawnerTemplate("us_support", (-404.0, 26.5, 17.0))
    SpawnObject(usarkit)
    GetKitObjective("us_support")

    CreateTask("AR")
    TaskObjectives(
        "Most AR weapons have a separate weapon slot to deploy the bipod, which reduces recoil.\n\n\r"
        "Objective - Select the DEPLOYED weapon slot [4]."
    )
    SwitchWeaponObjective("deploy")

    CreateTask("AR")
    TaskObjectives(
        "Aim down sights [RMB] to deploy the bipod and hit the marked target with automatic fire.\n\n\r"
        "Objective - Hit the target."
    )
    TeleportAtStart((-383.0, 26.0, 18.6))
    target = ObjectSpawnerTemplate("target_pr_dynamic", (-284.0, 24.990, 18.6), rot=ROT_WEST, team=TEAM_ENEMY)
    SpawnObject(target)
    SetMarker((-284.0, 24.990, 18.6), "attack")
    DamageTargetObjective(target, 800)

    CreateTask("Excellent work!\n\n")
    TaskObjectives(
        "You have completed this chapter! Press CAPS LOCK to start the next chapter."
    )
    LeaveVehicleButton()
    UnspawnObject(shturm)
    ChapterCompletedSound()

    

    CreateChapter("GRENADIER", 0, 8)

    CreateTask("Grenadier")
    TaskObjectives(
        "The GRENADIER kit includes an under-barrel grenade launcher (UGL). It provides the squad with extra firepower.\n\n\r"
        "Objective - Pick up the GRENADIER kit [G]."
    )
    LeaveVehicleButton()
    TeleportAtStart(POS_FIRINGRANGE_100M)
    SetMarker((-404.0, 26.5, 17.0), type="observe")
    usgrenkit = ObjectSpawnerTemplate("us_assault", (-404.0, 26.5, 17.0))
    SpawnObject(usgrenkit)
    GetKitObjective("us_assault")

    CreateTask("Grenadier")
    TaskObjectives(
        "Hold the MAIN RADIO keybind [Q] to adjust iron sights while aiming down range.\n"
        "Hold [SHIFT] to zoom in slightly when using iron sights.\n\n\r"
        "Objective - Hit the target (100m)."
    )
    SwitchWeapon(4)
    TeleportAtStart((-383.0, 26.0, 18.6))
    target = ObjectSpawnerTemplate("target_pr_dynamic", (-284.0, 24.990, 18.6), rot=ROT_WEST, team=TEAM_ENEMY)
    SpawnObject(target)
    SetMarker((-284.0, 24.990, 18.6), "attack")
    DamageTargetObjective(target, 100)

    CreateTask("Grenadier")
    TaskObjectives(
        "Hold the MAIN RADIO keybind [Q] to adjust iron sights while aiming down range.\n"
        "Hold [SHIFT] to zoom in slightly when using iron sights.\n\n\r"
        "Objective - Hit the target (200m)."
    )
    TeleportAtStart((-383.0, 26.0, 136.0))
    target = ObjectSpawnerTemplate("target_pr_dynamic", (-183.0, 24.990, 136.0), rot=ROT_WEST, team=TEAM_ENEMY)
    SpawnObject(target)
    SetMarker((-183.0, 24.990, 136.0), "attack")
    DamageTargetObjective(target, 100)

    CreateTask("Grenadier")
    TaskObjectives(
        "The grenade launcher is especially useful for clearing interiors from a distance.\n"
        "Fire a grenade through the window to splash the wall inside. Note the arming distance - grenades won't explode if you're too close.\n\n\r"
        "Objective - Hit the target (50m)."
    )
    TeleportAtStart((30.0, 26.0, -335.5))
    target = ObjectSpawnerTemplate("target_pr_dynamic_nocol", (45.3, 25.5, -334.2), rot=ROT_SOUTH, team=TEAM_ENEMY)
    SpawnObject(target)
    SetMarker((47.5, 26.0, -335.5), "attack")
    DamageTargetObjective(target, 100)

    CreateTask("Excellent work!\n\n")
    TaskObjectives(
        "You have completed this chapter! Press CAPS LOCK to start the next chapter."
    )
    ChapterCompletedSound()






    # EXAMPLE (advanced):
    # You can create your own components for tasks

    class ExampleTaskComponent(TaskComponent):
        def __init__(self, examplearg):
            TaskComponent.__init__(self)
            self.examplearg = examplearg

        def start(self):
            rdebug.debugMessage("start: Set up timers/events here, or run your action directly")

        def stop(self):
            rdebug.debugMessage("stop: clean up")

        # This is called at 30hz between start and stop.
        # heavy things here will cause low fps.
        def think(self):
            pass

    # EXAMPLE (advanced):
    # You can create your own objectives for tasks.
    # Objective inherits from TaskComponent and adds checkCompletion, which is called at 30hz and should return True when task is completed.
    import time
    class ExampleObjective(Objective):
        def __init__(self, time):
            Objective.__init__(self)
            self.time = time
            self.startTime = None

        def start(self):
            rdebug.debugMessage("start: Set up timers/events here")
            self.startTime = time.time()

        def stop(self):
            rdebug.debugMessage("stop: clean up")
            self.startTime = None

        def checkCompletion(self):
            return time.time() - self.startTime > self.time






def advanced():
    SetMainMenuButtonText(1, "ADVANCED")

    CreateChapter("MORTARS", 1, 0)

    CreateTask("Mortar")
    TaskObjectives(
        "The MORTAR squad can build two mortar pits next to an FOB with two supply crates. Use the shovel to build it and enter it once completed.\n\n\r"
        "Objective - Build the mortar pit and man it [E].")
    LeaveVehicleButton()
    CreateSquad()
    TeleportAtStart((-406.0, 27.0, 285.0))
    crate1 = ObjectSpawnerTemplate("pr_supply_crate_us", (-410.0, 27.0, 284.0))
    SpawnObject(crate1)
    crate2 = ObjectSpawnerTemplate("pr_supply_crate_us", (-410.0, 27.0, 286.0))
    SpawnObject(crate2)
    mortar = ObjectSpawnerTemplate("deployable_mortar_m252", (-400.0, 25.0, 285.0), ROT_EAST)
    SpawnObject(mortar)
    GetInSeatObjective("mortar")

    CreateTask("Mortar")
    TaskObjectives(
        "You need to know the range to the target before firing. As a SQUAD LEADER you can find it below the SQUAD/KIT menu map.\n\n\r"
        "Rotate the mortar using your LEFT [A] and RIGHT [D] keys.\n\n\r"
        "Objective - Press CONTINUE to proceed.")
    SetMarker((100.0, 26.0, 285.0), "observe")
    ClickContinueObjective()

    CreateTask("Mortar")
    TaskObjectives(
        "Use weapon slot buttons [1-3] to change the round type. Press [4] to open the angle calculator.\n\n\r"
        "Input the range (500) to calculate the angle. Adjust your angle using your FORWARD [W] and BACKWARD [S] keys.\n\n\r"
        "Objective - Press CONTINUE to proceed.")
    ClickContinueObjective()

    CreateTask("Mortar")
    TaskObjectives(
        "Press [1] to select the HE round. Fire 5 rounds at the target when ready. \n\n\r"
        "Press [R] to prepare new rounds. Press REARM in the tutorial menu if needed.\n\n\r"
        "Objective - Destroy the target.")
    SetMarker((100.0, 26.0, 285.0), "attack")
    target = ObjectSpawnerTemplate("civ_atm_technical", (100.0, 26.0, 287.0), ROT_NORTH, TEAM_ENEMY)
    SpawnObject(target)
    DestroyTargetObjective(target)

    CreateTask("Excellent work!\n\n")
    TaskObjectives(
        "You have completed this chapter! Press CAPS LOCK to start the next chapter."
    )
    ChapterCompletedSound()


    CreateChapter("ARMOUR", 1, 1)

    CreateTask("Armour - introduction")
    TaskObjectives(
        "Armoured vehicles require two crewmen - a DRIVER and a GUNNER - to be properly manned.\n\n\r"
        "Use your SECONDARY RADIO [T] to request the crewman kit directly from the vehicle. Press [G] to pick it up.\n\n\r"
        "Objective - Request the crewman kit.")
    VoiceOverAtStart(
        "voicefile.wav",
        1.0,
        "On most servers armoured vehicles are claimable by specific squad names - APC or TANK.\n",
        20.0
    )
    LeaveVehicleButton()
    CreateSquad()
    TeleportAtStart((73.0, 26.0, 17.0))
    lav = ObjectSpawnerTemplate("us_apc_lav25", POS_PLAYERFRONT, ROT_EAST)
    SpawnObject(lav)
    GetKitObjective("us_tanker")

    CreateTask("APC")
    TaskObjectives(
        "Armoured personnel carriers (APCs) serve two purposes - engaging light targets and transporting troops.\n\n\r"
        "Use your ENTER/EXIT keybind [E] to enter the APC and switch to the gunner seat [F2].\n\n\r"
        "Objective - Enter the APC gunner seat."
    )
    VoiceOverAtStart(
        "voicefile.wav",
        1.0,
        "When you enter a gunner seat in a live match, you will need to wait 30 seconds before the turret is operational.\nAs a gunner you should never leave your seat unless absolutely necessary.\n",
        20.0
    )
    GetInSeatObjective("gunner")

    CreateTask("Ammunition types")
    TaskObjectives(
        "Most armoured vehicles are supplied with two types of ammunition - Armour Piercing (AP) and High Explosive (HE).\n\n\r"
        "Use your weapon slot buttons [1-2] to select the round type (see bottom right corner). Press the ZOOM keybind [X] to switch between zoom levels.\n\n\r"
        "Objective - Use AP to destroy the target."
    )
    VoiceOverAtStart(
        "voicefile.wav",
        1.0,
        "When firing, a heat bar will appear below your ammo count. If your gun overheats, you won't be able to fire until it cools down.\n",
        20.0
    )
    SetMarker((160.0, 27.0, -9.0), "attack")
    btr = ObjectSpawnerTemplate("ru_apc_btr60", (160.0, 26.0, -9.0), ROT_WEST, team=TEAM_ENEMY)
    SpawnObject(btr, keep=False)
    DestroyTargetObjective(btr)

    CreateTask("Thermal sights")
    TaskObjectives(
        "Modern turrets are equipped with thermal imagery. Hold the SECONDARY RADIO [T] to toggle your thermal sight.\n\n\r"
        "There is a hostile AT vehicle lurking in the forest. Use your thermal sight and zoom to find it.\n\n\r"
        "Objective - Destroy the hidden target."
    )
    shturm = ObjectSpawnerTemplate("ru_atm_shturm", (197.0, 26.0, 52.0), ROT_WEST, team=TEAM_ENEMY)
    SpawnObject(shturm, keep=False)
    DestroyTargetObjective(shturm)

    CreateTask("Tanks")
    TaskObjectives(
        "Tanks are engineered to withstand smaller AT projectiles. Their main purpose is destroying enemy armour and breaking through heavy defenses.\n\n\r"
        "Jump on top of the tank and get inside [E]. Then, switch to the gunner seat [F2].\n\n\r"
        "Objective - Enter the gunner seat."
    )
    LeaveVehicleButton()
    TeleportAtStart(POS_FIRINGRANGE_800M)
    UnspawnObject(lav)
    t55 = ObjectSpawnerTemplate("mil_tnk_t55", (-397.0, 26.0, 420.0), ROT_EAST)
    SpawnObject(t55)
    GetInSeatObjective("t55_Gun")

    CreateTask("Range adjustment")
    TaskObjectives(
        "Switch your round type to HEAT [2] - it is the most effective against emplacements. Remember, switching round types takes time.\n\n\r"
        "Hold your MAIN RADIO [Q] to adjust the range(bottom right corner).\n\n\r"
        "Objective - Destroy the FOB (800m)."
    )
    VoiceOverAtStart(
        "voicefile.wav",
        1.0,
        "Note - High explosive (HEAT) and fragmentation (FRAG) rounds have less velocity and more bullet drop compared to armour piercing (AP) rounds.\n",
        20.0
    )
    SetMarker((413.0, 26.0, 406.0), "attack")
    enemyfob = ObjectSpawnerTemplate("fixed_firebase", (413.0, 26.0, 406.0), ROT_NORTH, TEAM_ENEMY)
    SpawnObject(enemyfob)
    DestroyTargetObjective(enemyfob)

    CreateTask("FRAG")
    TaskObjectives(
        "Switch your round type to FRAG [3] - it has more splash damage, which is deadly against infantry.\n\n\r"
        "The target is hidden behind the wall - hit the ground behind it to damage the target.\n\n\r"
        "Objective - Damage the target (300m)."
    )
    UnspawnObject(enemyfob)
    wall = ObjectSpawnerTemplate("concrete_pillar_wall", (-100.0, 25, 431.0), ROT_WEST)
    SpawnObject(wall)
    target = ObjectSpawnerTemplate("target_pr_dynamic", (-97.0, 24.990, 426.0), ROT_WEST, TEAM_ENEMY)
    SpawnObject(target)
    SetMarker((-100.0, 26.0, 422.0), "attack")
    DamageTargetObjective(target, 10)

    CreateTask("Rangefinder")
    TaskObjectives(
        "Modern armoured vehicles have a laser rangefinder built into the sighting device.\n\n\r"
        "Note, that certain sights will require you to readjust your aim after lazing.\n\n\r"
        "Objective - Enter the gunner seat."
    )
    LeaveVehicleButton()
    UnspawnObject(t55)
    UnspawnObject(target)
    UnspawnObject(wall)
    TeleportAtStart((-405.0, 27.5, 410.0))
    m1a2 = ObjectSpawnerTemplate("us_tnk_m1a2", (-397.0, 26.0, 410.0), ROT_EAST)
    SpawnObject(m1a2)
    GetInSeatObjective("a2_gun")

    CreateTask("Rangefinder")
    TaskObjectives(
        "This particular tank automatically adjusts your barrel. Zoom in [X], look at the target and press [C] to laze it.\n\n\r"
        "Objective - Destroy the target using AP."
    )
    SetMarker((413.0, 26.0, 416.0), "attack")
    enemytank = ObjectSpawnerTemplate("mil_tnk_t55", (313.0, 26.0, 416.0), ROT_NORTH, TEAM_ENEMY)
    SpawnObject(enemytank)
    DestroyTargetObjective(enemytank)

    CreateTask("Coaxial machine gun")
    TaskObjectives(
        "Press the CYCLE WEAPONS keybind [F] to switch to your coaxial machine gun.\n\n\r"
        "Objective - Hit the target with COAX."
    )
    target = ObjectSpawnerTemplate("target_pr_dynamic", (200.0, 24.990, 406.0), ROT_WEST, TEAM_ENEMY)
    SpawnObject(target)
    SetMarker((200.0, 26.0, 406.0), "attack")
    DamageTargetObjective(target, 100)

    CreateTask("Smoke")
    TaskObjectives(
        "Heavy damage to the vehicle might disable your turret. If this happens, your ammo count will turn red.\n\n\r"
        "If you're in danger use the thermal smoke grenade launchers [3] and retreat using the smokescreen as cover.\n\n\r"
        "Objective - Press CONTINUE to proceed."
    )
    SetObjectHealth(m1a2, 0.15)
    UnspawnObject(target)
    t90_1 = ObjectSpawnerTemplate("ru_tnk_t90", (-365.0, 26.0, 415.0), ROT_WEST)
    SpawnObject(t90_1, keep=False)
    t90_2 = ObjectSpawnerTemplate("ru_tnk_t90", (-365.0, 26.0, 410.0), ROT_WEST)
    SpawnObject(t90_2, keep=False)
    t90_3 = ObjectSpawnerTemplate("ru_tnk_t90", (-365.0, 26.0, 405.0), ROT_WEST)
    SpawnObject(t90_3, keep=False)
    ClickContinueObjective()

    CreateTask("Excellent work!\n\n")
    TaskObjectives(
        "You have completed this chapter! Press CAPS LOCK to start the next chapter."
    )
    ChapterCompletedSound()

def addSandboxVehicles():
    tank500 = ObjectSpawnerTemplate("ru_apc_btr60", POS_TARGET_500M, team=TEAM_ENEMY)
    SpawnObject(tank500, respawn=True)
    FollowPathAction(tank500, points=[(100.0, 27.0, 400.0), POS_TARGET_500M], speed=8.0)

    tank400 = ObjectSpawnerTemplate("ru_apc_btr60", POS_TARGET_400M, team=TEAM_ENEMY)
    SpawnObject(tank400, respawn=True)
    FollowPathAction(tank400, points=[(0.0, 27.0, 400.0), POS_TARGET_400M], speed=8.0)

    tank300 = ObjectSpawnerTemplate("ru_apc_btr60", POS_TARGET_300M, team=TEAM_ENEMY)
    SpawnObject(tank300, respawn=True)
    FollowPathAction(tank300, points=[(-90.0, 27.0, 400.0), POS_TARGET_300M], speed=8.0)

    tank200 = ObjectSpawnerTemplate("ru_apc_btr60", POS_TARGET_200M, team=TEAM_ENEMY)
    SpawnObject(tank200, respawn=True)
    FollowPathAction(tank200, points=[(-190.0, 27.0, 400.0), POS_TARGET_200M], speed=8.0)

    tank100 = ObjectSpawnerTemplate("ru_apc_btr60", POS_TARGET_100M, team=TEAM_ENEMY)
    SpawnObject(tank100, respawn=True)
    FollowPathAction(tank100, points=[(-290.0, 27.0, 400.0), POS_TARGET_100M], speed=8.0)

    # target_test = ObjectSpawnerTemplate("target_pr_dynamic", (-290.0, 32.0, 17.0), team=TEAM_ENEMY)
    # SpawnObject(target_test, respawn=True)
    # FollowPathAction(target_test, points=[(-290.0, 32.0, 117.0), (-290.0, 32.0, 17.0)], speed=8.0)


    flyingtarget = ObjectSpawnerTemplate("us_the_uh1c", (0.0, 100.0, 270.0), team=TEAM_ENEMY)
    flyingbigtarget = ObjectSpawnerTemplate("us_the_chinook", (100.0, 100.0, 270.0), team=TEAM_ENEMY)
    SpawnObject(flyingtarget, respawn=True)
    SpawnObject(flyingbigtarget, respawn=True)
    FollowPathAction(flyingtarget, points=[(0.0, 100.0, -270.0), (0.0, 100.0, 670.0)], speed=25.0)
    FollowPathAction(flyingbigtarget, points=[(100.0, 100.0, -270.0), (100.0, 100.0, 670.0)], speed=30.0)

    flyingtarget = ObjectSpawnerTemplate("us_the_uh1c", (-100.0, 80.0, 270.0), team=TEAM_ENEMY)
    flyingbigtarget = ObjectSpawnerTemplate("us_the_chinook", (-200.0, 80.0, 270.0), team=TEAM_ENEMY)
    SpawnObject(flyingtarget, respawn=True)
    SpawnObject(flyingbigtarget, respawn=True)
    FollowPathAction(flyingtarget, points=[(-100.0, 80.0, -270.0), (-100.0, 80.0, 670.0)], speed=25.0)
    FollowPathAction(flyingbigtarget, points=[(-200.0, 80.0, -270.0), (-200.0, 80.0, 670.0)], speed=30.0)

    flyingtarget = ObjectSpawnerTemplate("us_the_uh1c", (-250.0, 60.0, 70.0), team=TEAM_ENEMY)
    flyingbigtarget = ObjectSpawnerTemplate("us_the_chinook", (-300.0, 60.0, 270.0), team=TEAM_ENEMY)
    SpawnObject(flyingtarget, respawn=True)
    SpawnObject(flyingbigtarget, respawn=True)
    FollowPathAction(flyingtarget, points=[(-250.0, 60.0, -270.0), (-250.0, 60.0, 670.0)], speed=25.0)
    FollowPathAction(flyingbigtarget, points=[(-300.0, 60.0, -270.0), (-300.0, 60.0, 670.0)], speed=30.0)



AllTeams =  ['ch', 'gb', 'mec', 'us', 'usa', 'fsa', 'cf', 'chinsurgent', 'meinsurgent', 'pl', 'ru', 'arf', 'taliban',
                    'idf', 'hamas', 'ger', 'vnusa', 'vnusmc', 'vnnva', 'gb82', 'arg82', 'fr', 'nl', 'ww2ger', 'ww2usa']



def sandbox():
    SetMainMenuButtonText(2, "SANDBOX")

    CreateChapter("ANTI TANK", 2, 0)
    CreateTask()
    # Weapons
    TeleportAtStart((-400.0, 27.0, 131.0))
    SpawnObject(ObjectSpawnerTemplate("ru_at", (-400.0, 26.0, 130.0)), respawn=True)
    SpawnObject(ObjectSpawnerTemplate("ru_riflemanat", (-400.0, 26.0, 140.0)), respawn=True)
    SpawnObject(ObjectSpawnerTemplate("us_at", (-400.0, 26.0, 150.0)), respawn=True)
    SpawnObject(ObjectSpawnerTemplate("us_riflemanat", (-400.0, 26.0, 160.0)), respawn=True)
    SpawnObject(ObjectSpawnerTemplate("us_riflemanat_alt", (-400.0, 26.0, 170.0)), respawn=True)
    SpawnObject(ObjectSpawnerTemplate("civ_atm_technical", (-400.0, 27.0, 180.0), rot=ROT_EAST), respawn=True)
    SpawnObject(ObjectSpawnerTemplate("deployable_tow", (-400.0, 27.0, 190.0), rot=ROT_EAST), respawn=True)
    SpawnObject(ObjectSpawnerTemplate("ru_atm_shturm", (-400.0, 27.0, 200.0), rot=ROT_EAST), respawn=True)
    SpawnObject(ObjectSpawnerTemplate("ru_atm_spandrel", (-400.0, 27.0, 210.0), rot=ROT_EAST), respawn=True)
    SpawnObject(ObjectSpawnerTemplate("gb_aav_stormer", (-400.0, 27.0, 220.0), rot=ROT_EAST), respawn=True)
    addSandboxVehicles()



    CreateChapter("GRENADIER", 2, 1)
    CreateTask()
    # Weapons
    TeleportAtStart((-400.0, 27.0, 131.0))
    pos = (-400.0, 25.5, 136.0)
    i = 0
    for team in AllTeams:
        kitname = "%s_assault" % team
        if rkits.kitExists(kitname):
            SpawnObject(ObjectSpawnerTemplate(kitname, pos=(pos[0], pos[1], pos[2] + i * 3) ), respawn=True)
            i += 1



    CreateChapter("AUTOMATIC RIFLEMAN", 2, 2)
    CreateTask()
    # Weapons
    TeleportAtStart((-400.0, 27.0, 131.0))
    pos = (-400.0, 25.5, 136.0)
    i = 0
    for team in AllTeams:
        kitname = "%s_support" % team
        if rkits.kitExists(kitname):
            SpawnObject(ObjectSpawnerTemplate(kitname, pos=(pos[0], pos[1], pos[2] + i * 3) ), respawn=True)
            i += 1

        kitname = "%s_mg" % team
        if rkits.kitExists(kitname):
            SpawnObject(ObjectSpawnerTemplate(kitname, pos=(pos[0], pos[1], pos[2] + i * 3) ), respawn=True)
            i += 1



    CreateChapter("DEPLOYABLES", 2, 3)
    CreateTask()
    addSandboxVehicles()
    TeleportAtStart((-400.0, 27.0, 131.0))
    pos = (-400.0, 25.5, 136.0)
    i = 0
    templates = {}
    for type in ["ANTIAIR_TEMPLATES", "HMG_TEMPLATES", "TOW_TEMPLATES",
                 "MORTAR_TEMPLATES", "FOXHOLE_TEMPLATES", "RAZORWIRES_TEMPLATES", "SANDBAGS_TEMPLATES"]:
        templates[type] = set()
        templates[type].update(sum(cfg.C[type].values(), []))
    for type in templates:
        for deployableTemplate in templates[type]:
            template = ObjectSpawnerTemplate(deployableTemplate, pos=(pos[0], pos[1], pos[2] + i * 6), rot=ROT_EAST)
            SpawnObject(template)
            SetObjectHealth(template, 1.0)
            i += 1





###to do / untested old stuff
##############
#def assets():
    ### assets
    CreateChapter("assets", 3, 2)

    CreateTask("Get in the logistics truck")
    CreateSquad()
    TeleportAtStart((221.0, 26.0, -253.0))
    SpawnObject(ObjectSpawnerTemplate("mec_trk_logistics", POS_PLAYERFRONT, ROT_NORTH))
    GetInSeatObjective("logistic")

    pos = (102.0, 26.0, -366.0)
    CreateTask("Drive the truck to the position marked on your map")
    SetMarker(pos, "move")
    MoveToPositionObjective(pos, 15)

    btr = ObjectSpawnerTemplate("ru_apc_btr60", (-272.0, 26.0, -361.0), team=TEAM_ENEMY)
    SpawnObject(btr)
    SetMarker((-272.0, 1000.0, -361.0), "attack")

    CreateTask("Drop one supply crate")
    BeAroundObjectObjective("pr_supply_crate_mec", 1)

    CreateTask("Get an officer kit from the crate")
    GetKitObjective("officer")

    CreateTask("Deploy a firebase")
    DeployAssetObjective("outpost")

    CreateTask("Get another kit and shovel the firebase")
    BuildAssetObjective("outpost")

    CreateTask("Drop another supply crate")
    BeAroundObjectObjective("pr_supply_crate_gb", 2)

    CreateTask("Deploy an anti tank so it can hit the vehicle to the west")

    DeployAssetObjective("tow")
    BuildAssetObjective("tow")

    CreateTask("Destroy the vehicle with the Anti Tank missile")
    DestroyTargetObjective(btr)
    # CreateChapter("Mortar sandbox", 5, 3)
    # CreateTask("Sandbox")
    # # Weapons
    # TeleportAtStart((-400.0, 27.0, 131.0))
    # pos = (-400.0, 25.5, 136.0)
    # i = 0
    # for team in AllTeams:
    #     if rkits.kitExists(kitname):
    #         SpawnObject(ObjectSpawnerTemplate(kitname, pos=(pos[0], pos[1], pos[2] + i * 3) ), respawn=True)
    #         i += 1
    #
    #     kitname = "%s_mg" % team
    #     if rkits.kitExists(kitname):
    #         SpawnObject(ObjectSpawnerTemplate(kitname, pos=(pos[0], pos[1], pos[2] + i * 3) ), respawn=True)
    #         i += 1
    # addSandboxesVehicles()



    # CreateChapter("grenadier", 1, 0)
    # truck100 = ObjectSpawnerTemplate("ru_trk_logistics", POS_TARGET_100M)
    # truck200 = ObjectSpawnerTemplate("ru_trk_logistics", POS_TARGET_200M)
    # CreateTask("Hit the target: 100m")
    #
    # TeleportAtStart(POS_FIRINGRANGE_100M)
    # kit = ObjectSpawnerTemplate("gb_assault")
    # SpawnObject(kit)
    # PickupKit(kit)
    #
    # SpawnObject(truck100, keep=False)
    # DamageTargetObjective(truck100, 100)
    #
    #
    # CreateTask("Hit the target: 200m")
    # TeleportAtStart(POS_FIRINGRANGE_200M)
    # SpawnObject(truck200, keep=False)
    # DamageTargetObjective(truck200, 100)