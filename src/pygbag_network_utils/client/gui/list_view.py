import pygame

from .consts import BLACK, DARK_BLUE, FONT_SMALL, GRAY


class ListView:
    def __init__(self, x, y, width, height, items, item_height=30):
        self.rect = pygame.Rect(x, y, width, height)
        self.items = items
        self.item_height = item_height
        self.scroll_offset = 0
        self.scroll_speed = 10
        self.scrollbar_width = 10
        self.dragging = False
        self.drag_offset_y = 0
        self.scrollbar_rect = None

    def draw(self, surface):
        pygame.draw.rect(surface, GRAY, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)

        start_index = self.scroll_offset // self.item_height
        end_index = start_index + self.rect.height // self.item_height
        # logger.debug(f"Drawing items {start_index} to {end_index}")

        for i, item in enumerate(self.items[start_index:end_index], start=start_index):
            item_rect = pygame.Rect(
                self.rect.x,
                self.rect.y + (i - start_index) * self.item_height,
                self.rect.width,
                self.item_height,
            )
            # pygame.draw.rect(surface, WHITE, item_rect)
            text_surface = FONT_SMALL.render(f"{item}", True, BLACK)
            surface.blit(text_surface, (item_rect.x + 5, item_rect.y + 5))

        # Draw scrollbar
        if len(self.items) * self.item_height > self.rect.height:
            scrollbar_height = self.rect.height * (
                self.rect.height / (len(self.items) * self.item_height)
            )
            scrollbar_y = (
                self.rect.y
                + (self.scroll_offset / (len(self.items) * self.item_height))
                * self.rect.height
            )
            self.scrollbar_rect = pygame.Rect(
                self.rect.right - self.scrollbar_width,
                scrollbar_y,
                self.scrollbar_width,
                scrollbar_height,
            )
            pygame.draw.rect(surface, DARK_BLUE, self.scrollbar_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if (
                self.scrollbar_rect
                and event.button == 1
                and self.scrollbar_rect.collidepoint(event.pos)
            ):
                self.dragging = True
                self.drag_offset_y = event.pos[1] - self.scrollbar_rect.y
            elif event.button == 4 and self.rect.collidepoint(event.pos):  # Scroll up
                self.scroll_offset = max(self.scroll_offset - self.scroll_speed, 0)
            elif event.button == 5 and self.rect.collidepoint(event.pos):  # Scroll down
                max_offset = max(
                    0, len(self.items) * self.item_height - self.rect.height
                )
                self.scroll_offset = min(
                    self.scroll_offset + self.scroll_speed, max_offset
                )
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                new_y = event.pos[1] - self.drag_offset_y
                max_offset = max(
                    0, len(self.items) * self.item_height - self.rect.height
                )
                self.scroll_offset = int(
                    ((new_y - self.rect.y) / self.rect.height) * max_offset
                )
                self.scroll_offset = max(0, min(self.scroll_offset, max_offset))

    def update_items(self, new_itemlist):
        self.items = new_itemlist
