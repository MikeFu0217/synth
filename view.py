import math
import pygame, pigame
from pygame.locals import *
from sound import *
import time
import random
import colorsys

size = width, height = 320, 240
white = (255, 255, 255)
black = (0, 0, 0)

# waveform‐specific colors
SAW_COLOR = (255, 105, 180)   # bright pink
SIN_COLOR = (0, 255, 0)       # bright green
SQR_COLOR = (135, 206, 235)   # sky blue
COLOR_MAP = {
    'saw': SAW_COLOR,
    'sin': SIN_COLOR,
    'sqr': SQR_COLOR
}

# Draw parameter text positions
def get_param_text_center(wave_name, param_name):
    x = None
    y = None
    if wave_name == 'saw':
        x = width // 9 * 2
    elif wave_name == 'sin':
        x = width // 9 * 3
    elif wave_name == 'sqr':
        x = width // 9 * 4
    else:
        raise ValueError("Invalid wave name")

    if param_name == 'vol':
        y = height // 16 * 2
    elif param_name == 'att':
        y = height // 16 * 4
    elif param_name == 'dec':
        y = height // 16 * 5
    elif param_name == 'sus':
        y = height // 16 * 6
    elif param_name == 'rel':
        y = height // 16 * 7
    elif param_name == 'L':
        y = height // 16 * 9
    elif param_name == 'M':
        y = height // 16 * 10
    elif param_name == 'H':
        y = height // 16 * 11
    elif param_name == 'dec2':
        y = height // 16 * 13
    elif param_name == 'del':
        y = height // 16 * 14
    elif param_name == 'wet':
        y = height // 16 * 15
    else:
        raise ValueError("Invalid parameter name")

    return (x, y)

def draw_param(screen, wave_name, param_name, value, font, radius=5, zoom=False):
    if zoom:
        draw_param_ring(screen, wave_name, param_name, value, font, radius)
    else:
        text = font.render(f'{value:.2f}', True, COLOR_MAP.get(wave_name, white))
        rect = text.get_rect(center=get_param_text_center(wave_name, param_name))
        screen.blit(text, rect)

def draw_param_ring(screen, wave_name, param_name, value, font, radius=11):
    """
    Draw a knob for the given parameter:
    - 'value' in [0,1] shown as a filled white sector.
    - Sector starts at 6 o'clock and moves clockwise.
    - Thin colored circle border indicates the channel (waveform).
    """
    center = get_param_text_center(wave_name, param_name)
    start_angle = -math.pi / 2
    steps = 60

    # border color by waveform
    border_color = COLOR_MAP.get(wave_name, white)

    # background circle
    size_px = radius * 2 + 2
    knob_surf = pygame.Surface((size_px, size_px), pygame.SRCALPHA)
    cx, cy = radius + 1, radius + 1
    pygame.draw.circle(knob_surf, black, (cx, cy), radius)

    # filled sector
    for i in range(steps + 1):
        t = i / steps
        angle = start_angle - 2 * math.pi * t * value
        x = cx + radius * math.cos(angle)
        y = cy - radius * math.sin(angle)
        pygame.draw.line(knob_surf, white, (cx, cy), (x, y), 1)

    # waveform‐colored border
    pygame.draw.circle(knob_surf, border_color, (cx, cy), radius, 1)

    screen.blit(knob_surf, knob_surf.get_rect(center=center))

def draw_params(screen, font, sound):
    for channel in sound.channels:
        wn = channel.waveform.name
        draw_param(screen, wn, 'vol' , channel.volume               , font)
        draw_param(screen, wn, 'att' , channel.envelopes[0].attack_time , font)
        draw_param(screen, wn, 'dec' , channel.envelopes[0].decay_time  , font)
        draw_param(screen, wn, 'sus' , channel.envelopes[0].sustain_level, font)
        draw_param(screen, wn, 'rel' , channel.envelopes[0].release_time , font)
        draw_param(screen, wn, 'L'   , channel.filters[0].low        , font)
        draw_param(screen, wn, 'M'   , channel.filters[0].mid        , font)
        draw_param(screen, wn, 'H'   , channel.filters[0].high       , font)
        draw_param(screen, wn, 'dec2', channel.reverbs[0].decay      , font)
        draw_param(screen, wn, 'del' , channel.reverbs[0].delay      , font)
        draw_param(screen, wn, 'wet' , channel.reverbs[0].wet        , font)

def draw_texts(screen, font):
    # static labels, always white
    text_saw = font.render('SAW', True, white)
    screen.blit(text_saw, text_saw.get_rect(center=(width // 9 * 2, height // 16)))
    text_sin = font.render('SIN', True, white)
    screen.blit(text_sin, text_sin.get_rect(center=(width // 9 * 3, height // 16)))
    text_sqr = font.render('SQR', True, white)
    screen.blit(text_sqr, text_sqr.get_rect(center=(width // 9 * 4, height // 16)))

    # parameter names, always white
    for name, y_mul in [('VOL',2),('ATT',4),('DEC',5),('SUS',6),('REL',7),
                        ('L',9),('M',10),('H',11),('DEC',13),('DEL',14),('WET',15)]:
        txt = font.render(name, True, white)
        screen.blit(txt, txt.get_rect(center=(width//9*1, height//16*y_mul)))

def draw_box(screen, wave_name, param_name):
    box_width  = width // 9 + 3
    box_height = height // 16 + 2
    pos = get_param_text_center(wave_name, param_name)
    pos = (pos[0] - box_width//2, pos[1] - box_height//2)
    surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
    pygame.draw.rect(surf, white, (0,0,box_width,box_height), 1)
    screen.blit(surf, pos)

# preview panels layout
OUTER_MARGIN = 5
INNER_PADDING = 5
PANELS = 3

def _compute_panel_regions():
    side_x = width // 2
    side_w = width - side_x
    side_h = height
    total_margin = OUTER_MARGIN * (PANELS + 1)
    h0 = (side_h - total_margin) // PANELS
    regions = []
    for i in range(PANELS):
        xi = side_x + OUTER_MARGIN
        yi = OUTER_MARGIN + i * (h0 + OUTER_MARGIN)
        wi = side_w - 2 * OUTER_MARGIN
        hi = h0
        regions.append((xi, yi, wi, hi))
    return regions

def draw_waveform_preview(screen, wave_name):
    panel, _, _ = _compute_panel_regions()
    x, y, w, h = panel
    pygame.draw.rect(screen, white, (x, y, w, h), 1)
    rx, ry = x + INNER_PADDING, y + INNER_PADDING
    rw, rh = w - 2*INNER_PADDING, h - 2*INNER_PADDING

    pts = []
    samples = rw
    cycles = 2
    for i in range(samples):
        t = i / (samples - 1)
        phase = t * cycles
        if wave_name == 'sin':
            v = math.sin(2*math.pi*phase)
        elif wave_name == 'saw':
            v = 2*(phase % 1) - 1
        elif wave_name == 'sqr':
            v = 1.0 if (phase % 1) < 0.5 else -1.0
        px = rx + i
        cyc = ry + rh/2
        py = cyc - v * (rh/2)
        pts.append((int(px), int(py)))

    color = COLOR_MAP.get(wave_name, white)
    if len(pts) > 1:
        pygame.draw.lines(screen, color, False, pts, 1)

def draw_envelope_preview(screen, sound, wave_name):
    _, panel, _ = _compute_panel_regions()
    x, y, w, h = panel
    pygame.draw.rect(screen, white, (x, y, w, h), 1)
    rx, ry = x + INNER_PADDING, y + INNER_PADDING
    rw, rh = w - 2*INNER_PADDING, h - 2*INNER_PADDING

    ch = next((c for c in sound.channels if c.waveform.name == wave_name), None)
    if not ch:
        return

    A = ch.envelopes[0].attack_time
    D = ch.envelopes[0].decay_time
    S = ch.envelopes[0].sustain_level
    R = ch.envelopes[0].release_time
    total = (A + D + R) or 1

    a_w = rw * (A / total)
    d_w = rw * (D / total)
    r_w = rw * (R / total)
    bottom, top = ry + rh, ry

    pts = [
        (rx, bottom),
        (rx + a_w, top),
        (rx + a_w + d_w, bottom - S * rh),
        (rx + rw - r_w, bottom - S * rh),
        (rx + rw, bottom),
    ]
    color = COLOR_MAP.get(wave_name, white)
    pygame.draw.lines(screen, color, False, pts, 1)

def draw_filter_preview(screen, sound, wave_name):
    *_, panel = _compute_panel_regions()
    x, y, w, h = panel
    pygame.draw.rect(screen, white, (x, y, w, h), 1)
    rx, ry = x + INNER_PADDING, y + INNER_PADDING
    rw, rh = w - 2*INNER_PADDING, h - 2*INNER_PADDING

    ch = next((c for c in sound.channels if c.waveform.name == wave_name), None)
    if not ch:
        return

    vals = [ch.filters[0].low, ch.filters[0].mid, ch.filters[0].high]
    bar_w = rw / 7
    spacing = bar_w
    color = COLOR_MAP.get(wave_name, white)
    for i, v in enumerate(vals):
        bx = rx + spacing*(i+1) + bar_w*i
        bh = rh * v
        by = ry + (rh - bh)
        pygame.draw.rect(screen, color, (int(bx), int(by), int(bar_w), int(bh)))

def draw_screen(screen, font, sound, wave_name, param_name):
    screen.fill(black)
    draw_texts(screen, font)
    draw_params(screen, font, sound)
    draw_box(screen, wave_name, param_name)
    draw_waveform_preview(screen, wave_name)
    draw_envelope_preview(screen, sound, wave_name)
    draw_filter_preview(screen, sound, wave_name)
    pygame.display.update()


class Particle:
    def __init__(self, x, y, vx, vy, life, size, hue):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.size = size
        self.hue = hue

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surf):
        if self.life <= 0:
            return
        # Calculate alpha fade and brightness fade
        frac = max(0, self.life / PARTICLE_LIFE)
        alpha = int(255 * frac)
        # Compute RGB from hue, with full saturation & value scaled by frac
        r_f, g_f, b_f = colorsys.hsv_to_rgb(self.hue, 1.0, frac)
        color = (int(r_f * 255), int(g_f * 255), int(b_f * 255), alpha)
        radius = int(self.size * frac)
        if radius > 0:
            pygame.draw.circle(surf, color, (int(self.x), int(self.y)), radius)

# module‐level particle lists & timing
PARTICLE_LIFE = 1.0
_listen_particles = []
_speak_particles = []
_last_time = time.time()

def draw_AI_interface(screen, font, AI_state):
    global _last_time, _listen_particles, _speak_particles

    # compute dt
    now = time.time()
    dt = now - _last_time
    _last_time = now

    # clear screen
    screen.fill(black)

    # compute pulsing radius & alpha
    sin_val = math.sin(2 * math.pi * now / 2.0)
    radius = int(45 + 15 * sin_val)
    alpha = int(((sin_val + 1) / 2) * (230 - 50) + 50)

    # compute dynamic hue based on time (cycle every 5 seconds)
    hue = (now / 5.0) % 1.0
    # base RGB for ring/fill
    r_f, g_f, b_f = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    ring_color = (
        int(r_f * 255), int(g_f * 255), int(b_f * 255),
        int(alpha * 0.6)
    )
    fill_color = (
        int(r_f * 255), int(g_f * 255), int(b_f * 255),
        alpha
    )

    # prepare glow surface
    glow = pygame.Surface((width, height), pygame.SRCALPHA)
    # outer ring
    pygame.draw.circle(
        glow, ring_color,
        (width//2, height//2),
        radius + 4, 4
    )
    # inner fill
    pygame.draw.circle(
        glow, fill_color,
        (width//2, height//2),
        radius
    )
    screen.blit(glow, (0, 0))

    # spawn & update particles
    if AI_state == "reasoning":
        # --- reasoning: draw a static ring with rotating points + ambient particles ---
        cx, cy = width // 2, height // 2
        const_radius = 45  # fixed radius for reasoning state

        # initialize rotating‐dot angles and ambient list on first entry
        if not hasattr(draw_AI_interface, "_reason_angles"):
            num_dots = 16
            draw_AI_interface._reason_angles = [
                i * 2 * math.pi / num_dots for i in range(num_dots)
            ]
            draw_AI_interface._reason_particles = []

        # draw the static ring outline
        pygame.draw.circle(screen, white, (cx, cy), const_radius, 2)

        # update & draw rotating dots around the ring
        angular_speed = math.pi / 2  # half-circle per second
        for i, angle in enumerate(draw_AI_interface._reason_angles):
            # advance each dot’s angle
            new_angle = (angle + angular_speed * dt) % (2 * math.pi)
            draw_AI_interface._reason_angles[i] = new_angle
            x = cx + const_radius * math.cos(new_angle)
            y = cy + const_radius * math.sin(new_angle)
            pygame.draw.circle(screen, white, (int(x), int(y)), 3)

        # spawn a few ambient particles from the ring
        spawn_rate = 5  # particles per second
        if random.random() < spawn_rate * dt:
            a = random.random() * 2 * math.pi
            px = cx + const_radius * math.cos(a)
            py = cy + const_radius * math.sin(a)
            speed = random.uniform(10, 30)
            vx = math.cos(a) * speed
            vy = math.sin(a) * speed
            hue_p = hue
            size = random.uniform(2, 4)
            draw_AI_interface._reason_particles.append(
                Particle(px, py, vx, vy, PARTICLE_LIFE, size, hue_p)
            )

        # update & draw ambient particles
        for p in draw_AI_interface._reason_particles[:]:
            p.update(dt)
            p.draw(screen)
            if p.life <= 0:
                draw_AI_interface._reason_particles.remove(p)

        # render centered "Thinking..." text
        txt = font.render("Thinking...", True, white)
        screen.blit(txt, txt.get_rect(center=(cx, cy)))

        pygame.display.update()
        return

    elif AI_state == "listen":
        # spawn inbound particles with same hue
        for _ in range(2):
            angle = random.random() * 2*math.pi
            px = width/2 + (radius+5) * math.cos(angle)
            py = height/2 + (radius+5) * math.sin(angle)
            speed = random.uniform(20, 60)
            vx = -math.cos(angle) * speed
            vy = -math.sin(angle) * speed
            _listen_particles.append(
                Particle(px, py, vx, vy, PARTICLE_LIFE, random.uniform(2,5), hue)
            )
        # update & draw
        for p in _listen_particles[:]:
            p.update(dt)
            p.draw(screen)
            if p.life <= 0:
                _listen_particles.remove(p)

    else:  # "speak"
        # spawn outbound burst particles with varied hue offset
        for _ in range(3):
            angle = random.random() * 2*math.pi
            speed = random.uniform(50, 100)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            # give each particle a slight hue variation
            ph = (hue + random.uniform(-0.1, 0.1)) % 1.0
            _speak_particles.append(
                Particle(width/2, height/2, vx, vy, PARTICLE_LIFE, random.uniform(3,7), ph)
            )
        for p in _speak_particles[:]:
            p.update(dt)
            p.draw(screen)
            if p.life <= 0:
                _speak_particles.remove(p)

    # 5. Static size, dynamic grayscale color
    cx, cy = width//2, height//2
    label = "Listening..." if AI_state == "listen" else "Speaking..."
    # choose a fixed font size per state
    font_size = 28 if AI_state == "listen" else 32
    text_font = pygame.font.Font(None, font_size)

    # recompute the 2 s sine oscillation
    sin_val = math.sin(2 * math.pi * now / 2.0)  # now is from your dt code

    # set up different gray centers & amplitudes
    if AI_state == "listen":
        gray_center, gray_amp = 200, 55   # pulses between 145 and 255
    else:
        gray_center, gray_amp = 100, 60   # pulses between 40 and 160

    # compute dynamic gray and clamp
    gray = int(gray_center + gray_amp * sin_val)
    gray = max(0, min(255, gray))
    text_color = (gray, gray, gray)

    # render & blit at center
    txt_surf = text_font.render(label, True, text_color)
    txt_rect = txt_surf.get_rect(center=(cx, cy))
    screen.blit(txt_surf, txt_rect)

    # 6. Present the frame
    pygame.display.update()