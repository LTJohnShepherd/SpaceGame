import pygame

# ---------- UI helpers ----------
class Button:
    """Simple rectangular button with hover color and click handling."""

    def __init__(self, rect, text, font, base_color=(170,170,170), hover_color=(220,220,220), text_color=(0,0,0)):
        self.rect = pygame.Rect(rect) #pygame.Rect(left, top, width, height) , rect is a tupple with those values, pygame.Rect() create a Rect object for the button (stores position and size)
        self.text = text #text for the button
        self.font = font
        self.base_color = base_color # the color of the button
        self.hover_color = hover_color # the color of the button when you hover on it with the mouse.
        self.text_color = text_color 

    def draw(self, surface):# surface: the screen you want to draw on

        mouse_pos = pygame.mouse.get_pos() #position of the mouse on the screen

        if self.rect.collidepoint(mouse_pos): # set button color depending on mouse hover
            color = self.hover_color
        else:
            color = self.base_color

        pygame.draw.rect(surface, color, self.rect, border_radius=12) # pygame.draw.rect(surface, color, rect (object), width=0, border_radius=0)
        
        label = self.font.render(self.text, True, self.text_color) # render the button text into a new surface (text becomes an image that can be drawn)
        
        label_rect = label.get_rect(center=self.rect.center) # create a Rect for the text surface and center it inside the button's rectangle
        
        surface.blit(label, label_rect) # draw (blit) the rendered text onto the target surface at the calculated position

    # Handle mouse click events: returns True if the left mouse button was pressed
    # while the cursor is positioned over the button; otherwise returns False.
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False
