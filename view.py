import math
import pygame, pigame
from pygame.locals import *
from sound import *

size = width, height = 320, 240
white = (255, 255, 255)
black = (0, 0, 0)

def initialize_view(screen):
    screen.fill(black)

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
    elif param_name == 'ref':
        y = height // 16 * 15
    else:
        raise ValueError("Invalid parameter name")

    return (x, y)

def draw_param(screen, wave_name, param_name, value, font):
    text = font.render(f'{value:.1f}', True, white)
    rect = text.get_rect(center=get_param_text_center(wave_name, param_name))
    screen.blit(text, rect)

def draw_params(screen, font, sound):
    for i, channel in enumerate(sound.channels):
        # Draw volume
        volume = sound.get_volume(channel)
        draw_param(screen, channel.waveform.name, 'vol', volume, font)
        # Draw env_att
        env_att = sound.get_env_att(channel)
        draw_param(screen, channel.waveform.name, 'att', env_att, font)
        # Draw env_dec
        env_dec = sound.get_env_dec(channel)
        draw_param(screen, channel.waveform.name, 'dec', env_dec, font)
        # Draw env_sus
        env_sus = sound.get_env_sus(channel)
        draw_param(screen, channel.waveform.name, 'sus', env_sus, font)
        # Draw env_rel
        env_rel = sound.get_env_rel(channel)
        draw_param(screen, channel.waveform.name, 'rel', env_rel, font)
        # Draw filter_L
        filter_L = sound.get_filter_L(channel)
        draw_param(screen, channel.waveform.name, 'L', filter_L, font)
        # Draw filter_M
        filter_M = sound.get_filter_M(channel)
        draw_param(screen, channel.waveform.name, 'M', filter_M, font)
        # Draw filter_H
        filter_H = sound.get_filter_H(channel)
        draw_param(screen, channel.waveform.name, 'H', filter_H, font)
        # Draw reverb_dec
        reverb_dec = sound.get_reverb_dec(channel)
        draw_param(screen, channel.waveform.name, 'dec2', reverb_dec, font)
        # Draw reverb_del
        reverb_del = sound.get_reverb_del(channel)
        draw_param(screen, channel.waveform.name, 'del', reverb_del, font)
        # Draw reverb_ref
        reverb_ref = sound.get_reverb_ref(channel)
        draw_param(screen, channel.waveform.name, 'ref', reverb_ref, font)

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
    text_ref = font.render('ref', True, white)
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

def draw_waveform_preview(screen, wave_name):
    """
    Draw a 2-cycle waveform preview (sine, saw, or square)
    in the upper-right, with 1/6 horizontal and 1/10 vertical margins,
    framed in white, trace in green.
    """
    # screen inset
    margin = 5
    preview_w = int(width / 2.3)
    preview_h = int(height / 3.2)
    x = width - preview_w - margin
    y = margin

    # draw border
    rect = pygame.Rect(x, y, preview_w, preview_h)
    pygame.draw.rect(screen, white, rect, 1)

    # compute inner drawing region
    region_h = preview_h * 4 / 5            # fill 4/5 vertically
    vert_margin = (preview_h - region_h) / 2
    region_w = preview_w * 5 / 6            # fill 4/6 horizontally
    horiz_margin = (preview_w - region_w) / 2

    # sample points
    points = []
    n_samples = preview_w                   # resolution
    periods = 2                             # two full cycles
    for i in range(n_samples):
        t = i / (n_samples - 1)
        phase = t * periods

        if wave_name == 'sin':
            v = math.sin(2 * math.pi * phase)
        elif wave_name == 'saw':
            v = 2 * (phase % 1) - 1
        elif wave_name == 'sqr':
            v = 1.0 if (phase % 1) < 0.5 else -1.0
        else:
            raise ValueError(f"Unknown wave '{wave_name}'")

        # map to pixel coords within the inner region
        px = x + horiz_margin + (i / (n_samples - 1)) * region_w
        py = y + vert_margin + (region_h / 2) * (1 - v)
        points.append((int(px), int(py)))

    # draw the green trace
    if len(points) > 1:
        pygame.draw.lines(screen, green, False, points, 1)

def draw_screen(screen, font, sound, wave_name, param_name):
    screen.fill(black)
    draw_texts(screen, font)
    draw_params(screen, font, sound)
    draw_box(screen, wave_name, param_name)
    draw_waveform_preview(screen, wave_name)
    pygame.display.update()