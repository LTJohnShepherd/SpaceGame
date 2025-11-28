import sys
import pygame
from spacegame.models.units.expedition_ship import ExpeditionShip
from spacegame.models.units.frigate import Frigate
from spacegame.ui.ui import (
    EXPEDITION_PREVIEW_IMG,
    FRIGATE_PREVIEW_IMG,
    INTERCEPTOR_PREVIEW_IMG,
    draw_health_bar,
)


def fleet_management_screen(main_player: ExpeditionShip, player_fleet):
    """
    Fleet management screen:
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
    BG_COLOR = (4, 18, 35)
    NAV_LINE_COLOR = (35, 80, 120)
    TITLE_COLOR = (185, 210, 235)
    TOP_BAR_HEIGHT = 96
    TAB_HEIGHT = 38  # same as internal screen tabs

    # Fonts (title size matches internal screen: 42)
    title_font = pygame.font.Font(None, 40)
    label_font = pygame.font.Font(None, 28)

    # ----------------- TITLE + NAV LAYOUT -----------------
    # Title "FLEET CONFIGURATION" positioned like the internal screen title
    title_text = "FLEET CONFIGURATION"
    title_surf = title_font.render(title_text, True, TITLE_COLOR)
    title_rect = title_surf.get_rect(center=(width // 2, TOP_BAR_HEIGHT // 2 - 22))

    # Nav band (same vertical bounds as internal screen)
    tabs_y = TOP_BAR_HEIGHT - TAB_HEIGHT - 4
    nav_top_y = tabs_y - 6
    nav_bottom_y = tabs_y + TAB_HEIGHT + 6

    # Back arrow and close "X" at same height as in internal screen
    nav_center_y = TOP_BAR_HEIGHT // 1.3

    arrow_size = 32
    back_arrow_rect = pygame.Rect(0, 0, arrow_size, arrow_size)
    back_arrow_rect.center = (40, nav_center_y)
    back_arrow_hit_rect = back_arrow_rect.inflate(20, 20)

    close_font = pygame.font.Font(None, 40)
    close_surf = close_font.render("X", True, (255, 160, 0))
    close_rect = close_surf.get_rect()
    close_rect.center = (width - 40, TOP_BAR_HEIGHT // 1.25)
    close_hit_rect = close_rect.inflate(20, 20)

    # ----------------- DATA SAFETY -----------------
    if not hasattr(main_player, "interceptor_pool"):
        main_player.interceptor_pool = [
            {"id": i, "name": f"Interceptor {i+1}", "alive": True}
            for i in range(5)
        ]
    if not hasattr(main_player, "hangar_assignments"):
        main_player.hangar_assignments = [None, None, None]

    if not hasattr(main_player, "hangar"):
        main_player.hangar = [False, False, False]

    if not hasattr(main_player, "hangar_ships"):
        main_player.hangar_ships = [None, None, None]

    # ----------------- LAYOUT CONSTANTS -----------------
    ROW_CENTER_Y = height // 2
    COLUMN_SPACING_X = width // 3

    center_x = width // 2
    left_center_x = center_x - COLUMN_SPACING_X
    mid_center_x = center_x
    right_center_x = center_x + COLUMN_SPACING_X

    # Expedition ship (left)
    ms_w, ms_h = 170, 160
    ms_rect = pygame.Rect(0, 0, ms_w, ms_h)
    SHIP_OFFSET_X = 40  # ship offset to the right
    ms_rect.center = (left_center_x + SHIP_OFFSET_X, ROW_CENTER_Y)

    # Light crafts column (middle)
    circle_radius = 30
    circle_spacing = 120
    circle_col_x = mid_center_x
    circle_top_y = ROW_CENTER_Y - circle_spacing
    circle_rects = []
    for i in range(3):
        cx = circle_col_x
        cy = circle_top_y + i * circle_spacing
        rect = pygame.Rect(0, 0, circle_radius * 2, circle_radius * 2)
        rect.center = (cx, cy)
        circle_rects.append(rect)

    # Escort frigate preview (right)
    fr_w, fr_h = 140, 70
    fr_rect = pygame.Rect(0, 0, fr_w, fr_h)
    fr_rect.center = (right_center_x, ROW_CENTER_Y)

    # For aligning section titles between title band and previews
    previews_top = min(ms_rect.top, circle_rects[0].top, fr_rect.top)

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
                        from spacegame.screens.squad_detail import (
                            squad_detail_screen,
                        )

                        res = squad_detail_screen(main_player, player_fleet, idx)
                        if res == "to_game":
                            return "to_game"
                        break

        # ------------- DRAW -------------
        screen.fill(BG_COLOR)

        # Title
        screen.blit(title_surf, title_rect)

        # Back arrow
        arrow_color = (255, 255, 255)
        arrow_points = [
            (back_arrow_rect.left, back_arrow_rect.centery),
            (back_arrow_rect.right, back_arrow_rect.top),
            (back_arrow_rect.right, back_arrow_rect.bottom),
        ]
        pygame.draw.polygon(screen, arrow_color, arrow_points)

        # Close X
        screen.blit(close_surf, close_rect)

        # -------- Section titles + lines (CURRENT LOADOUT / SQUADS / ESCORTS) --------
        fleet_title_bottom = title_rect.bottom
        label_height = label_font.size("M")[1]
        labels_y = fleet_title_bottom + (
            previews_top - fleet_title_bottom - label_height
        ) // 7.1

        line_margin = int(label_height * 15 / 19.5)

        # LEFT: CURRENT LOADOUT
        current_surf = label_font.render("CURRENT LOADOUT", True, NAV_LINE_COLOR)
        current_rect = current_surf.get_rect()
        current_rect.centerx = left_center_x
        current_rect.y = labels_y

        pygame.draw.line(
            screen,
            NAV_LINE_COLOR,
            (current_rect.left, current_rect.top - line_margin),
            (current_rect.right * 1.4, current_rect.top - line_margin),
            1,
        )
        pygame.draw.line(
            screen,
            NAV_LINE_COLOR,
            (current_rect.left, current_rect.bottom + line_margin),
            (current_rect.right * 1.4, current_rect.bottom + line_margin),
            1,
        )
        screen.blit(current_surf, current_rect)

        ms_surf = pygame.transform.smoothscale(
            EXPEDITION_PREVIEW_IMG, (ms_rect.width, ms_rect.height)
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

        # MIDDLE: SQUADS
        total_slots = len(main_player.hangar_assignments)
        equipped_slots = sum(1 for a in main_player.hangar_assignments if a is not None)
        squads_text = (
            f"SQUADS: {equipped_slots} / {total_slots}"
            if total_slots > 0
            else "SQUADS: 0 / 0"
        )

        squads_surf = label_font.render(squads_text, True, TITLE_COLOR)
        squads_rect = squads_surf.get_rect()
        squads_rect.centerx = circle_col_x / 1.2
        squads_rect.y = labels_y

        pygame.draw.line(
            screen,
            NAV_LINE_COLOR,
            (squads_rect.left, squads_rect.top - line_margin),
            (squads_rect.right * 1.45, squads_rect.top - line_margin),
            1,
        )
        pygame.draw.line(
            screen,
            NAV_LINE_COLOR,
            (squads_rect.left, squads_rect.bottom + line_margin),
            (squads_rect.right * 1.45, squads_rect.bottom + line_margin),
            1,
        )
        screen.blit(squads_surf, squads_rect)

        for i, c_rect in enumerate(circle_rects):
            cx, cy = c_rect.center

            assigned_id = None
            if 0 <= i < len(main_player.hangar_assignments):
                assigned_id = main_player.hangar_assignments[i]

            assigned_entry = None
            if assigned_id is not None:
                for entry in main_player.interceptor_pool:
                    if entry["id"] == assigned_id and entry.get("alive", False):
                        assigned_entry = entry
                        break

            if assigned_entry is not None:
                r = circle_radius - 4
                size = int(r * 2)
                icpt_img = pygame.transform.smoothscale(
                    INTERCEPTOR_PREVIEW_IMG, (size, size)
                )
                img_rect = icpt_img.get_rect(center=(cx, cy))
                screen.blit(icpt_img, img_rect.topleft)

                name_surf = label_font.render(
                    assigned_entry.get("name", "Interceptor"), True, (220, 220, 255)
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

            fighter_ship = (
                main_player.hangar_ships[i]
                if i < len(main_player.hangar_ships)
                else None
            )
            fighter_alive = (
                fighter_ship is not None
                and fighter_ship.health > 0.0
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

        # RIGHT: ESCORTS
        frigates = [s for s in player_fleet if isinstance(s, Frigate)]
        alive_frigates = [f for f in frigates if getattr(f, "health", 0) > 0]

        if frigates:
            escorts_text = f"ESCORTS: {len(alive_frigates)} / {len(frigates)}"
        else:
            escorts_text = "ESCORTS: 0 / 0"

        escorts_surf = label_font.render(escorts_text, True, TITLE_COLOR)
        escorts_rect = escorts_surf.get_rect()
        escorts_rect.centerx = fr_rect.centerx / 1.1
        escorts_rect.y = labels_y

        pygame.draw.line(
            screen,
            NAV_LINE_COLOR,
            (escorts_rect.left, escorts_rect.top - line_margin),
            (escorts_rect.right * 1.14, escorts_rect.top - line_margin),
            1,
        )
        pygame.draw.line(
            screen,
            NAV_LINE_COLOR,
            (escorts_rect.left, escorts_rect.bottom + line_margin),
            (escorts_rect.right * 1.14, escorts_rect.bottom + line_margin),
            1,
        )
        screen.blit(escorts_surf, escorts_rect)

        if frigates:
            f = frigates[0]
            fr_img = pygame.transform.smoothscale(
                FRIGATE_PREVIEW_IMG, (fr_rect.width, fr_rect.height)
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
        clock.tick(60)