import sys
import time
import random
import math
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

clone_bullets = []
clone_shoot_cooldown = 1000  # Cooldown time in milliseconds for shooting
clone_shot_limit = 5# Number of shots each clone can fire

window_width = 800
window_height = 800
road_left = 100
road_right = window_width - 100
road_line_y = 0  # Initial position of road lines

aladdin_x = window_width // 2
aladdin_y = 50
aladdin_speed = 20
left_forearm_up = True
right_forearm_up = False
last_update_time = 0
jump=False

obstacle = []
bullets = []
score = 0
missed_circles = 0
misfires = 0
game_over = False
paused = False

scenery_offset_y = 0  # New variable to track scenery vertical offset

# Add new variables for duplicate Aladdins as obstacles
aladdin_clones = [
    {'x': random.randint(road_left + 10, road_right - 10), 'y': window_height, 'radius': 20},
    {'x': random.randint(road_left + 10, road_right - 10), 'y': window_height + 200, 'radius': 20},
    {'x': random.randint(road_left + 10, road_right - 10), 'y': window_height + 400, 'radius': 20},
    {'x': random.randint(road_left + 10, road_right - 10), 'y': window_height + 600, 'radius': 20}
]

# Add a health variable
aladdin_health = 100

# Add a list to store clone bullets
clone_bullets = []

# Add a shooting cooldown for clones
clone_shoot_cooldown = 4000  # Time in milliseconds between shots for each clone

# Add a shooting limit for clones
clone_shot_limit = 5  # Each clone can only fire 5 shots

def midpoint_line(x0, y0, x1, y1):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    glPointSize(5)
    glBegin(GL_LINES)
    glVertex2f(x0, y0)
    glVertex2f(x1, y1)
    glEnd()

def midpoint_circle(x_center, y_center, radius):
   def draw_circle_points(x_center, y_center, x, y):
    """Function to plot the eight symmetric points of the circle."""
    points = [
        (x_center + x, y_center + y),
        (x_center - x, y_center + y),
        (x_center + x, y_center - y),
        (x_center - x, y_center - y),
        (x_center + y, y_center + x),
        (x_center - y, y_center + x),
        (x_center + y, y_center - x),
        (x_center - y, y_center - x)
    ]
    for p in points:
        glVertex2i(*p)  # OpenGL function to plot points

def midpoint_circle(x_center, y_center, radius):
    x = 0
    y = radius
    d = 1 - radius  # Correct initialization for midpoint algorithm
    glPointSize(3)
    draw_circle_points(x_center, y_center, x, y)

    while x < y:
        if d < 0:
            d = d + 2 * x + 3
        else:
            d = d + 2 * (x - y) + 5
            y -= 1
        x += 1
        draw_circle_points(x_center, y_center, x, y)

def draw_aladdin():
    global aladdin_x, aladdin_y, left_forearm_up, right_forearm_up
    
    glColor3f(.4, .3, 0) 
    # Draw Aladdin's head
    for i in range(10):
        midpoint_circle(aladdin_x, aladdin_y + 40, i)
    glColor3f(1.0, 1.0, 0.0)  # Set color to yellow
    # Draw Aladdin's body using closely spaced lines to fill
    for y in range(aladdin_y, aladdin_y + 30):
        midpoint_line(aladdin_x - 10, y, aladdin_x + 10, y)

    # Draw Aladdin's arms using closely spaced lines to fill
    for y in range(aladdin_y + 20, aladdin_y + (35 if left_forearm_up else 5), 1 if left_forearm_up else -1):
        midpoint_line(aladdin_x - 10, y, aladdin_x - 20, y)

    for y in range(aladdin_y + 20, aladdin_y + (5 if left_forearm_up else 35), -1 if left_forearm_up else 1):
        midpoint_line(aladdin_x + 10, y, aladdin_x + 20, y)

def update_forearm_positions():
    global left_forearm_up, right_forearm_up, last_update_time
    current_time = time.time()
    if last_update_time == 0:
        last_update_time = current_time

    elapsed_time = current_time - last_update_time
    if elapsed_time >= 0.5:
        left_forearm_up = not left_forearm_up
        right_forearm_up = not right_forearm_up
        last_update_time = current_time

def draw_tree(x, y):
    # Draw tree trunk
    glColor3f(0.55, 0.27, 0.07)  # Brown color for the trunk
    glBegin(GL_QUADS)
    glVertex2f(x - 5, y)
    glVertex2f(x + 5, y)
    glVertex2f(x + 5, y + 15)
    glVertex2f(x - 5, y + 15)
    glEnd()

    # Draw tree foliage with dark green
    glColor3f(0.0, 0.1, 0.0)  # Dark green for foliage
    glBegin(GL_TRIANGLES)  # Using triangles for a filled effect
    glVertex2f(x, y + 20)  # Top of the foliage
    glVertex2f(x - 15, y + 5)  # Left base
    glVertex2f(x + 15, y + 5)  # Right base
    glEnd()

    glBegin(GL_TRIANGLES)  # Additional layer for more fullness
    glVertex2f(x, y + 30)  # Top of the foliage
    glVertex2f(x - 10, y + 15)  # Left base
    glVertex2f(x + 10, y + 15)  # Right base
    glEnd()

def draw_lamppost(x, y):
    # Draw lamppost base
    glColor3f(0.75, 0.75, 0.75)  # Grey color
    glBegin(GL_QUADS)
    glVertex2f(x - 2, y)
    glVertex2f(x + 2, y)
    glVertex2f(x + 2, y + 20)
    glVertex2f(x - 2, y + 20)
    glEnd()

    # Draw lamppost light
    glColor3f(1.0, 1.0, 0.0)  # Yellow color
    midpoint_circle(x, y + 25, 3)

def draw_scenery():
    global road_left, road_right, scenery_offset_y
    # Draw basic green background on the sides of the road
    glColor3f(0.2, 0.8, 0.2)  # Basic green for the background
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(road_left, 0)
    glVertex2f(road_left, window_height)
    glVertex2f(0, window_height)
    glEnd()

    glBegin(GL_QUADS)
    glVertex2f(road_right, 0)
    glVertex2f(window_width, 0)
    glVertex2f(window_width, window_height)
    glVertex2f(road_right, window_height)
    glEnd()

    # Draw the darkest green trees along the roadside
    glColor3f(0.0, 0.1, 0.0)  # Darkest green for trees
    for i in range(0, window_height, 100):
        draw_tree(road_left - 20, (i + scenery_offset_y) % window_height)
        draw_tree(road_right + 20, (i + scenery_offset_y) % window_height)

    # Draw decorative elements (e.g., lampposts)
    for i in range(50, window_height, 150):
        draw_lamppost(road_left + 10, (i + scenery_offset_y) % window_height)
        draw_lamppost(road_right - 10, (i + scenery_offset_y) % window_height)

def draw_road():
    # Draw track background with a maroon red color
    glColor3f(0.5, 0.0, 0.0)  # Maroon red for the track
    glBegin(GL_QUADS)
    glVertex2f(road_left, 0)
    glVertex2f(road_right, 0)
    glVertex2f(road_right, window_height)
    glVertex2f(road_left, window_height)
    glEnd()

    # Draw lane markings in black
    glColor3f(0.0, 0.0, 0.0)  # Black color for lane markings
    lane_width = (road_right - road_left) / 6  # Assuming 4 lanes

    # Draw straight lane markings
    for lane in range(1, 6):  # Draw 3 lane lines (4 lanes total)
        x = road_left + lane * lane_width
        glBegin(GL_LINES)
        glVertex2f(x, 0)
        glVertex2f(x, window_height)
        glEnd()

    # Draw dashed lines for the lanes
    for i in range(-40, window_height, 80):
        y = road_line_y + i
        if y >= 0 and y <= window_height:
            midpoint_line((road_left + road_right) // 2, y, (road_left + road_right) // 2, y + 40)

    # Draw lane numbers
    glColor3f(1.0, 1.0, 1.0)  # White color for lane numbers
    for lane in range(1, 5):  # Assuming 4 lanes
        x = road_left + lane * lane_width - lane_width / 2
        render_text(x - 10, window_height - 50, str(lane))  # Adjust y position as needed

def draw_circle_points(x_center, y_center, x, y):
    glBegin(GL_POINTS)
    glVertex2f(x_center + x, y_center + y)
    glVertex2f(x_center - x, y_center + y)
    glVertex2f(x_center + x, y_center - y)
    glVertex2f(x_center - x, y_center - y)
    glVertex2f(x_center + y, y_center + x)
    glVertex2f(x_center - y, y_center + x)
    glVertex2f(x_center + y, y_center - x)
    glVertex2f(x_center - y, y_center - x)
    glEnd()

def draw_obstacle(x, y):
    glColor3f(1.0, 1.0, 1.0)  # White color for the obstacle
    midpoint_line(x + 20, y, x - 20, y) # Down
    midpoint_line(x + 20, y + 10, x - 20, y + 10) # Up
    midpoint_line(x + 20, y, x + 20, y + 10) # Right
    midpoint_line(x - 20, y, x - 20, y + 10) # Left

def convert_coordinate(x, y):
    global window_width, window_height
    a = x - (window_width / 2)
    b = (window_height / 2) - y
    return a, b
def timer(value):
    global obstacle, missed_circles, game_over, score, bullets, road_line_y, jump, aladdin_y, scenery_offset_y, aladdin_clones, clone_bullets, aladdin_health
    if game_over or paused:
        glutTimerFunc(70, timer, 0)  # Update every 16 milliseconds (~60 FPS)
        return
    update_forearm_positions()  # Update forearm positions

    road_line_y -= 2  # Move the road lines downward more smoothly
    if road_line_y < -40:
        road_line_y = 0
        
    scenery_offset_y -= 2  # Move scenery elements downward
    if scenery_offset_y < -window_height:
        scenery_offset_y = 0
        
    if jump:
        aladdin_y += 4
        if aladdin_y >= 100:
            jump = False
    elif aladdin_y > 50:
        aladdin_y -= 4
    
    if random.randint(0, 100) > 98:  # Reduced probability for fewer falling blocks
        radius = random.randint(20, 30)
        x = random.randint(150, window_width - 150)  # Random x position
        y = window_height
        obstacle.append({'x': x, 'y': y, 'radius': radius})

    # Randomly generate new Aladdin clones as enemies
    if len(aladdin_clones) < 4 and random.randint(0, 200) > 198:  # Adjust probability and limit
        clone_x = random.randint(road_left + 10, road_right - 10)
        aladdin_clones.append({'x': clone_x, 'y': window_height, 'radius': 20, 'speed': random.randint(2, 5)})

    # Move bullets and check for collisions
    new_bullets = []
    for bullet in bullets:
        bullet['x'] += bullet['dx']
        bullet['y'] += bullet['dy']

        # Check collision with obstacles
        for circle in obstacle:
            dist = math.sqrt((bullet['x'] - circle['x'])**2 + (bullet['y'] - circle['y'])**2)
            if dist <= bullet['radius'] + circle['radius']:  # Check collision
                score += 1
                obstacle.remove(circle)
                break
        else:
            # Check collision with Aladdin clones
            for clone in aladdin_clones:
                dist = math.sqrt((bullet['x'] - clone['x'])**2 + (bullet['y'] - clone['y'])**2)
                if dist <= bullet['radius'] + clone['radius']:  # Check collision
                    score += 5  # Increase score by 5 when a clone is shot
                    aladdin_clones.remove(clone)
                    break
            else:
                new_bullets.append(bullet)  # Keep bullet if no collision

    bullets = new_bullets  # Update bullets list

    # Move clone bullets and check for collisions
    new_clone_bullets = []
    for bullet in clone_bullets:
        bullet['x'] += bullet['dx']
        bullet['y'] += bullet['dy']

        # Check collision with Aladdin
        dist_to_aladdin = math.sqrt((bullet['x'] - aladdin_x)**2 + (bullet['y'] - aladdin_y)**2)
        if dist_to_aladdin <= bullet['radius'] + 10:  # Approximate Aladdin's size
            aladdin_health -= 10  # Decrease health by 10
            if aladdin_health <= 0:
                game_over = True
            continue  # Skip adding this bullet to new_clone_bullets
        else:
            new_clone_bullets.append(bullet)

    clone_bullets = new_clone_bullets

    for circle in obstacle:
        circle['y'] -= 2  # Move 2 pixels downward

        # Rocket and circle collision
        dist_to_aladdin = math.sqrt((circle['x'] - aladdin_x - 10)**2 + (circle['y'] - aladdin_y - 50)**2)
        if dist_to_aladdin < circle['radius']:
            if jump and aladdin_y > 50:  # Check if Aladdin is jumping
                score += 1  # Award point for dodging
                obstacle.remove(circle)  # Remove the dodged obstacle
            else:
                aladdin_health -= 20  # Decrease health by 20
                if aladdin_health <= 0:
                    game_over = True
                obstacle.remove(circle)  # Remove the obstacle after collision

    # Remove obstacles that have moved off the screen
    new_circles = []
    for circle in obstacle:
        if circle['y'] > 0:
            new_circles.append(circle)
        else:
            missed_circles += 1
            if missed_circles >= 3:
                game_over = True

    obstacle = new_circles

    # Update Aladdin clones
    update_aladdin_clones()

    glutPostRedisplay()
    glutTimerFunc(70, timer, 0)  # Update every 16 milliseconds (~60 FPS)

def draw_buttons():
    global score, missed_circles, aladdin_health
    render_text(20, window_height - 100, f"Score: {score}")
    render_text(20, window_height - 120, f"Missed: {missed_circles}")
    render_text(20, window_height - 140, f"Health: {aladdin_health}")

    # Back Button (Arrow)
    glColor3f(0.0, 0.0, 0.0)
    midpoint_line(30, window_height - 30, 20, window_height - 40)
    midpoint_line(20, window_height - 40, 30, window_height - 50)
    midpoint_line(20, window_height - 40, 40, window_height - 40)

    # Pause Button
    glColor3f(1.0, 1.0,1.0)
    midpoint_line(70, window_height - 50, 70, window_height - 25)
    midpoint_line(80, window_height - 50, 80, window_height - 25)

    # Cross Button (Exit)
    glColor3f(1.0, 0.0, 0.0)
    midpoint_line(120, window_height - 50, 140, window_height - 30)
    midpoint_line(120, window_height - 30, 140, window_height - 50)

def keyboard(key, x, y):
    global aladdin_x, aladdin_y, aladdin_speed, bullets, misfires, game_over, jump
    if game_over:
        return
    if key == b'a':  # Move left
        aladdin_x = max(aladdin_x - aladdin_speed, road_left + 10)
    elif key == b'd':  # Move right
        aladdin_x = min(aladdin_x + aladdin_speed, road_right - 10)
    elif key == b'w':  # Move forward (up)
        aladdin_y = min(aladdin_y + aladdin_speed, window_height - 50)
    elif key == b's':  # Move backward (down)
        aladdin_y = max(aladdin_y - aladdin_speed, 0)
    elif key == b'f':  # Fire bullet
        bullets.append({'x': aladdin_x, 'y': aladdin_y + 70, 'radius': 5, 'dx': 0, 'dy': 10})
    elif key == b' ':  # Jump
        jump = True

def mouse(button, state, x, y):
    global game_over, paused, aladdin_x, aladdin_y
    y = window_height - y
    target_x, target_y = x, y
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if 20 <= x <= 40 and window_height - 50 <= y <= window_height - 30:
            reset_game()
        elif 70 <= x <= 80 and window_height - 50 <= y <= window_height - 25:
            toggle_pause()
        elif 120 <= x <= 140 and window_height - 50 <= y <= window_height - 30:
            exit_game()
        # Ensure the target is within the road boundaries
        if road_left < target_x < road_right:
            dx = target_x - aladdin_x
            dy = target_y - (aladdin_y + 70)
            dist = math.sqrt(dx**2 + dy**2)
            dx /= dist
            dy /= dist
            bullets.append({'x': aladdin_x, 'y': aladdin_y + 70, 'dx': dx * 10, 'dy': dy * 10, 'radius': 5})

def reset_game():
    global aladdin_x, aladdin_y, aladdin_speed, obstacle, bullets, score, missed_circles, misfires, game_over, paused
    aladdin_x = window_width // 2
    aladdin_y = 50
    aladdin_speed = 20
    obstacle = []
    bullets = []
    score = 0
    missed_circles = 0
    misfires = 0
    game_over = False
    paused = False

def toggle_pause():
    global paused
    paused = not paused
    print(f"Game paused: {paused}")  # Debugging line to check pause state

def exit_game():
    global game_over, obstacle, bullets
    game_over = True
    obstacle.clear()
    bullets.clear()
    glutPostRedisplay()

def draw_aladdin_clone_obstacle(clone):
    x, y = clone['x'], clone['y']
    glColor3f(0.0, 0.0, 1.0)  # Blue color for clones

    # Draw Aladdin's head
    for i in range(10):
        glColor3f(0.0, 0.0,0.0)#black color for clones
        midpoint_circle(x, y + 40, i)
    for i in range(10):
        glColor3f(0.0, 0.0,0.0)
    midpoint_line(x - 10, y + 30, x + 10, y + 30)
    midpoint_line(x - 10, y, x - 10, y + 30)
    midpoint_line(x + 10, y, x + 10, y + 30)
    midpoint_line(x - 10, y, x + 10, y)

    midpoint_line(x - 10, y + 20, x - 20, y + 20)
    midpoint_line(x + 10, y + 20, x + 20, y + 20)
    if left_forearm_up:
        midpoint_line(x - 20, y + 20, x - 20, y + 35)
        midpoint_line(x + 20, y + 20, x + 20, y + 5)
    else:
        midpoint_line(x - 20, y + 20, x - 20, y + 5)
        midpoint_line(x + 20, y + 20, x + 20, y + 35)
dclone_bullets = []
clone_shoot_cooldown = 1000  # Cooldown time in milliseconds for shooting
clone_shot_limit = 3  # Number of shots each clone can fire

def update_aladdin_clones():
    global game_over, score, clone_bullets
    for clone in aladdin_clones:
        clone['y'] -= 1  # Reduce the speed to make clones move slower

        # Check collision with Aladdin
        dist_to_aladdin = math.sqrt((clone['x'] - aladdin_x - 10)**2 + (clone['y'] - aladdin_y - 50)**2)
        if dist_to_aladdin < clone['radius']:
            if jump and aladdin_y > 50:  # Check if Aladdin is jumping
                score += 1  # Award point for dodging
                aladdin_clones.remove(clone)  # Remove the dodged clone
            else:
                game_over = True  # Game over if Aladdin collides with a clone
        # Allow each clone to shoot only when it's inside the window
        if 0 <= clone['y'] <= window_height:
            # Update shooting logic to respect the shot limit
            if 'shots_fired' not in clone:
                clone['shots_fired'] = 0  # Initialize shots fired count

            current_time = time.time() * 1000  # Current time in milliseconds
            if current_time - clone.get('last_shot_time', 0) > clone_shoot_cooldown and clone['shots_fired'] < clone_shot_limit:
                clone_bullets.append({'x': clone['x'], 'y': clone['y'], 'dx': 0, 'dy': -5, 'radius': 5})
                clone['last_shot_time'] = current_time  # Update last shot time
                clone['shots_fired'] += 1  # Increment shots fired

    # Remove clones that have moved off the screen
    aladdin_clones[:] = [clone for clone in aladdin_clones if clone['y'] > 0]

def display():
    global score
    glClear(GL_COLOR_BUFFER_BIT)

    draw_road()
    draw_scenery()
    draw_aladdin()  # Draw the main Aladdin
    draw_buttons()

    # Draw bullets
    glColor3f(1.0, 1.0, 0.0)
    for bullet in bullets:
        midpoint_circle(bullet['x'], bullet['y'], bullet['radius'])

    # Draw clone bullets
    glColor3f(1.0, 0.0, 0.0)
    for bullet in clone_bullets:
        midpoint_circle(bullet['x'], bullet['y'], bullet['radius'])

    # Draw obstacles
    for circle in obstacle:
        glColor3f(1.0, 1.0, 1.0)
        draw_obstacle(circle['x'], circle['y'])

    # Draw Aladdin clone obstacles
    for clone in aladdin_clones:
        draw_aladdin_clone_obstacle(clone)

    if game_over:
        render_text(window_width // 2 - 80, window_height // 2, f"Game Over!! Final Score: {score}")
        glutSwapBuffers()
        return

    glutSwapBuffers()

def render_text(x, y, text):
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Dictator's Dash")
    glClearColor(0, 0, 0, 0)
    gluOrtho2D(0, window_width, 0, window_height)
    glutDisplayFunc(display)
    glutTimerFunc(0, timer, 0)
    glutMouseFunc(mouse)
    glutKeyboardFunc(keyboard)
    glutMainLoop()

if __name__ == "__main__":
    main()