import sys
import pygame
from pygame.math import Vector2
from spacegame.ui.ui import Button, INTERCEPTOR_PREVIEW_IMG, draw_triangle
from spacegame.models.units.interceptor import Interceptor
from spacegame.models.units.frigate import Frigate
from spacegame.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS


# ---- Tier icon helpers (same style as in light_craft_selection) ----
ICON_BLUE = (70, 130, 220)
ICON_WHITE = (240, 240, 255)


def tier_to_roman(tier_value: int) -> str:
    if tier_value <= 0:
        return "0"
    numerals = ["", "I", "II", "III"]
    if tier_value < len(numerals):
        return numerals[tier_value]
    return numerals[-1] + f"+{tier_value - (len(numerals) - 1)}"


def draw_tier_icon(surface: pygame.Surface, host_rect: pygame.Rect, tier_value: int) -> None:
    """
    Blue flag in the top-right corner of host_rect.
    Inside it – large centered roman numeral.
    """
    large_tier_font = pygame.font.Font(None, 26)

    flag_w = 22
    flag_h = 22
    flag_rect = pygame.Rect(host_rect.right - flag_w - 1, host_rect.top + 1, flag_w, flag_h)

    pygame.draw.rect(surface, ICON_BLUE, flag_rect)

    text = tier_to_roman(int(tier_value))
    tier_text = large_tier_font.render(text, True, ICON_WHITE)
    tier_text_rect = tier_text.get_rect(center=flag_rect.center)
    surface.blit(tier_text, tier_text_rect)


def _compute_squad_stats(is_equipped: bool):
    if not is_equipped:
        return {
            "damage_to_hull": 0.0,
            "damage_to_armor": 0.0,
            "hull": 0,
            "speed": 0.0,
        }

    return {
        "damage_to_hull": 37.4,
        "damage_to_armor": 2.8,
        "hull": 3990,
        "speed": 11.7,
    }


def _gather_slot_info(main_player, player_fleet, slot_index: int):
    hangar = getattr(main_player, "hangar_system", None)
    if hangar is None or not (0 <= slot_index < hangar.num_slots):
        return {
            "is_equipped": False,
            "name": "NONE",
            "rarity": "NONE",
            "tier": 0,
            "ready_ships": 0,
            "max_ships": 0,
            "selected_ship_index": -1,
            "stats": _compute_squad_stats(False),
        }

    assigned_id = hangar.assignments[slot_index]
    is_equipped = assigned_id is not None

    entry = None  # noqa
    if is_equipped:
        for e in hangar.pool:
            if e.get("id") == assigned_id and e.get("alive", False):
                entry = e
                break
        if entry is None:
            is_equipped = False

    if not is_equipped:
        return {
            "is_equipped": False,
            "name": "NONE",
            "rarity": "NONE",
            "tier": 0,
            "ready_ships": 0,
            "max_ships": 0,
            "selected_ship_index": -1,
            "stats": _compute_squad_stats(False),
        }

    name = entry.get("name", "Interceptor Squadron")
    rarity = entry.get("rarity", "COMMON")
    tier = int(entry.get("tier", 0))

    ready_ships = 1 if hangar.slots[slot_index] else 0
    max_ships = 1
    selected_ship_index = 0 if ready_ships > 0 else -1

    stats = _compute_squad_stats(True)

    return {
        "is_equipped": True,
        "name": name,
        "rarity": rarity,
        "tier": tier,
        "ready_ships": ready_ships,
        "max_ships": max_ships,
        "selected_ship_index": selected_ship_index,
        "stats": stats,
    }


def squad_detail_screen(main_player, player_fleet, slot_index: int):
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    clock = pygame.time.Clock()
    width, height = screen.get_size()

    # ---------- COLORS ----------
    BG_COLOR = (4, 18, 35)
    NAV_LINE_COLOR = (35, 80, 120)
    TITLE_COLOR = (185, 210, 235)
    NAV_BG_COLOR = (10, 40, 70)

    CARD_BG = (12, 26, 50)
    STAT_LABEL = (160, 185, 210)
    STAT_VALUE = (230, 240, 255)

    BUTTON_BASE = (28, 80, 135)
    BUTTON_HOVER = (40, 110, 185)
    BUTTON_TEXT = TITLE_COLOR
    BUTTON_DISABLED_BG = (40, 50, 70)
    BUTTON_DISABLED_TEXT = (110, 120, 140)

    PLUS_CIRCLE = (80, 160, 230)
    READY_FILLED = (120, 220, 255)
    READY_EMPTY = (60, 90, 130)

    REMOVE_X_COLOR = TITLE_COLOR
    REMOVE_X_DISABLED = (90, 110, 140)

    # ---------- FONTS ----------
    title_font = pygame.font.Font(None, 40)
    label_font = pygame.font.Font(None, 28)
    name_font = pygame.font.Font(None, 32)
    small_header_font = pygame.font.Font(None, 22)  # "DETAILS" + rarity
    stat_font = pygame.font.Font(None, 24)
    officer_font = pygame.font.Font(None, 24)
    button_font = pygame.font.Font(None, 28)

    # ---------- TOP BAR / NAV ----------
    TOP_BAR_HEIGHT = 96
    TAB_HEIGHT = 38

    title_text = "FLEET CONFIGURATION"
    title_surf = title_font.render(title_text, True, TITLE_COLOR)
    title_rect = title_surf.get_rect(center=(width // 2, TOP_BAR_HEIGHT // 2 - 22))

    tabs_y = TOP_BAR_HEIGHT - TAB_HEIGHT - 4
    nav_top_y = tabs_y - 6
    nav_bottom_y = tabs_y + TAB_HEIGHT + 6

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

    # ---------- LAYOUT CONSTANTS (from fleet_management) ----------
    ROW_CENTER_Y = height // 2
    COLUMN_SPACING_X = width // 3

    center_x = width // 2
    left_center_x = center_x - COLUMN_SPACING_X
    mid_center_x = center_x
    right_center_x = center_x + COLUMN_SPACING_X

    ms_w, ms_h = 170, 160
    ms_rect = pygame.Rect(0, 0, ms_w, ms_h)
    SHIP_OFFSET_X = 40
    ms_rect.center = (left_center_x + SHIP_OFFSET_X, ROW_CENTER_Y)

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

    fr_w, fr_h = 140, 70
    fr_rect = pygame.Rect(0, 0, fr_w, fr_h)
    fr_rect.center = (right_center_x, ROW_CENTER_Y)

    previews_top = min(ms_rect.top, circle_rects[0].top, fr_rect.top)

    # ---------- LEFT CARD LAYOUT ----------
    card_margin_x = 40
    card_top = nav_bottom_y + 24
    card_width = int(width * 0.42)
    card_height = int(height * 0.64)
    card_rect = pygame.Rect(card_margin_x, card_top, card_width, card_height)

    # Officer square size (rect itself will be placed in draw section)
    officer_box_size = 70

    # CHANGE button under card (manual rect for sharp edges)
    change_btn_w = 220
    change_btn_h = 54
    change_btn_x = card_rect.left
    change_btn_y = card_rect.bottom + 26
    change_rect = pygame.Rect(change_btn_x, change_btn_y, change_btn_w, change_btn_h)

    # ---------- RIGHT PREVIEW LAYOUT ----------
    preview_center = Vector2(int(width * 0.69), int(height * 0.50))
    preview_size = 220

    plus_radius = 80
    plus_rect = pygame.Rect(0, 0, plus_radius * 2, plus_radius * 2)
    plus_rect.center = (int(preview_center.x), int(preview_center.y))

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # noqa: F841

        slot_info = _gather_slot_info(main_player, player_fleet, slot_index)
        is_equipped = slot_info["is_equipped"]
        stats = slot_info["stats"]

        # ---- detect if this squad is currently deployed (alive ship in this slot) ----
        hangar = getattr(main_player, "hangar_system", None)
        is_deployed = False
        if hangar is not None and 0 <= slot_index < getattr(hangar, "num_slots", 0):
            ship = hangar.ships[slot_index]
            if ship is not None and getattr(ship, "health", 0.0) > 0.0:
                is_deployed = True

        # remove button layout (aligned with squad name height, directly under orange X)
        remove_radius = 20
        remove_center_x = close_rect.centerx
        remove_center_y = card_rect.top + 42 + name_font.get_height() // 2
        remove_center = (remove_center_x, remove_center_y)
        remove_hit_rect = pygame.Rect(0, 0, remove_radius * 2 + 10, remove_radius * 2 + 10)
        remove_hit_rect.center = remove_center

        # --- prepare hangar / assignments / dot positions for clicks + drawing ---
        if hangar is not None:
            num_slots = hangar.num_slots
            assignments = hangar.assignments
        else:
            assignments = getattr(main_player, "hangar_assignments", [])
            num_slots = len(assignments)

        slot_dot_positions = []
        if num_slots > 0:
            dot_spacing = 22
            dot_x = remove_center[0]
            start_y = remove_center[1] + remove_radius + 26
            for i in range(num_slots):
                y = start_y + i * dot_spacing
                slot_dot_positions.append((i, dot_x, y))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if back_arrow_hit_rect.collidepoint(mx, my):
                    return

                if close_hit_rect.collidepoint(mx, my):
                    return "to_game"

                # only allow remove if equipped and not currently deployed
                if is_equipped and (not is_deployed) and remove_hit_rect.collidepoint(mx, my):
                    hangar = getattr(main_player, "hangar_system", None)
                    if hangar is not None:
                        hangar.clear_slot(slot_index)
                    return

                # plus: only when nothing is equipped
                if (not is_equipped) and plus_rect.collidepoint(mx, my):
                    from spacegame.screens.light_craft_selection import (
                        light_craft_selection_screen,
                    )

                    light_craft_selection_screen(main_player, slot_index)
                    continue

                # CHANGE: only when equipped and not deployed
                if is_equipped and (not is_deployed) and change_rect.collidepoint(mx, my):
                    from spacegame.screens.light_craft_selection import (
                        light_craft_selection_screen,
                    )

                    light_craft_selection_screen(main_player, slot_index)
                    continue

                # --- slot-circle click handling: change viewed slot ---
                slot_clicked = False
                hit_radius_sq = 10 * 10
                for idx, dx, dy in slot_dot_positions:
                    if (mx - dx) * (mx - dx) + (my - dy) * (my - dy) <= hit_radius_sq:
                        slot_index = idx  # switch view to this slot
                        slot_clicked = True
                        break
                if slot_clicked:
                    continue  # re-enter loop with new slot_index

        # ---------- DRAW ----------
        screen.fill(BG_COLOR)

        # top nav band
        pygame.draw.rect(
            screen,
            NAV_BG_COLOR,
            (0, nav_top_y, width, nav_bottom_y - nav_top_y),
        )
        pygame.draw.line(screen, NAV_LINE_COLOR, (0, nav_top_y), (width, nav_top_y), 1)
        pygame.draw.line(
            screen, NAV_LINE_COLOR, (0, nav_bottom_y), (width, nav_bottom_y), 1
        )

        # title + back / close
        screen.blit(title_surf, title_rect)

        arrow_color = (255, 255, 255)
        arrow_points = [
            (back_arrow_rect.left, back_arrow_rect.centery),
            (back_arrow_rect.right, back_arrow_rect.top),
            (back_arrow_rect.right, back_arrow_rect.bottom),
        ]
        pygame.draw.polygon(screen, arrow_color, arrow_points)
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

        # -------- LEFT CARD --------
        pygame.draw.rect(screen, CARD_BG, card_rect)  # no border

        # top row: DETAILS + rarity
        details_surf = small_header_font.render("DETAILS", True, TITLE_COLOR)
        details_rect = details_surf.get_rect()
        details_rect.topleft = (card_rect.left + 24, card_rect.top + 10)
        screen.blit(details_surf, details_rect)

        rarity_text = slot_info["rarity"].upper()
        rarity_surf = small_header_font.render(rarity_text, True, TITLE_COLOR)
        rarity_rect = rarity_surf.get_rect()
        rarity_rect.topright = (card_rect.right - 24, card_rect.top + 10)
        screen.blit(rarity_surf, rarity_rect)

        # big squad name
        name_surf = name_font.render(slot_info["name"].upper(), True, STAT_VALUE)
        name_rect = name_surf.get_rect()
        name_rect.topleft = (card_rect.left + 24, card_rect.top + 42)
        screen.blit(name_surf, name_rect)

        # stats with underline per row
        stats_top = card_rect.top + 96
        row_h = 32
        stat_rows = [
            ("Damage to Hull", f"{stats['damage_to_hull']:.1f}" if is_equipped else "0"),
            ("Damage to Armor", f"{stats['damage_to_armor']:.1f}" if is_equipped else "0"),
            ("Hull", f"{int(stats['hull'])}" if is_equipped else "0"),
            ("Speed", f"{stats['speed']:.1f}" if is_equipped else "0"),
        ]
        line_left = card_rect.left + 24
        line_right = card_rect.right - 24
        for i, (label_text, value_text) in enumerate(stat_rows):
            y = stats_top + i * row_h
            lbl = stat_font.render(label_text, True, STAT_LABEL)
            val = stat_font.render(value_text, True, STAT_VALUE)

            screen.blit(lbl, (card_rect.left + 24, y))
            val_rect = val.get_rect()
            val_rect.topright = (card_rect.right - 24, y)
            screen.blit(val, val_rect)

            line_y = y + stat_font.get_height() + 2
            pygame.draw.line(
                screen,
                NAV_LINE_COLOR,
                (line_left, line_y),
                (line_right, line_y),
                1,
            )

        # officer assign box: closer to stats
        officer_top = stats_top + row_h * len(stat_rows) + 26
        officer_box_rect = pygame.Rect(
            card_rect.left + 24,
            officer_top,
            officer_box_size,
            officer_box_size,
        )

        pygame.draw.rect(screen, CARD_BG, officer_box_rect)  # flat square
        pygame.draw.rect(screen, TITLE_COLOR, officer_box_rect, 2)

        ocx, ocy = officer_box_rect.center
        inner_radius = int(officer_box_size / 2.8)
        pygame.draw.circle(screen, TITLE_COLOR, (ocx, ocy), inner_radius, 2)

        plus_size = 14  # keep plus size fixed
        pygame.draw.line(
            screen, TITLE_COLOR, (ocx - plus_size, ocy), (ocx + plus_size, ocy), 2
        )
        pygame.draw.line(
            screen, TITLE_COLOR, (ocx, ocy - plus_size), (ocx, ocy + plus_size), 2
        )

        officer_lbl = officer_font.render("ASSIGN OFFICER", True, STAT_VALUE)
        officer_lbl_rect = officer_lbl.get_rect()
        officer_lbl_rect.midleft = (officer_box_rect.right + 18, ocy)
        screen.blit(officer_lbl, officer_lbl_rect)

        # CHANGE button (sharp edges), disabled if not equipped or deployed
        mx, my = pygame.mouse.get_pos()
        change_enabled = is_equipped and (not is_deployed)
        if change_enabled:
            hovered_change = change_rect.collidepoint(mx, my)
            change_color = BUTTON_HOVER if hovered_change else BUTTON_BASE
            change_text_color = BUTTON_TEXT
        else:
            change_color = BUTTON_DISABLED_BG
            change_text_color = BUTTON_DISABLED_TEXT

        pygame.draw.rect(screen, change_color, change_rect, 0)
        change_text = button_font.render("CHANGE", True, change_text_color)
        change_text_rect = change_text.get_rect(center=change_rect.center)
        screen.blit(change_text, change_text_rect)

        # -------- RIGHT PREVIEW / STATUS --------
        if is_equipped:
            # triangle frame (blue) a bit higher with preview_center
            draw_triangle(
                screen,
                (preview_center.x, preview_center.y),
                preview_size * 1.1,
                (80, 200, 255),
                2,
            )

            # ship preview
            ship_w = 160
            ship_h = 100
            ship_img = pygame.transform.smoothscale(
                INTERCEPTOR_PREVIEW_IMG, (ship_w, ship_h)
            )
            ship_rect = ship_img.get_rect()
            ship_rect.center = (int(preview_center.x), int(preview_center.y))
            screen.blit(ship_img, ship_rect.topleft)

            # tier icon – between remove text and ship, on rarity row height
            tier_host_rect = pygame.Rect(0, 0, 40, 40)
            tier_y = rarity_rect.centery + 8
            tier_x = (ship_rect.left + remove_center[0]) // 2
            tier_host_rect.center = (tier_x, tier_y)
            draw_tier_icon(screen, tier_host_rect, slot_info["tier"])
        else:
            # empty slot: big plus-circle
            pygame.draw.circle(screen, PLUS_CIRCLE, plus_rect.center, plus_radius, 3)
            plus_size_big = 26
            cx, cy = plus_rect.center
            pygame.draw.line(screen, PLUS_CIRCLE, (cx - plus_size_big, cy), (cx + plus_size_big, cy), 3)
            pygame.draw.line(screen, PLUS_CIRCLE, (cx, cy - plus_size_big), (cx, cy + plus_size_big), 3)

        # -------- REMOVE SQUAD + SLOT DOTS --------
        # button circle (same size, thicker X only). Disabled if not equipped or deployed.
        can_modify = is_equipped and (not is_deployed)
        circle_color = REMOVE_X_COLOR if can_modify else REMOVE_X_DISABLED
        pygame.draw.circle(screen, circle_color, remove_center, remove_radius, 3)

        # centered, larger thicker X
        x_size = 12
        x0, y0 = remove_center
        pygame.draw.line(
            screen,
            circle_color,
            (x0 - x_size, y0 - x_size),
            (x0 + x_size, y0 + x_size),
            4,
        )
        pygame.draw.line(
            screen,
            circle_color,
            (x0 + x_size, y0 - x_size),
            (x0 - x_size, y0 + x_size),
            4,
        )

        # "REMOVE" / "SQUAD" to the LEFT of button, 2 lines
        remove_color = (110, 135, 155)
        remove_font = pygame.font.Font(None, 24)
        text_remove = remove_font.render("REMOVE", True, remove_color)
        text_squad = remove_font.render("SQUAD", True, remove_color)

        text_right = remove_center[0] - remove_radius - 14
        text_remove_rect = text_remove.get_rect()
        text_squad_rect = text_squad.get_rect()
        text_remove_rect.topright = (text_right, remove_center[1] - text_remove.get_height())
        text_squad_rect.topright = (text_right, remove_center[1] + 2)
        screen.blit(text_remove, text_remove_rect)
        screen.blit(text_squad, text_squad_rect)

        # slot dots (one per hangar slot) in vertical column under the button
        if num_slots > 0:
            dot_spacing = 22
            dot_x = remove_center[0]
            start_y = remove_center[1] + remove_radius + 26
            for i in range(num_slots):
                y = start_y + i * dot_spacing

                # determine if slot actually has a ship assigned
                has_squad = False
                if i < len(assignments):
                    val = assignments[i]
                    # treat None or -1 (or similar sentinel) as "no ship"
                    has_squad = (val is not None and val != -1)

                # base size/color kept the same
                radius = 7
                color = READY_EMPTY
                width = 2  # hollow by default

                if has_squad:
                    # filled circle, same color & radius
                    width = 0

                if i == slot_index:
                    # currently selected squad
                    radius = 9
                    if has_squad:
                        # selected & has squad -> big filled bright
                        color = READY_FILLED
                        width = 0
                    else:
                        # selected & no squad -> big bright hollow
                        color = READY_FILLED
                        width = 2

                pygame.draw.circle(screen, color, (dot_x, y), radius, width)

        pygame.display.flip()
