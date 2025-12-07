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
    UI_NAV_LINE_COLOR
    )

from spacegame.models.modules.fabricatormodule import (
    FabricatorModule,
    get_fabricator_modules_for_ship,
)


def fabrication_main_screen(main_player, player_fleet):
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

    # ----- BIG CENTER RECT (AROUND THE PLUS-CIRCLE) -----
    plus_radius = 120
    preview_center = (width // 2, height // 2)
    big_rect_pad = 100
    big_rect = pygame.Rect(
        preview_center[0] - plus_radius - big_rect_pad,
        preview_center[1] - plus_radius - big_rect_pad,
        (plus_radius + big_rect_pad) * 2,
        (plus_radius + big_rect_pad) * 2
    )


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


                # BIG CENTER RECT -> OPEN BLUEPRINT SELECT
                if big_rect.collidepoint(mx, my):
                    from spacegame.screens.fabrication_bpselect_screen import fabrication_bpselect_screen
                    res = fabrication_bpselect_screen(main_player, player_fleet, selected_fabricator_index)
                    if res == "to_game":
                        return "to_game"
                    elif isinstance(res, int):
                        selected_fabricator_index = res

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
        content_top = nav_bottom_y + 24  # same as used when we built card_rect

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

        # progress bar inside ALL slot squares (selected or not)
        fabrication_progress = 0.0  # 0 = idle, >0 once fabrication has started
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

        title_font = pygame.font.Font(None, 36)
        module_title = title_font.render("FABRICATOR", True, UI_SECTION_TEXT_COLOR)
        module_title_rect = module_title.get_rect()
        module_title_rect.topleft = (details_x, details_y)
        screen.blit(module_title, module_title_rect)

        # description lines (to the right of the square)
        desc_font = pygame.font.Font(None, 20)
        desc_lines = [
            "A standard fabricator module, used for",
            "on-ship fabrication for weapons and",
            "strike craft.",
        ]
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

        # Statistics for the currently selected fabricator module (slot 01 / 02 / ...)
        if 0 <= selected_fabricator_index < len(fabricator_modules):
            fabricator_module = fabricator_modules[selected_fabricator_index]
        else:
            fabricator_module = FabricatorModule()

        stat_rows = [
            ("Module Size:", str(fabricator_module.module_size)),
            ("Base Fabrication Time:", str(fabricator_module.base_fabrication_time)),
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

        # Center big plus-circle (production slot) — centralized to middle of screen
        plus_radius = 120
        preview_center = (width // 2, height // 2)
        pygame.draw.circle(screen, (200, 220, 235), preview_center, plus_radius, 3)
        # small plus inside
        px, py = preview_center
        pygame.draw.line(screen, (200, 220, 235), (px - 36, py), (px + 36, py), 4)
        pygame.draw.line(screen, (200, 220, 235), (px, py - 36), (px, py + 36), 4)

        # Corner-only rect around big circle (like the 01 square corners)
        big_corner_len = 28
        big_corner_thick = 4
        corner_color = UI_TAB_TEXT_SELECTED
        # top-left
        pygame.draw.line(screen, corner_color, (big_rect.left, big_rect.top), (big_rect.left + big_corner_len, big_rect.top), big_corner_thick)
        pygame.draw.line(screen, corner_color, (big_rect.left, big_rect.top), (big_rect.left, big_rect.top + big_corner_len), big_corner_thick)
        # top-right
        pygame.draw.line(screen, corner_color, (big_rect.right - big_corner_len, big_rect.top), (big_rect.right, big_rect.top), big_corner_thick)
        pygame.draw.line(screen, corner_color, (big_rect.right, big_rect.top), (big_rect.right, big_rect.top + big_corner_len), big_corner_thick)
        # bottom-left
        pygame.draw.line(screen, corner_color, (big_rect.left, big_rect.bottom - big_corner_len), (big_rect.left, big_rect.bottom), big_corner_thick)
        pygame.draw.line(screen, corner_color, (big_rect.left, big_rect.bottom), (big_rect.left + big_corner_len, big_rect.bottom), big_corner_thick)
        # bottom-right
        pygame.draw.line(screen, corner_color, (big_rect.right - big_corner_len, big_rect.bottom), (big_rect.right, big_rect.bottom), big_corner_thick)
        pygame.draw.line(screen, corner_color, (big_rect.right, big_rect.bottom - big_corner_len), (big_rect.right, big_rect.bottom), big_corner_thick)

        # Bottom green button (centered)
        btn_w = 380
        btn_h = 36
        btn_x = width // 2 - btn_w // 2
        btn_y = height - 100
        btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        BTN_LIGHT_GREEN = (96, 255, 144)
        pygame.draw.rect(screen, BTN_LIGHT_GREEN, btn_rect, width=2, border_radius=0)
        btn_label = section_font.render("ADD BLUEPRINT FOR PRODUCTION", True, BTN_LIGHT_GREEN)
        btn_label_rect = btn_label.get_rect(center=btn_rect.center)
        screen.blit(btn_label, btn_label_rect)

        pygame.display.flip()