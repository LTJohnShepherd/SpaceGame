import sys
import pygame
from spacegame.ui.fleet_management_ui import (
    draw_fleet_section_titles,
    compute_fleet_preview_layout,
)
from spacegame.models.units.expedition_ship import ExpeditionShip
from spacegame.models.units.frigate import Frigate
from spacegame.ui.ui import preview_for_unit, draw_health_bar
from spacegame.config import (
    FPS,
    UI_BG_COLOR, 
    UI_NAV_LINE_COLOR, 
    UI_TITLE_COLOR,
    UI_TOP_BAR_HEIGHT,
    UI_TAB_HEIGHT,
    UI_TAB_TEXT_SELECTED
    )


def _build_hangar_snapshot(main_player):
    """Build a hangar snapshot using the Hangar system on the main player.

    The Hangar instance is the single source of truth. We simply delegate to its
    snapshot() helper, which returns:
      - assignments: list of interceptor ids per slot
      - ships: list of Interceptor objects (or None) per slot
      - pool_by_id: dict[id] -> InterceptorEntry
    """
    hangar = getattr(main_player, "hangar_system", None)
    if hangar is None or not hasattr(hangar, "snapshot"):
        return [], [], {}
    return hangar.snapshot()


def _entry_is_alive(entry) -> bool:
    return bool(getattr(entry, "alive", False))


def _entry_name(entry) -> str:
    name = getattr(entry, "name", None)
    return name if name is not None else "Interceptor"


def fleet_management_screen(main_player: ExpeditionShip, player_fleet):
    """
    Fleet management screen (new Hangar system only):
    - 3 slots in a vertical column.
    - Empty slot: hollow circle with '+'.
    - Assigned slot: interceptor preview image drawn instead of the circle.
    - Clicking a slot opens a stored crafts screen.
    """
    screen = pygame.display.get_surface()
    if screen is None:
        return

    clock = pygame.time.Clock()
    width, height = screen.get_size()

    # ---------- COLORS / CONSTANTS TO MATCH INTERNAL SCREEN ----------
    # Fonts
    title_font = pygame.font.Font(None, 40)
    label_font = pygame.font.Font(None, 28)

    # ----------------- TITLE + NAV LAYOUT -----------------
    title_text = "FLEET CONFIGURATION"
    title_surf = title_font.render(title_text, True, UI_TITLE_COLOR)
    title_rect = title_surf.get_rect(center=(width // 2, UI_TOP_BAR_HEIGHT // 2 - 22))

    # Nav band (same vertical bounds as internal screen)
    tabs_y = UI_TOP_BAR_HEIGHT - UI_TAB_HEIGHT - 4
    nav_top_y = tabs_y - 6
    nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6

    # Back arrow and close "X" at same height as in internal screen
    nav_center_y = UI_TOP_BAR_HEIGHT // 1.3

    arrow_size = 32
    back_arrow_rect = pygame.Rect(0, 0, arrow_size, arrow_size)
    back_arrow_rect.center = (40, nav_center_y)
    back_arrow_hit_rect = back_arrow_rect.inflate(20, 20)

    close_font = pygame.font.Font(None, 40)
    close_surf = close_font.render("X", True, (255, 160, 0))
    close_rect = close_surf.get_rect()
    close_rect.center = (width - 40, UI_TOP_BAR_HEIGHT // 1.25)
    close_hit_rect = close_rect.inflate(20, 20)

    
    # ----------------- LAYOUT CONSTANTS (shared fleet preview geometry) -----------------
    fleet_layout = compute_fleet_preview_layout(width, height)
    left_center_x = fleet_layout["left_center_x"]
    mid_center_x = fleet_layout["mid_center_x"]
    ms_rect = fleet_layout["ms_rect"]
    circle_rects = fleet_layout["circle_rects"]
    fr_rect = fleet_layout["fr_rect"]
    previews_top = fleet_layout["previews_top"]
    circle_radius = fleet_layout.get("circle_radius", 30)
    circle_col_x = mid_center_x

    running = True
    while running:
        # ------------- EVENTS -------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_arrow_hit_rect.collidepoint(event.pos):
                    running = False
                    continue
                if close_hit_rect.collidepoint(event.pos):
                    return "to_game"

                for idx, c_rect in enumerate(circle_rects):
                    if c_rect.collidepoint(event.pos):
                        # Open detailed squad card for this hangar slot.
                        from spacegame.screens.squad_detail import squad_detail_screen

                        res = squad_detail_screen(main_player, player_fleet, idx)
                        if res == "to_game":
                            return "to_game"
                        break

        # Rebuild a fresh snapshot of hangar state each frame (new system only)
        assignments, ships, pool_by_id = _build_hangar_snapshot(main_player)

        # ------------- DRAW -------------
        screen.fill(UI_BG_COLOR)

        # Title
        screen.blit(title_surf, title_rect)

        # Back arrow
        arrow_color = UI_TAB_TEXT_SELECTED
        arrow_points = [
            (back_arrow_rect.left, back_arrow_rect.centery),
            (back_arrow_rect.right, back_arrow_rect.top),
            (back_arrow_rect.right, back_arrow_rect.bottom),
        ]
        pygame.draw.polygon(screen, arrow_color, arrow_points)

        # Close X
        screen.blit(close_surf, close_rect)

        # -------- Section titles + lines (CURRENT LOADOUT / SQUADS / ESCORTS) --------
        total_slots = len(assignments)
        equipped_slots = sum(1 for a in assignments if a is not None)
        frigates = [s for s in player_fleet if isinstance(s, Frigate)]
        alive_frigates = [f for f in frigates if getattr(f, "health", 0) > 0]
        draw_fleet_section_titles(
            screen,
            title_rect,
            label_font,
            UI_TITLE_COLOR,
            UI_NAV_LINE_COLOR,
            previews_top,
            left_center_x,
            circle_col_x,
            fr_rect.centerx,
            total_slots,
            equipped_slots,
            len(frigates),
            len(alive_frigates),
        )

        # LEFT: expedition ship preview and HP
        ms_surf = pygame.transform.smoothscale(
            preview_for_unit("expedition"), (ms_rect.width, ms_rect.height)
        )
        screen.blit(ms_surf, ms_rect.topleft)
        bar_pad = 6
        bar_h = 6
        bar_w = ms_rect.width
        bar_x = ms_rect.left
        bar_y = ms_rect.bottom + bar_pad
        draw_health_bar(
            screen, bar_x, bar_y, bar_w, bar_h, main_player.health, main_player.max_health
        )

        # MIDDLE: squad circles (assigned interceptors or empty)
        for i, c_rect in enumerate(circle_rects):
            cx, cy = c_rect.center

            assigned_id = assignments[i] if 0 <= i < len(assignments) else None
            assigned_entry = (
                pool_by_id.get(assigned_id) if assigned_id is not None else None
            )
            if assigned_entry is not None and not _entry_is_alive(assigned_entry):
                assigned_entry = None

            if assigned_entry is not None:
                r = circle_radius - 4
                size = int(r * 2)
                # choose preview image by unit_type
                preview_img = preview_for_unit(getattr(assigned_entry, "unit_type"))
                icpt_img = pygame.transform.smoothscale(preview_img, (size, size))
                img_rect = icpt_img.get_rect(center=(cx, cy))
                screen.blit(icpt_img, img_rect.topleft)

                name_surf = label_font.render(
                    _entry_name(assigned_entry), True, (220, 220, 255)
                )
                name_x = cx - name_surf.get_width() // 2
                name_y = c_rect.top - 24
                screen.blit(name_surf, (name_x, name_y))
            else:
                pygame.draw.circle(
                    screen, (230, 230, 230), (cx, cy), circle_radius, 2
                )
                pygame.draw.line(
                    screen, (230, 230, 230), (cx - 8, cy), (cx + 8, cy), 2
                )
                pygame.draw.line(
                    screen, (230, 230, 230), (cx, cy - 8), (cx, cy + 8), 2
                )

            fighter_ship = ships[i] if 0 <= i < len(ships) else None
            fighter_alive = (
                fighter_ship is not None
                and getattr(fighter_ship, "health", 0.0) > 0.0
                and fighter_ship in player_fleet
            )

            if fighter_alive:
                hb_w = circle_radius * 2
                hb_h = 5
                hb_x = cx - hb_w // 2
                hb_y = cy + circle_radius + 6
                draw_health_bar(
                    screen,
                    hb_x,
                    hb_y,
                    hb_w,
                    hb_h,
                    fighter_ship.health,
                    fighter_ship.max_health,
                )

        if frigates:
            f = frigates[0]
            fr_img = pygame.transform.smoothscale(
                preview_for_unit("frigate"), (fr_rect.width, fr_rect.height)
            )
            screen.blit(fr_img, fr_rect.topleft)

            bar_pad = 6
            bar_h = 6
            bar_w = fr_rect.width
            bar_x = fr_rect.left
            bar_y = fr_rect.bottom + bar_pad
            draw_health_bar(
                screen, bar_x, bar_y, bar_w, bar_h, f.health, f.max_health
            )
        else:
            pygame.draw.rect(screen, (80, 80, 80), fr_rect, border_radius=10)

        pygame.display.flip()
        clock.tick(FPS)