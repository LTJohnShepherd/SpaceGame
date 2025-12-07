import sys
import pygame
from spacegame.config import (
    SCREEN_WIDTH, 
    SCREEN_HEIGHT, 
    UI_BG_COLOR, 
    UI_TAB_HEIGHT, 
    UI_SECTION_TEXT_COLOR,
    UI_TITLE_COLOR,
    UI_TAB_UNDERLINE_COLOR,
    UI_TAB_TEXT_SELECTED,
    UI_TAB_TEXT_COLOR,
    UI_NAV_BG_COLOR,
    UI_NAV_LINE_COLOR,
    UI_ICON_BLUE,
    PREVIEWS_DIR
    )
from spacegame.models.modules.fabricatormodule import (
    FabricatorModule,
    get_fabricator_modules_for_ship,
)
from spacegame.models.resources.orem import RUOreM
from spacegame.ui.fleet_management_ui import draw_tier_icon
                      

def fabrication_bpdetails_screen(main_player, player_fleet, selected_fabricator_index, bp):
    # Use the existing display surface if present; otherwise create one.
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    width, height = screen.get_size()

    # ---------- FONTS ----------
    title_font = pygame.font.Font(None, 40)
    tab_font = pygame.font.Font(None, 28)
    section_font = pygame.font.Font(None, 28)
    close_font = pygame.font.Font(None, 40)
    name_font = pygame.font.Font(None, 26)   # blueprint & REQUIREMENTS
    desc_font = pygame.font.Font(None, 20)   # data
    stat_font = pygame.font.Font(None, 20)   # ore
    btn_font = pygame.font.Font(None, 28)    # BUILD
    meta_font = pygame.font.Font(None, 20)   # DETAILS / PRODUCTION DETAILS / rarity

    # ---------- TOP BAR ----------
    TOP_BAR_HEIGHT = 96

    # Title in the center of the top bar (moved slightly up to give more room to tabs)
    title_text = "FABRICATION"
    title_surf = title_font.render(title_text, True, UI_SECTION_TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(width // 2, TOP_BAR_HEIGHT // 2 - 22))

    # Back arrow (left)
    arrow_size = 32
    back_arrow_rect = pygame.Rect(0, 0, arrow_size, arrow_size)
    back_arrow_rect.center = (40, TOP_BAR_HEIGHT // 1.3)

    # Close "X" (right)
    close_surf = close_font.render("X", True, (255, 160, 40))
    close_rect = close_surf.get_rect()
    close_rect.center = (width - 40, TOP_BAR_HEIGHT // 1.25)
    close_hit_rect = close_rect.inflate(16, 16)

    # ---------- TABS ----------
    tab_labels = ["STORAGE", "BRIDGE", "FABRICATION", "REFINING", "INTERNAL MODULES"]
    selected_tab = 2  # FABRICATION selected
    tab_spacing = 16

    tab_entries = []
    total_tabs_width = -tab_spacing
    # Measure and compute widths (icon + text + padding)
    icon_size = 24
    ICON_MARGIN = 10
    H_PADDING = 24

    for label in tab_labels:
        text_surf = tab_font.render(label, True, UI_TAB_TEXT_COLOR)
        text_width = text_surf.get_width()
        tab_width = icon_size + ICON_MARGIN + text_width + H_PADDING * 2
        tab_entries.append({"label": label, "text_surf": text_surf, "width": tab_width})
        total_tabs_width += tab_width + tab_spacing

    # Move tabs slightly lower so they are not too close to the title text
    tabs_y = TOP_BAR_HEIGHT - UI_TAB_HEIGHT - 4
    tabs_left = width // 2 - total_tabs_width // 2

    # Create rects for tabs
    x = tabs_left
    for entry in tab_entries:
        rect = pygame.Rect(x, tabs_y, entry["width"], UI_TAB_HEIGHT)
        entry["rect"] = rect
        x += entry["width"] + tab_spacing
    # ---------- FABRICATOR MODULE SLOTS (01 / 02 / ...) ----------
    fabricator_modules = get_fabricator_modules_for_ship()
    if not fabricator_modules:
        fabricator_modules = [FabricatorModule()]

    selected_fabricator_index = 0  # which fabricator slot is currently selected

    # Geometry for the left card and index column (01 / 02 / ...)
    nav_top_y = tabs_y - 6
    nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6
    content_top = nav_bottom_y + 24

    LEFT_SHIFT = 20
    card_x = 40 - LEFT_SHIFT
    card_y = content_top
    card_w = int(width * 0.38)
    card_h = int(height * 0.64)
    card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

    idx_size = 96
    idx_rect_base = pygame.Rect(card_rect.left + 16, card_rect.top + 16, idx_size, idx_size)
    IDX_V_SPACING = idx_size + 24

    # one rect per equipped fabricator: 01 stays as-is, 02/03/... stacked below it
    idx_rects: list[pygame.Rect] = [
        pygame.Rect(idx_rect_base.left, idx_rect_base.top + i * IDX_V_SPACING, idx_size, idx_size)
        for i in range(len(fabricator_modules))
    ]
    if not idx_rects:
        idx_rects.append(idx_rect_base)

    # ----- BIG CENTER RECT -----
    plus_radius = 120
    preview_center = (width // 2, height // 2)
    big_rect_pad = 100
    big_rect = pygame.Rect(
        preview_center[0] - plus_radius - big_rect_pad,
        preview_center[1] - plus_radius - big_rect_pad,
        (plus_radius + big_rect_pad) * 2,
        (plus_radius + big_rect_pad) * 2
    )

    # ---------- REQUIREMENTS PANEL (RIGHT) ----------
    right_panel_w = 340
    right_rect = pygame.Rect(
        width - right_panel_w - 40,
        card_rect.top,
        right_panel_w,
        140,
    )

    # ---------- BUILD BUTTON (BIG GREEN) ----------
    build_btn_h = 64
    build_btn_rect = pygame.Rect(
        right_rect.left,
        height - build_btn_h - 40,
        right_panel_w,
        build_btn_h,
    )

    # "SPEED UP" button (used only while fabricating)
    speed_btn_h = 64
    speed_btn_rect = pygame.Rect(
        right_rect.left,
        right_rect.bottom + 40,
        right_panel_w,
        speed_btn_h,
    )

    ore_preview_img = None
    try:
        ore_preview_img = pygame.image.load(
            PREVIEWS_DIR + "/" + RUOreM().preview_filename
        ).convert_alpha()
    except Exception:
        pass

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if back_arrow_rect.collidepoint(mx, my):
                    return

                if close_hit_rect.collidepoint(mx, my):
                    return "to_game"

                # Tabs
                for idx, entry in enumerate(tab_entries):
                    if entry["rect"].collidepoint(mx, my):
                        label = entry["label"]
                        # Open Storage (Inventory) when STORAGE tab clicked
                        if label == "STORAGE":
                            from spacegame.screens.inventory import inventory_screen
                            res = inventory_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            # return focus back to FABRICATION tab after closing inventory
                            selected_tab = 2
                        elif label == "INTERNAL MODULES":
                            from spacegame.screens.internal_modules_screen import internal_modules_screen
                            res = internal_modules_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            # after closing, go back to FABRICATION tab highlight
                            selected_tab = 2
                        else:
                            selected_tab = idx
                        break
                
                # Fabricator slot buttons (01 / 02 / ...)
                for i, rect in enumerate(idx_rects):
                    if rect.collidepoint(mx, my):
                        selected_fabricator_index = i
                        break

                                # ----- BUILD / SPEED UP / CANCEL -----
                fab_module = fabricator_modules[selected_fabricator_index]

                ore_letter = getattr(bp, "required_ore_letter")
                ore_amount = int(getattr(bp, "required_ore_amount"))
                player_inventory = getattr(main_player, "inventory", {})
                available_ore = int(player_inventory.get(ore_letter, 0))
                insufficient_resources = available_ore < ore_amount

                total_ms = int(getattr(fab_module, "fabrication_total_ms", 0))
                start_ticks = int(getattr(fab_module, "fabrication_start_ticks", 0))
                is_fabricating = (total_ms > 0 and start_ticks > 0)

                # CANCEL (bottom red button while fabricating)
                if is_fabricating and build_btn_rect.collidepoint(mx, my):
                    fab_module.fabrication_total_ms = 0
                    fab_module.fabrication_start_ticks = 0
                    fab_module.fabrication_progress = 0.0
                    fab_module.fabrication_blueprint = None
                    continue

                # SPEED UP (grey button)
                if is_fabricating and speed_btn_rect.collidepoint(mx, my):
                    # finish instantly for now
                    fab_module.fabrication_start_ticks = pygame.time.get_ticks() - total_ms
                    continue

                # BUILD (start fabrication)
                if (not is_fabricating) and (not insufficient_resources) and build_btn_rect.collidepoint(mx, my):
                    base_time_s = int(getattr(bp, "base_fabrication_time", 0))
                    total_ms = max(1, base_time_s * 1000)
                    fab_module.fabrication_total_ms = total_ms
                    fab_module.fabrication_start_ticks = pygame.time.get_ticks()
                    fab_module.fabrication_blueprint = bp
                    fab_module.fabrication_progress = 0.0

                    # optional: consume ore
                    player_inventory[ore_letter] = max(0, available_ore - ore_amount)
                    continue


        # ---------- DRAW ----------
        screen.fill(UI_BG_COLOR)

        # Nav band coordinates
        nav_top_y = tabs_y - 6
        nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6

        # Brighter strip behind all nav text/buttons
        pygame.draw.rect(
            screen,
            UI_NAV_BG_COLOR,
            (0, nav_top_y, width, nav_bottom_y - nav_top_y),
        )

        # Lines above and below the nav/tab area
        pygame.draw.line(screen, UI_NAV_LINE_COLOR, (0, nav_top_y), (width, nav_top_y), 1)
        pygame.draw.line(
            screen, UI_NAV_LINE_COLOR, (0, nav_bottom_y), (width, nav_bottom_y), 1
        )

        # Title (on top of nav background)
        screen.blit(title_surf, title_rect)

        # Back arrow (on top of nav background)
        arrow_color = (220, 235, 255)
        arrow_points = [
            (back_arrow_rect.left, back_arrow_rect.centery),
            (back_arrow_rect.right, back_arrow_rect.top),
            (back_arrow_rect.right, back_arrow_rect.bottom),
        ]
        pygame.draw.polygon(screen, arrow_color, arrow_points)

        # Close X (on top of nav background)
        screen.blit(close_surf, close_rect)

        # Tabs (transparent background: only icon, text, highlight on nav lines)
        for idx, entry in enumerate(tab_entries):
            rect = entry["rect"]
            is_selected = idx == selected_tab

            icon_rect = pygame.Rect(0, 0, icon_size, icon_size)
            icon_rect.centery = rect.centery
            icon_rect.left = rect.left + H_PADDING
            pygame.draw.rect(
                screen,
                (210, 220, 235) if is_selected else (170, 190, 210),
                icon_rect,
                border_radius=4,
                width=2,
            )

            text_color = UI_TAB_TEXT_SELECTED if is_selected else UI_TAB_TEXT_COLOR
            label_surf = tab_font.render(entry["label"], True, text_color)
            label_rect = label_surf.get_rect()
            label_rect.centery = rect.centery
            label_rect.left = icon_rect.right + ICON_MARGIN
            screen.blit(label_surf, label_rect)

            if is_selected:
                # highlight segments exactly on the top/bottom nav lines
                pygame.draw.line(
                    screen,
                    UI_TAB_UNDERLINE_COLOR,
                    (rect.left + 6, nav_top_y),
                    (rect.right - 6, nav_top_y),
                    2,
                )
                pygame.draw.line(
                    screen,
                    UI_TAB_UNDERLINE_COLOR,
                    (rect.left + 6, nav_bottom_y),
                    (rect.right - 6, nav_bottom_y),
                    2,
                )

        # ---------- MAIN CONTENT (fabrication visual) ----------
        content_top = nav_bottom_y + 24  # same as used in card_rect

        # Left detail: index squares (01, 02, ...) with corner-only decoration + progress bar,
        # and transparent details to the right (no border/background).
        def draw_index_square(rect: pygame.Rect, label: str, selected: bool) -> None:
            # selected -> orange corners (like internal modules), others -> white
            corner_color = UI_TAB_UNDERLINE_COLOR if selected else UI_TAB_TEXT_SELECTED
            corner_len = 18
            corner_thick = 3

            # corner-only frame (same pattern as original 01)
            # top-left
            pygame.draw.line(screen, corner_color, (rect.left, rect.top), (rect.left + corner_len, rect.top), corner_thick)
            pygame.draw.line(screen, corner_color, (rect.left, rect.top), (rect.left, rect.top + corner_len), corner_thick)
            # top-right
            pygame.draw.line(screen, corner_color, (rect.right - corner_len, rect.top), (rect.right, rect.top), corner_thick)
            pygame.draw.line(screen, corner_color, (rect.right, rect.top), (rect.right, rect.top + corner_len), corner_thick)
            # bottom-left
            pygame.draw.line(screen, corner_color, (rect.left, rect.bottom - corner_len), (rect.left, rect.bottom), corner_thick)
            pygame.draw.line(screen, corner_color, (rect.left, rect.bottom), (rect.left + corner_len, rect.bottom), corner_thick)
             # bottom-right
            pygame.draw.line(screen, corner_color, (rect.right - corner_len, rect.bottom), (rect.right, rect.bottom), corner_thick)
            pygame.draw.line(screen, corner_color, (rect.right, rect.bottom - corner_len), (rect.right, rect.bottom), corner_thick)

            # index text (01 / 02 / ...)
            index_font = pygame.font.Font(None, 36)
            idx_text = index_font.render(label, True, corner_color)
            it_rect = idx_text.get_rect(center=rect.center)
            screen.blit(idx_text, it_rect)

        # draw all fabricator slots (01 / 02 / ...)
        for i, rect in enumerate(idx_rects, start=1):
            draw_index_square(rect, f"{i:02d}", selected=(i - 1) == selected_fabricator_index)

        # ----- shared fabrication timer/progress (per fabricator module) -----
        fab_module = fabricator_modules[selected_fabricator_index]
        base_time_s = int(getattr(bp, "base_fabrication_time", 0))
        total_ms = int(getattr(fab_module, "fabrication_total_ms", 0))
        start_ticks = int(getattr(fab_module, "fabrication_start_ticks", 0))
        now_ticks = pygame.time.get_ticks()

        if total_ms > 0 and start_ticks > 0:
            elapsed = max(0, now_ticks - start_ticks)
            fabrication_progress = min(1.0, elapsed / float(total_ms))
            remaining_ms = max(0, total_ms - elapsed)
            remaining_s = remaining_ms // 1000
        else:
            fabrication_progress = 0.0
            remaining_s = base_time_s

        fab_module.fabrication_progress = fabrication_progress
        fab_module.fabrication_remaining_s = remaining_s

        pb_margin = 12
        PROGRESS_COLOR = (255, 160, 40)  # same orange as nav X


        for rect in idx_rects:
            pb_rect = pygame.Rect(
                rect.left + pb_margin,
                rect.bottom - 22,
                rect.width - pb_margin * 2,
                12,
            )
            pygame.draw.rect(screen, (40, 50, 70), pb_rect)

            if fabrication_progress > 0.0:
                inner_w = max(2, int(pb_rect.width * fabrication_progress))
                inner_rect = pygame.Rect(pb_rect.left, pb_rect.top, inner_w, pb_rect.height)
                pygame.draw.rect(screen, PROGRESS_COLOR, inner_rect)



        # Details to the right of the FIRST 01 square (fixed position)
        if idx_rects:
            base_idx_rect = idx_rects[0]
        else:
            base_idx_rect = idx_rect_base

        details_x = base_idx_rect.right + 18
        details_y = base_idx_rect.top

        # small row: "DETAILS" on the left, rarity on the right
        details_label = meta_font.render("DETAILS", True, (160, 180, 210))
        screen.blit(details_label, (details_x, details_y))

        rarity_text = "COMMON"
        if bp is not None and hasattr(bp, "rarity"):
            rarity_text = str(bp.rarity).upper()
        rarity_surf = meta_font.render(rarity_text, True, (160, 180, 210))
        rarity_rect = rarity_surf.get_rect()
        rarity_rect = rarity_surf.get_rect()
        rarity_rect.topright = (card_rect.right - 110, details_y)
        screen.blit(rarity_surf, rarity_rect.topleft)

        # now place the blueprint name a bit lower, under the DETAILS row
        title_font = pygame.font.Font(None, 26)

        # title from blueprint (can be multi-line with '\n')
        if bp is not None and getattr(bp, "title", None):
            title_text = str(bp.title)
        elif bp is not None and hasattr(bp, "name"):
            title_text = str(bp.name)

        title_lines = title_text.split("\n")
        module_title_rect = None
        ty = details_y + details_label.get_height() + 6
        for i, line in enumerate(title_lines[:2]):
            module_title = title_font.render(line, True, UI_SECTION_TEXT_COLOR)
            r = module_title.get_rect()
            r.topleft = (details_x, ty + i * (title_font.get_height() + 2))
            screen.blit(module_title, r.topleft)
            module_title_rect = r

        if module_title_rect is None:
            module_title_rect = pygame.Rect(details_x, details_y, 0, title_font.get_height())

        # description lines (from blueprint)
        desc_font = pygame.font.Font(None, 20)
        desc_text = str(bp.description)


        # allow '\n' in description; otherwise simple wrapping like before
        desc_lines = []
        for paragraph in desc_text.split("\n"):
            words = paragraph.split()
            line = ""
            max_width = card_rect.right - details_x - 100
            for w in words:
                test = (line + " " + w).strip()
                if desc_font.size(test)[0] > max_width and line:
                    desc_lines.append(line)
                    line = w
                else:
                    line = test
            if line:
                desc_lines.append(line)

        dy = module_title_rect.bottom + 8
        for line in desc_lines:
            s = desc_font.render(line, True, (180, 200, 220))
            screen.blit(s, (details_x, dy))
            dy += s.get_height() + 2

        # Module stats placed under description — render with connecting underline
        stat_label_font = pygame.font.Font(None, 20)
        stat_value_font = pygame.font.Font(None, 20)
        stat_x = details_x
        stat_y = dy + 12

        # Statistics derived from the unit this blueprint produces (Tier = bp.tier)
        # Default values (in case something goes wrong)
        damage_to_hull = 0
        damage_to_armor = 0
        hull = 0
        speed = 0

        if bp is not None:
            try:
                unit_cls = getattr(bp, "unit_class", None)
                tier = getattr(bp, "tier", 0)
                if unit_cls is not None:
                    # Build a temporary ship instance to read its stats
                    unit = unit_cls((0, 0), tier=tier)
                    damage_to_hull = getattr(unit, "bullet_damage", 0)
                    damage_to_armor = getattr(unit, "armor_damage", 0)
                    hull = getattr(unit, "max_health", getattr(unit, "health", 0))
                    mover = getattr(unit, "mover", None)
                    speed = getattr(mover, "speed", getattr(unit, "speed", 0))
            except Exception:
                pass

        stat_rows = [
            ("Damage to Hull:",  str(int(damage_to_hull))),
            ("Damage to Armor:", str(int(damage_to_armor))),
            ("Hull:",            str(int(hull))),
            ("Speed:",           str(int(speed))),
        ]

        for label_text, value_text in stat_rows:
            lbl = stat_label_font.render(label_text, True, UI_SECTION_TEXT_COLOR)
            val = stat_value_font.render(value_text, True, (200, 230, 200))

            # draw label and value
            screen.blit(lbl, (stat_x, stat_y))
            val_rect = val.get_rect()
            # right-align the value to the card's right padding (match squad_detail)
            val_rect.topright = (card_rect.right - 110, stat_y)
            screen.blit(val, val_rect.topleft)

            # draw a thin line from under the label area to under the value (like squad_detail)
            line_y = stat_y + lbl.get_height() + 4
            line_left = stat_x
            line_right = val_rect.right
            pygame.draw.line(screen, UI_NAV_LINE_COLOR, (line_left, line_y), (line_right, line_y), 1)

            stat_y += lbl.get_height() + 12

        # Officer assign box (use style from squad_detail) placed below stats
        officer_box_h = 70
        officer_box_w = 240
        CARD_BG = (12, 26, 50)
        officer_box_rect = pygame.Rect(details_x, stat_y + 36, officer_box_w, officer_box_h)
        pygame.draw.rect(screen, CARD_BG, officer_box_rect)
        pygame.draw.rect(screen, UI_TITLE_COLOR, officer_box_rect, 2)

        # plus-circle inside officer box (left side)
        ocx = officer_box_rect.left + 42
        ocy = officer_box_rect.centery
        inner_radius = int(officer_box_h / 2.8)
        pygame.draw.circle(screen, UI_TITLE_COLOR, (ocx, ocy), inner_radius, 2)

        plus_size = 14
        pygame.draw.line(screen, UI_TITLE_COLOR, (ocx - plus_size, ocy), (ocx + plus_size, ocy), 2)
        pygame.draw.line(screen, UI_TITLE_COLOR, (ocx, ocy - plus_size), (ocx, ocy + plus_size), 2)

        # Two-line label inside the same square (centered vertically, left-aligned next to plus)
        line1 = stat_label_font.render("ASSIGN", True, UI_SECTION_TEXT_COLOR)
        line2 = stat_label_font.render("OFFICER", True, UI_SECTION_TEXT_COLOR)
        text_x = ocx + inner_radius + 12
        total_text_h = line1.get_height() + line2.get_height() + 4
        start_y = officer_box_rect.centery - total_text_h // 2
        screen.blit(line1, (text_x, start_y))
        screen.blit(line2, (text_x, start_y + line1.get_height() + 4))

        # Corner-only rect around big circle (like the 01 square corners)
        big_corner_len = 28
        big_corner_thick = 4
        corner_color = UI_TAB_TEXT_SELECTED

        # MOVE THE BOTTOM CORNERS HIGHER
        bottom_offset = 80  # ← how much upward to move them (adjust freely)
        adjusted_bottom = big_rect.bottom - bottom_offset

        # top-left
        pygame.draw.line(screen, corner_color, (big_rect.left, big_rect.top), (big_rect.left + big_corner_len, big_rect.top), big_corner_thick)
        pygame.draw.line(screen, corner_color, (big_rect.left, big_rect.top), (big_rect.left, big_rect.top + big_corner_len), big_corner_thick)
        # top-right
        pygame.draw.line(screen, corner_color, (big_rect.right - big_corner_len, big_rect.top), (big_rect.right, big_rect.top), big_corner_thick)
        pygame.draw.line(screen, corner_color, (big_rect.right, big_rect.top), (big_rect.right, big_rect.top + big_corner_len), big_corner_thick)
        # bottom-left (moved upward)
        pygame.draw.line(screen, corner_color, (big_rect.left, adjusted_bottom - big_corner_len), (big_rect.left, adjusted_bottom), big_corner_thick)
        pygame.draw.line(screen, corner_color, (big_rect.left, adjusted_bottom), (big_rect.left + big_corner_len, adjusted_bottom), big_corner_thick)

        # bottom-right (moved upward)
        pygame.draw.line(screen, corner_color, (big_rect.right - big_corner_len, adjusted_bottom), (big_rect.right, adjusted_bottom), big_corner_thick)
        pygame.draw.line(screen, corner_color, (big_rect.right, adjusted_bottom - big_corner_len), (big_rect.right, adjusted_bottom), big_corner_thick)

        # --- blueprint preview in the center of the big rect ---
        if bp is not None and hasattr(bp, "preview_filename"):
            try:
                img = pygame.image.load(PREVIEWS_DIR + "/" + bp.preview_filename).convert_alpha()

                inner_margin = 40
                avail_height = adjusted_bottom - big_rect.top
                max_w = big_rect.width  - inner_margin * 2
                max_h = avail_height    - inner_margin * 2

                if max_w > 0 and max_h > 0:
                    scale = min(
                        max_w / img.get_width(),
                        max_h / img.get_height(),
                        1.0,
                    )
                    new_size = (
                        int(img.get_width() * scale),
                        int(img.get_height() * scale),
                    )
                    img = pygame.transform.smoothscale(img, new_size)

                    center_x = big_rect.centerx
                    center_y = (big_rect.top + adjusted_bottom) // 2
                    img_rect = img.get_rect(center=(center_x, center_y))
                    screen.blit(img, img_rect.topleft)
            except Exception:
                pass

                # ---------- PRODUCTION DETAILS (RIGHT) ----------
        ore_letter = getattr(bp, "required_ore_letter")
        ore_amount = int(getattr(bp, "required_ore_amount"))
        ore_tier = int(getattr(bp, "required_ore_tier"))
        player_inventory = getattr(main_player, "inventory")
        available_ore = int(player_inventory.get(ore_letter, 0))
        insufficient_resources = available_ore < ore_amount

        # header
        prod_surf = meta_font.render("PRODUCTION DETAILS", True, (160, 180, 210))
        prod_rect = prod_surf.get_rect()
        prod_rect.left = right_rect.left + 16
        prod_rect.centery = details_y
        screen.blit(prod_surf, prod_rect)

        is_fabricating = (total_ms > 0 and start_ticks > 0 and fabrication_progress < 1.0)
        # idle vs fabricating UI
        if not is_fabricating:
            # ----- IDLE: REQUIREMENTS + TIME + BUILD / INSUFFICIENT -----

            # "REQUIREMENTS"
            req_surf = name_font.render("REQUIREMENTS", True, UI_SECTION_TEXT_COLOR)
            req_rect = req_surf.get_rect()
            req_rect.left = right_rect.left + 16
            req_rect.centery = module_title_rect.centery
            screen.blit(req_surf, req_rect)
            row_y = req_rect.bottom + 28

            # ore preview image
            ore_size = 40
            ore_surf = pygame.transform.smoothscale(ore_preview_img, (ore_size, ore_size))
            ore_rect = ore_surf.get_rect()
            ore_rect.left = right_rect.left + 16
            ore_rect.centery = row_y
            screen.blit(ore_surf, ore_rect)

            # ore tier flag box
            flag_w = 70
            flag_h = 24
            flag_rect = pygame.Rect(0, 0, flag_w, flag_h)
            flag_rect.left = ore_rect.right + 12
            flag_rect.centery = ore_rect.centery
            draw_tier_icon(screen, flag_rect, ore_tier)
            pygame.draw.rect(screen, UI_NAV_LINE_COLOR, flag_rect, width=2)

            flag_text = f"{ore_letter}"
            flag_surf = stat_font.render(flag_text, True, UI_SECTION_TEXT_COLOR)
            flag_text_rect = flag_surf.get_rect(center=flag_rect.center)
            flag_text_rect.x -= 11
            screen.blit(flag_surf, flag_text_rect)

            # AVAILABLE / REQUIRED
            avail_text = f"{available_ore} / {ore_amount}"
            avail_color = UI_SECTION_TEXT_COLOR if not insufficient_resources else (220, 60, 60)
            avail_surf = stat_font.render(avail_text, True, avail_color)
            avail_rect = avail_surf.get_rect()
            avail_rect.right = right_rect.right - 20
            avail_rect.centery = ore_rect.centery
            screen.blit(avail_surf, avail_rect)

            # underline
            line_y = ore_rect.bottom
            pygame.draw.line(screen, UI_NAV_LINE_COLOR, (ore_rect.left, line_y), (avail_rect.right, line_y), 1)

            # --- TIME ROW (uses remaining_s, so it will match the shared timer) ---
            time_row_y = ore_rect.bottom + 26

            # clock icon
            clock_radius = 16
            clock_cx = ore_rect.left + clock_radius
            clock_cy = time_row_y
            pygame.draw.circle(screen, UI_TAB_TEXT_SELECTED, (clock_cx, clock_cy), clock_radius, 3)
            pygame.draw.line(screen, UI_TAB_TEXT_SELECTED, (clock_cx, clock_cy),
                             (clock_cx, clock_cy - clock_radius // 2), 2)
            pygame.draw.line(screen, UI_TAB_TEXT_SELECTED, (clock_cx, clock_cy),
                             (clock_cx + clock_radius // 2, clock_cy), 2)

            # TIME rect aligned with ore flag
            time_box_w = 56
            time_box_h = 24
            time_box_rect = pygame.Rect(0, 0, time_box_w, time_box_h)
            time_box_rect.left = flag_rect.left
            time_box_rect.centery = time_row_y
            pygame.draw.rect(screen, UI_ICON_BLUE, time_box_rect)
            time_label_surf = stat_font.render("TIME", True, (255, 255, 255))
            time_label_rect = time_label_surf.get_rect(center=time_box_rect.center)
            screen.blit(time_label_surf, time_label_rect)

            # text: total/remaining time (seconds)
            time_text = f"{remaining_s}s"
            time_surf = stat_font.render(time_text, True, UI_SECTION_TEXT_COLOR)
            time_rect = time_surf.get_rect()
            time_rect.centery = time_row_y
            time_rect.right = avail_rect.right
            screen.blit(time_surf, time_rect)

            # underline below time row
            line_y = time_box_rect.bottom + 8
            pygame.draw.line(screen, UI_NAV_LINE_COLOR, (ore_rect.left, line_y), (time_rect.right, line_y), 1)

            # BUILD button / insufficient banner
            WARNING_ORANGE = (255, 160, 40)
            if not insufficient_resources:
                build_color = (60, 200, 90)
                pygame.draw.rect(screen, build_color, build_btn_rect)
                build_text_surf = btn_font.render("BUILD", True, (10, 20, 10))
                build_text_rect = build_text_surf.get_rect(center=build_btn_rect.center)
                screen.blit(build_text_surf, build_text_rect)
            else:
                outer_bg = (8, 18, 40)
                pygame.draw.rect(screen, outer_bg, build_btn_rect)
                pygame.draw.rect(screen, WARNING_ORANGE, build_btn_rect, 2)

                icon_rect = build_btn_rect.copy()
                icon_rect.width = icon_rect.height
                icon_bg = (40, 22, 10)
                pygame.draw.rect(screen, icon_bg, icon_rect)
                pygame.draw.rect(screen, WARNING_ORANGE, icon_rect, 1)

                margin = icon_rect.width * 0.23
                top_y = icon_rect.top + margin
                bottom_y = icon_rect.bottom - margin
                left_x = icon_rect.left + margin
                right_x = icon_rect.right - margin
                tri_points = [
                    ((left_x + right_x) / 2, top_y),
                    (left_x, bottom_y),
                    (right_x, bottom_y),
                ]
                pygame.draw.polygon(screen, WARNING_ORANGE, tri_points)

                cx = (left_x + right_x) / 2
                ex_top = top_y + (bottom_y - top_y) * 0.35
                ex_bottom = bottom_y - (bottom_y - top_y) * 0.2
                pygame.draw.line(screen, outer_bg, (cx, ex_top), (cx, ex_bottom), 3)
                pygame.draw.circle(
                    screen,
                    outer_bg,
                    (int(cx), int(bottom_y - (bottom_y - top_y) * 0.1)),
                    2,
                )

                warn_text = "INSUFFICIENT RESOURCES"
                warn_surf = btn_font.render(warn_text, True, (255, 230, 120))
                warn_rect = warn_surf.get_rect()
                warn_rect.midleft = (icon_rect.right + 5, build_btn_rect.centery)
                screen.blit(warn_surf, warn_rect)

        else:
            # ----- FABRICATING: progress bar + timers + SPEED UP + CANCEL -----

            # timer at top-left (mm:ss)
            minutes = remaining_s // 60
            seconds = remaining_s % 60
            time_str = f"{minutes:02d}:{seconds:02d}"
            time_font = pygame.font.Font(None, 42)
            time_surf = time_font.render(time_str, True, (255, 255, 255))
            time_rect = time_surf.get_rect()
            time_rect.topleft = (right_rect.left + 10, prod_rect.bottom + 6)
            screen.blit(time_surf, time_rect)

            # percent at top-right
            pct = int(fabrication_progress * 100)
            pct_text = f"{pct} %"
            pct_surf = time_font.render(pct_text, True, (255, 255, 255))
            pct_rect = pct_surf.get_rect()
            pct_rect.topright = (right_rect.right - 10, time_rect.top)
            screen.blit(pct_surf, pct_rect)

            # long horizontal progress bar
            bar_y = time_rect.bottom + 24
            bar_h = 18
            bar_rect = pygame.Rect(
                right_rect.left + 10,
                bar_y,
                right_panel_w - 20,
                bar_h,
            )
            pygame.draw.rect(screen, (15, 45, 70), bar_rect)
            inner_w = int(bar_rect.width * fabrication_progress)
            if inner_w > 0:
                inner_rect = pygame.Rect(bar_rect.left, bar_rect.top, inner_w, bar_h)
                pygame.draw.rect(screen, (0, 220, 180), inner_rect)

            # SPEED UP button (grey)
            pygame.draw.rect(screen, (40, 60, 90), speed_btn_rect)
            pygame.draw.rect(screen, UI_NAV_LINE_COLOR, speed_btn_rect, 2)
            speed_surf = btn_font.render("SPEED UP", True, (255, 255, 255))
            speed_rect = speed_surf.get_rect(center=speed_btn_rect.center)
            screen.blit(speed_surf, speed_rect)

            # CANCEL button (bottom red)
            cancel_bg = (210, 40, 40)
            pygame.draw.rect(screen, cancel_bg, build_btn_rect)
            cancel_surf = btn_font.render("CANCEL", True, (255, 255, 255))
            cancel_rect = cancel_surf.get_rect(center=build_btn_rect.center)
            screen.blit(cancel_surf, cancel_rect)

        pygame.display.flip()