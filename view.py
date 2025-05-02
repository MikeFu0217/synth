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

# Draw
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
        # Draw a knob for the parameter
        draw_param_ring(screen, wave_name, param_name, value, font, radius)
    else:
        text = font.render(f'{value:.2f}', True, white)
        rect = text.get_rect(center=get_param_text_center(wave_name, param_name))
        screen.blit(text, rect)

def draw_param_ring(screen, wave_name, param_name, value, font, radius=11):
    """
    Draw a knob for the given parameter:
    - 'value' in [0,1] shown as a filled white sector.
    - Sector starts at 6 o'clock and moves clockwise.
    - Thin colored circle border indicates parameter group.
    """
    # determine center position for this (wave,param)
    center = get_param_text_center(wave_name, param_name)

    # calculate start angle (6 o'clock) and set up drawing resolution
    start_angle = -math.pi / 2
    steps = 60  # more steps = smoother sector fill

    # pick a border color by parameter group
    if param_name in ('vol', 'att', 'dec', 'sus', 'rel'):
        border_color = (0, 255, 0)          # green for envelope/volume
    elif param_name in ('L', 'M', 'H'):
        border_color = (255, 165, 0)        # orange for filter bands
    elif param_name in ('dec2', 'del', 'ref'):
        border_color = (0, 191, 255)        # blue for reverb
    else:
        border_color = (255, 105, 180)      # pink fallback

    # create a transparent surface just big enough for the knob
    size = radius * 2 + 2
    knob_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = radius + 1, radius + 1  # center of the knob on its surface

    # draw full black circle background
    pygame.draw.circle(knob_surf, black, (cx, cy), radius)

    # draw white sector from 6 o'clock clockwise proportional to 'value'
    for i in range(steps + 1):
        t = i / steps
        angle = start_angle - 2 * math.pi * t * value
        x = cx + radius * math.cos(angle)
        y = cy - radius * math.sin(angle)
        pygame.draw.line(knob_surf, white, (cx, cy), (x, y), 1)

    # draw the outer border
    pygame.draw.circle(knob_surf, border_color, (cx, cy), radius, 1)

    # blit the knob onto the main screen at its center position
    knob_rect = knob_surf.get_rect(center=center)
    screen.blit(knob_surf, knob_rect)

def draw_params(screen, font, sound):
    for channel in sound.channels:
        # Draw volume
        draw_param(screen, channel.waveform.name, 'vol', channel.volume, font)
        # Draw env_att
        draw_param(screen, channel.waveform.name, 'att', channel.envelopes[0].attack_time, font)
        # Draw env_dec
        draw_param(screen, channel.waveform.name, 'dec', channel.envelopes[0].decay_time, font)
        # Draw env_sus
        draw_param(screen, channel.waveform.name, 'sus', channel.envelopes[0].sustain_level, font)
        # Draw env_rel
        draw_param(screen, channel.waveform.name, 'rel', channel.envelopes[0].release_time, font)
        # Draw filter_L
        draw_param(screen, channel.waveform.name, 'L', channel.filters[0].low, font)
        # Draw filter_M
        draw_param(screen, channel.waveform.name, 'M', channel.filters[0].mid, font)
        # Draw filter_H
        draw_param(screen, channel.waveform.name, 'H', channel.filters[0].high, font)
        # Draw reverb_dec
        draw_param(screen, channel.waveform.name, 'dec2', channel.reverbs[0].decay, font)
        # Draw reverb_del
        draw_param(screen, channel.waveform.name, 'del', channel.reverbs[0].delay, font)
        # Draw reverb_ref
        draw_param(screen, channel.waveform.name, 'wet', channel.reverbs[0].wet, font)

def draw_texts(screen, font):
    text_saw = font.render('saw', True, white)
    rect_saw = text_saw.get_rect(center=(width // 9 * 2, height // 16))
    screen.blit(text_saw, rect_saw)
    text_sin = font.render('sin', True, white)
    rect_sin = text_sin.get_rect(center=(width // 9 * 3, height // 16))
    screen.blit(text_sin, rect_sin)
    text_sqr = font.render('sqr', True, white)
    rect_sqr = text_sqr.get_rect(center=(width // 9 * 4, height // 16))
    screen.blit(text_sqr, rect_sqr)

    text_vol = font.render('vol', True, white)
    rect_vol = text_vol.get_rect(center=(width // 9 * 1, height // 16 * 2))
    screen.blit(text_vol, rect_vol)
    
    text_att = font.render('att', True, white)
    rect_att = text_att.get_rect(center=(width // 9 * 1, height // 16 * 4))
    screen.blit(text_att, rect_att)
    text_dec = font.render('dec', True, white)
    rect_dec = text_dec.get_rect(center=(width // 9 * 1, height // 16 * 5))
    screen.blit(text_dec, rect_dec)
    text_sus = font.render('sus', True, white)
    rect_sus = text_sus.get_rect(center=(width // 9 * 1, height // 16 * 6))
    screen.blit(text_sus, rect_sus)
    text_rel = font.render('rel', True, white)
    rect_rel = text_rel.get_rect(center=(width // 9 * 1, height // 16 * 7))
    screen.blit(text_rel, rect_rel)

    text_L = font.render('L', True, white)
    rect_L = text_L.get_rect(center=(width // 9 * 1, height // 16 * 9))
    screen.blit(text_L, rect_L)
    text_M = font.render('M', True, white)
    rect_M = text_M.get_rect(center=(width // 9 * 1, height // 16 * 10))
    screen.blit(text_M, rect_M)
    text_H = font.render('H', True, white)
    rect_H = text_H.get_rect(center=(width // 9 * 1, height // 16 * 11))
    screen.blit(text_H, rect_H)

    text_dec2 = font.render('dec', True, white)
    rect_dec2 = text_dec2.get_rect(center=(width // 9 * 1, height // 16 * 13))
    screen.blit(text_dec2, rect_dec2)
    text_del = font.render('del', True, white)
    rect_del = text_del.get_rect(center=(width // 9 * 1, height // 16 * 14))
    screen.blit(text_del, rect_del)
    text_ref = font.render('wet', True, white)
    rect_ref = text_ref.get_rect(center=(width // 9 * 1, height // 16 * 15))
    screen.blit(text_ref, rect_ref)

def draw_box(screen, wave_name, param_name):
    box_width = width // 9 + 3
    box_height = height // 16 + 2
    line_width = 1
    color = white

    position = get_param_text_center(wave_name, param_name)
    position = (position[0] - width//9//2 - 2, position[1] - height//16//2 - 2)

    box_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
    box_surf.fill((0, 0, 0, 0))
    pygame.draw.rect(box_surf, color, (0, 0, box_width, box_height), line_width)
    screen.blit(box_surf, position)


green = (0, 255, 0)

# constants
OUTER_MARGIN = 5       # margin between panels & screen edge
INNER_PADDING = 5      # padding inside each panel
PANELS = 3             # waveform, envelope, filter

def _compute_panel_regions():
    """Return a list of (x, y, w, h) for the 3 stacked panels on right half."""
    side_x = width // 2
    side_w = width - side_x
    side_h = height

    # usable area on right half
    x0 = side_x
    w0 = side_w

    # divide vertically into 3, with OUTER_MARGIN between them
    total_margin = OUTER_MARGIN * (PANELS + 1)
    h0 = (side_h - total_margin) // PANELS

    regions = []
    for i in range(PANELS):
        xi = x0 + OUTER_MARGIN
        yi = OUTER_MARGIN + i * (h0 + OUTER_MARGIN)
        wi = w0 - 2 * OUTER_MARGIN
        hi = h0
        regions.append((xi, yi, wi, hi))
    return regions  # [(x1,y1,w1,h1), (x2,y2,w2,h2), (x3,y3,w3,h3)]

def draw_waveform_preview(screen, wave_name):
    panel, _, _ = _compute_panel_regions()
    x, y, w, h = panel

    # border
    pygame.draw.rect(screen, white, (x, y, w, h), 1)

    # inner region
    rx = x + INNER_PADDING
    ry = y + INNER_PADDING
    rw = w - 2 * INNER_PADDING
    rh = h - 2 * INNER_PADDING

    points = []
    samples = rw
    cycles = 2
    for i in range(samples):
        t = i / (samples - 1)
        phase = t * cycles

        if wave_name == 'sin':
            v = math.sin(2 * math.pi * phase)
        elif wave_name == 'saw':
            v = 2 * (phase % 1) - 1
        elif wave_name == 'sqr':
            v = 1.0 if (phase % 1) < 0.5 else -1.0
        else:
            raise ValueError(f"Unknown wave '{wave_name}'")

        px = rx + i
        # center vertically in rx→rx+rw, map v∈[-1,1] to ry+rh → ry
        cy = ry + rh / 2
        amp = rh / 2
        py = cy - v * amp

        points.append((int(px), int(py)))

    if len(points) > 1:
        pygame.draw.lines(screen, green, False, points, 1)


def draw_envelope_preview(screen, sound, wave_name):
    _, panel, _ = _compute_panel_regions()
    x, y, w, h = panel

    pygame.draw.rect(screen, white, (x, y, w, h), 1)

    rx = x + INNER_PADDING
    ry = y + INNER_PADDING
    rw = w - 2 * INNER_PADDING
    rh = h - 2 * INNER_PADDING

    # find channel
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

    bottom = ry + rh
    top = ry

    pts = [
        (rx,            bottom),
        (rx + a_w,      top),
        (rx + a_w + d_w, bottom - S * rh),
        (rx + rw - r_w,  bottom - S * rh),
        (rx + rw,        bottom),
    ]
    pygame.draw.lines(screen, green, False, pts, 1)


def draw_filter_preview(screen, sound, wave_name):
    *_, panel = _compute_panel_regions()
    x, y, w, h = panel

    pygame.draw.rect(screen, white, (x, y, w, h), 1)

    rx = x + INNER_PADDING
    ry = y + INNER_PADDING
    rw = w - 2 * INNER_PADDING
    rh = h - 2 * INNER_PADDING

    # find channel
    ch = next((c for c in sound.channels if c.waveform.name == wave_name), None)
    if not ch:
        return

    vals = [
        ch.filters[0].low,
        ch.filters[0].mid,
        ch.filters[0].high,
    ]

    # three vertical bars, equal spacing
    bar_w = rw / 7
    spacing = bar_w
    for i, v in enumerate(vals):
        bx = rx + spacing * (i + 1) + bar_w * i
        bh = rh * v
        by = ry + (rh - bh)
        pygame.draw.rect(screen, green, (int(bx), int(by), int(bar_w), int(bh)))


# update draw_screen:
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
    if AI_state == "listen":
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