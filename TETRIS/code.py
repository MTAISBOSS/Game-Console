import time
import board
import pwmio
import displayio
import digitalio
import adafruit_ili9341
import asyncio
import random
import busio
from adafruit_display_text import label
import terminalio
from melody_player import MelodyPlayer

# Release any previously used displays
displayio.release_displays()

# Define pins for the ILI9341 display
cs_pin = board.GP18
reset_pin = board.GP17
dc_pin = board.GP16
mosi_pin = board.GP3
clk_pin = board.GP2

# Initialize SPI
spi = busio.SPI(clock=clk_pin, MOSI=mosi_pin)

# Initialize the display bus
display_bus = displayio.FourWire(spi, command=dc_pin, chip_select=cs_pin, reset=reset_pin)

# Initialize the ILI9341 display (rotation set to 90 for vertical orientation)
display = adafruit_ili9341.ILI9341(display_bus, width=240, height=320, rotation=90)

# Initialize buttons
button_right = digitalio.DigitalInOut(board.GP15)
button_right.direction = digitalio.Direction.INPUT
button_right.pull = digitalio.Pull.UP

button_left = digitalio.DigitalInOut(board.GP14)
button_left.direction = digitalio.Direction.INPUT
button_left.pull = digitalio.Pull.UP

button_down = digitalio.DigitalInOut(board.GP13)
button_down.direction = digitalio.Direction.INPUT
button_down.pull = digitalio.Pull.UP

button_rotate = digitalio.DigitalInOut(board.GP12)
button_rotate.direction = digitalio.Direction.INPUT
button_rotate.pull = digitalio.Pull.UP

# Create display groups for walls/ground, landed blocks, active Tetromino, score, and next Tetromino
walls_ground_group = displayio.Group()
landed_blocks_group = displayio.Group()
active_tetromino_group = displayio.Group()
score_group = displayio.Group()
next_tetromino_group = displayio.Group()

# Add groups to the display
display.root_group = displayio.Group()
display.root_group.append(walls_ground_group)
display.root_group.append(landed_blocks_group)
display.root_group.append(active_tetromino_group)
display.root_group.append(score_group)
display.root_group.append(next_tetromino_group)

# Tetris grid settings
GRID_WIDTH = 12
GRID_HEIGHT = 24
BLOCK_SIZE = 12  # Match the size of your BMP image

# Load colored BMP files
BLOCKS = [
    displayio.OnDiskBitmap("block_orange.bmp"),  # Orange
    displayio.OnDiskBitmap("block_green.bmp"),  # Green
    displayio.OnDiskBitmap("block_red.bmp"),  # Red
    displayio.OnDiskBitmap("block_blue.bmp"),  # Blue
    displayio.OnDiskBitmap("block_cyan.bmp"),  # Cyan
    displayio.OnDiskBitmap("block_grey.bmp"),  # Grey
    displayio.OnDiskBitmap("block.bmp"),  # Normal
]

# Tetromino shapes and their corresponding block colors
SHAPES = [
    ([[1, 1, 1, 1]], 0),  # I (Orange)
    ([[1, 1], [1, 1]], 1),  # O (Green)
    ([[1, 1, 1], [0, 1, 0]], 2),  # T (Red)
    ([[1, 1, 0], [0, 1, 1]], 3),  # S (Blue)
    ([[0, 1, 1], [1, 1, 0]], 1),  # Z (Cyan)
    ([[1, 1, 1], [1, 0, 0]], 0),  # L (Grey)
    ([[1, 1, 1], [0, 0, 1]], 2),  # J (Red)
]

# Initialize the grid
grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

# Add walls and ground
def initialize_walls_and_ground():
    for y in range(GRID_HEIGHT):
        grid[y][0] = 5  # Left wall (Grey)
        grid[y][GRID_WIDTH - 1] = 5  # Right wall (Grey)
    for x in range(GRID_WIDTH):
        grid[GRID_HEIGHT - 1][x] = 5  # Ground (Grey)

# Initialize walls and ground
initialize_walls_and_ground()

# Score system
score = 0

# Function to draw walls and ground
def draw_walls_and_ground():
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if grid[y][x] == 5:  # Walls and ground are represented by 5
                tile = displayio.TileGrid(BLOCKS[5], pixel_shader=BLOCKS[5].pixel_shader, x=x*BLOCK_SIZE, y=y*BLOCK_SIZE)
                walls_ground_group.append(tile)

# Function to draw the active Tetromino
def draw_active_tetromino(shape, x, y, color_index):
    # Clear the active Tetromino group before redrawing
    while len(active_tetromino_group) > 0:
        active_tetromino_group.pop()
    # Draw the active Tetromino
    for row in range(len(shape)):
        for col in range(len(shape[row])):
            if shape[row][col]:
                tile = displayio.TileGrid(BLOCKS[color_index], pixel_shader=BLOCKS[color_index].pixel_shader, x=(x + col)*BLOCK_SIZE, y=(y + row)*BLOCK_SIZE)
                active_tetromino_group.append(tile)

# Function to draw the next Tetromino preview
def draw_next_tetromino(shape, color_index):
    # Clear the next Tetromino group before redrawing
    while len(next_tetromino_group) > 0:
        next_tetromino_group.pop()
    # Draw the "NEXT" label
    next_label = label.Label(terminalio.FONT, text="NEXT", color=0xFFFFFF, x=180, y=70)
    next_tetromino_group.append(next_label)
    # Draw the next Tetromino in the preview area
    preview_x = GRID_WIDTH + 2  # Position the preview on the right side of the grid
    preview_y = 7  # Position the preview at the top
    for row in range(len(shape)):
        for col in range(len(shape[row])):
            if shape[row][col]:
                tile = displayio.TileGrid(BLOCKS[color_index], pixel_shader=BLOCKS[color_index].pixel_shader, x=(preview_x + col)*BLOCK_SIZE, y=(preview_y + row)*BLOCK_SIZE)
                next_tetromino_group.append(tile)

# Function to place the shape in the grid and add it to the landed blocks group
def place_shape(shape, x, y, color_index):
    for row in range(len(shape)):
        for col in range(len(shape[row])):
            if shape[row][col]:
                grid[y + row][x + col] = color_index + 1  # Store color index in grid
                # Add the landed block to the landed blocks group
                tile = displayio.TileGrid(BLOCKS[color_index], pixel_shader=BLOCKS[color_index].pixel_shader, x=(x + col)*BLOCK_SIZE, y=(y + row)*BLOCK_SIZE)
                landed_blocks_group.append(tile)

# Function to check for collisions
def check_collision(shape, x, y):
    for row in range(len(shape)):
        for col in range(len(shape[row])):
            if shape[row][col]:
                if x + col < 0 or x + col >= GRID_WIDTH or y + row >= GRID_HEIGHT or grid[y + row][x + col]:
                    return True
    return False

# Function to rotate the shape
def rotate_shape(shape):
    return [list(row) for row in zip(*shape[::-1])]

# Function to clear lines and update score
def clear_lines():
    global score
    lines_cleared = 0
    rows_to_remove = []
    for row in range(GRID_HEIGHT - 1):  # Skip the ground row
        if all(grid[row]):
            rows_to_remove.append(row)
            lines_cleared += 1

    # Remove the completed lines from the grid
    for row in rows_to_remove:
        del grid[row]
        grid.insert(0, [0 for _ in range(GRID_WIDTH)])

    # Update the score
    score += lines_cleared * 100  # Increase score by 100 points per line

    # Redraw the landed blocks group to reflect the updated grid
    while len(landed_blocks_group) > 0:
        landed_blocks_group.pop()
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if grid[y][x] and grid[y][x] != 5:  # Skip walls and ground
                block_index = grid[y][x] - 1  # Convert grid value to block index
                tile = displayio.TileGrid(BLOCKS[block_index], pixel_shader=BLOCKS[block_index].pixel_shader, x=x*BLOCK_SIZE, y=y*BLOCK_SIZE)
                landed_blocks_group.append(tile)

    return lines_cleared

# Function to display the score
def display_score():
    # Clear the score group before updating
    while len(score_group) > 0:
        score_group.pop()
    score_label = label.Label(terminalio.FONT, text=f"Score: {score}", color=0xFFFFFF, x=180, y=10)
    score_group.append(score_label)

# Function to display game over
def display_game_over():
    game_over_label = label.Label(terminalio.FONT, text="Game Over!", color=0xFF0000, x=170, y=150)
    final_score_label = label.Label(terminalio.FONT, text=f"Final Score: {score}", color=0xFFFFFF, x=160, y=170)
    score_group.append(game_over_label)
    score_group.append(final_score_label)

# Non-blocking debounce function
class ButtonDebouncer:
    def __init__(self, button):
        self.button = button
        self.last_state = button.value
        self.last_debounce_time = 0
        self.debounce_delay = 0.1  # Debounce delay in seconds

    def debounced_press(self):
        current_state = self.button.value
        if current_state != self.last_state:
            self.last_debounce_time = time.monotonic()
        self.last_state = current_state

        if (time.monotonic() - self.last_debounce_time) > self.debounce_delay:
            if not current_state:  # Button is pressed
                return True
        return False

# Initialize debouncers for buttons
debouncer_left = ButtonDebouncer(button_left)
debouncer_right = ButtonDebouncer(button_right)
debouncer_down = ButtonDebouncer(button_down)
debouncer_rotate = ButtonDebouncer(button_rotate)

# Tetris game logic
async def tetris_game():
    global score
    current_shape, current_color_index = random.choice(SHAPES)
    next_shape, next_color_index = random.choice(SHAPES)  # Initialize the next Tetromino
    current_x = GRID_WIDTH // 2 - len(current_shape[0]) // 2
    current_y = 0

    # Draw walls and ground (only once, as they don't change)
    draw_walls_and_ground()

    # Draw the next Tetromino preview
    draw_next_tetromino(next_shape, next_color_index)

    while True:
        # Draw the active Tetromino
        draw_active_tetromino(current_shape, current_x, current_y, current_color_index)

        # Display the score
        display_score()

        # Check for button presses using debouncers
        if debouncer_left.debounced_press():
            new_x = current_x - 1
            if not check_collision(current_shape, new_x, current_y):
                current_x = new_x

        if debouncer_right.debounced_press():
            new_x = current_x + 1
            if not check_collision(current_shape, new_x, current_y):
                current_x = new_x

        if debouncer_down.debounced_press():
            new_y = current_y + 1
            if not check_collision(current_shape, current_x, new_y):
                current_y = new_y

        if debouncer_rotate.debounced_press():
            rotated_shape = rotate_shape(current_shape)
            if not check_collision(rotated_shape, current_x, current_y):
                current_shape = rotated_shape

        # Move the shape down
        new_y = current_y + 1
        if check_collision(current_shape, current_x, new_y):
            place_shape(current_shape, current_x, current_y, current_color_index)
            lines_cleared = clear_lines()
            # Update the current and next Tetromino
            current_shape, current_color_index = next_shape, next_color_index
            next_shape, next_color_index = random.choice(SHAPES)
            draw_next_tetromino(next_shape, next_color_index)  # Update the next Tetromino preview
            current_x = GRID_WIDTH // 2 - len(current_shape[0]) // 2
            current_y = 0
            if check_collision(current_shape, current_x, current_y):
                display_game_over()
                await asyncio.sleep(3)  # Show game over screen for 3 seconds
                break  # Game over
        else:
            current_y = new_y

        await asyncio.sleep(0.2)  # Adjust speed here

# Main function to run both tasks concurrently
async def main():
    player = MelodyPlayer()  # Initialize the MelodyPlayer
    await asyncio.gather(
        tetris_game(),  # Run the Tetris game
        player.play_melody()  # Play the melody concurrently
    )

# Run the main function
asyncio.run(main())