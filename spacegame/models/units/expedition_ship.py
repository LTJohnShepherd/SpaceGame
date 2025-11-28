import pygame
from pygame.math import Vector2
from spacegame.models.units.fleet_unit import SpaceUnit
from spacegame.models.units.interceptor import Interceptor
from spacegame.models.units.hangar import Hangar
from spacegame.config import (
    EXPEDITION_MAX_HEALTH,
    HANGAR_SLOT_COUNT,
    INTERCEPTOR_POOL_SIZE,
    IMAGES_DIR,
)

class ExpeditionShip(SpaceUnit):
    """Main player-controlled rectangle with a 3-slot hangar."""
    
    def shape_id(self):
        return "expeditionship"
    
    def get_tier(self) -> int:
        return 0

    def __init__(self, start_pos, **kwargs):
        # load sprite first
        sprite = pygame.image.load(IMAGES_DIR + "/ExpeditionShip.png").convert_alpha()

        # fix orientation (rotate -90 degrees clockwise)
        sprite = pygame.transform.rotate(sprite, -90)

        # use sprite size instead of tiny rectangle
        scaled_sprite = pygame.transform.smoothscale(
            sprite,
            (sprite.get_width() // 4, sprite.get_height() // 4)
        )

        # update ship size
        super().__init__(start_pos, ship_size=scaled_sprite.get_size(), **kwargs)
        self.base_surf = scaled_sprite

        # Increase ExpeditionShip health
        self.max_health = EXPEDITION_MAX_HEALTH
        self.health = self.max_health

                # Hangar system: delegate light-craft management to Hangar helper.
        # Hangar keeps:
        #   - slots: which hangar slots currently have a ready interceptor
        #   - ships: which Interceptor objects are deployed from each slot
        #   - assignments: which pool id is assigned to each slot
        #   - pool: persistent interceptor data for fleet-management screens
        self.hangar_system = Hangar(self, num_slots=HANGAR_SLOT_COUNT, pool_size=INTERCEPTOR_POOL_SIZE)

        # Backwards-compatible aliases so existing screens (fleet management, HUD, etc.)
        # can keep using the older attributes. These all point into the Hangar instance.
        self.hangar = self.hangar_system.slots          # list[bool]: True = interceptor ready in hangar
        self.hangar_ships = self.hangar_system.ships    # list[Interceptor|None]: deployed per-slot ships
        self.interceptor_pool = self.hangar_system.pool # list[dict]: metadata (id, name, alive, tier)
        self.hangar_assignments = self.hangar_system.assignments  # list[int|None]: pool id per slot
        self.deployed = self.hangar_system.deployed     # list[Interceptor]: all currently deployed fighters

        # Remember the last selected light craft for convenience in input handling.
        self.last_selected_light_craft = None
    def can_deploy(self, slot):
        return 0 <= slot < HANGAR_SLOT_COUNT and self.hangar[slot]

    def deploy(self, slot):
        """Spawn a light Interceptor from the given hangar slot near the ExpeditionShip."""
        if not self.can_deploy(slot):
            return None

        # Determine which interceptor from the persistent pool is assigned to this slot (if any)
        interceptor_id = None
        if hasattr(self, "hangar_assignments") and 0 <= slot < len(self.hangar_assignments):
            interceptor_id = self.hangar_assignments[slot]

        # Spawn slightly in front of the rectangle
        offset = Vector2(70, 50).rotate(-self.angle)

        # Look up this interceptor's tier from the Hangar pool data (per-ship).
        tier_value = 0
        if interceptor_id is not None:
            for entry in self.interceptor_pool:
                if entry.get("id") == interceptor_id:
                    tier_value = entry.get("tier", 0)
                    break

        icpt = Interceptor(self.pos + offset, interceptor_id=interceptor_id, tier=tier_value)

        # Remember which slot this light craft came from for recall / docking logic.
        icpt.hangar_slot = slot
        icpt.recalling = False

        # Notify Hangar that an interceptor was deployed so it can update slots / bookkeeping.
        self.hangar_system.on_deployed(slot, icpt)

        return icpt
