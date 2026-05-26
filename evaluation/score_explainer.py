"""
TRACE - Speed Safety Score Explainer One-Pager
A single-page PDF designed for non-technical government and policy audiences.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(BASE_DIR, 'outputs', 'TRACE_Score_Explainer.pdf')

RED    = colors.HexColor('#C0392B')
ORANGE = colors.HexColor('#E67E22')
YELLOW = colors.HexColor('#D4AC0D')
GREEN  = colors.HexColor('#1E8449')
NAVY   = colors.HexColor('#1A2744')
SLATE  = colors.HexColor('#2C3E50')
LGRAY  = colors.HexColor('#F4F6F7')
MGRAY  = colors.HexColor('#BDC3C7')
DGRAY  = colors.HexColor('#717D7E')
WHITE  = colors.white

W, H = A4
M = 18*mm


def para(c_obj, text, x, y, width, style):
    p = Paragraph(text, style)
    w, h = p.wrap(width, 999)
    p.drawOn(c_obj, x, y - h)
    return h


def draw_rounded_rect(c_obj, x, y, w, h, r, fill_color, stroke_color=None):
    c_obj.setFillColor(fill_color)
    if stroke_color:
        c_obj.setStrokeColor(stroke_color)
        c_obj.setLineWidth(0.5)
    else:
        c_obj.setStrokeColor(fill_color)
    c_obj.roundRect(x, y, w, h, r, fill=1, stroke=1 if stroke_color else 0)


def draw_pill(c_obj, x, y, w, h, color, label, text_color=WHITE, fontsize=8):
    draw_rounded_rect(c_obj, x, y, w, h, h/2, color)
    c_obj.setFillColor(text_color)
    c_obj.setFont('Helvetica-Bold', fontsize)
    c_obj.drawCentredString(x + w/2, y + h/2 - fontsize*0.35, label)


def build():
    c = canvas.Canvas(OUTPUT, pagesize=A4)
    c.setTitle('TRACE Speed Safety Score - Explainer')

    c.setFillColor(NAVY)
    c.rect(0, H - 52*mm, W, 52*mm, fill=1, stroke=0)

    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 20)
    c.drawString(M, H - 20*mm, 'TRACE Speed Safety Score')
    c.setFont('Helvetica', 10)
    c.setFillColor(colors.HexColor('#A9CCE3'))
    c.drawString(M, H - 29*mm, 'Tiered Road Alignment and Composite Evaluation')

    tagline = (
        'A tool that assesses whether posted speed limits are set at the right level '
        'for the road, its users, and the people most at risk.'
    )
    tag_style = ParagraphStyle('tag', fontName='Helvetica', fontSize=9,
                               textColor=colors.HexColor('#D6EAF8'),
                               leading=13, alignment=TA_LEFT)
    para(c, tagline, M, H - 36*mm, W - 2*M, tag_style)

    badge_x = W - M - 38*mm
    badge_y = H - 50*mm
    draw_rounded_rect(c, badge_x, badge_y, 38*mm, 38*mm, 4,
                      colors.HexColor('#243660'), colors.HexColor('#3D5A99'))
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(badge_x + 19*mm, badge_y + 22*mm, '0-100')
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#A9CCE3'))
    c.drawCentredString(badge_x + 19*mm, badge_y + 14*mm, 'Speed Safety Score')
    c.drawCentredString(badge_x + 19*mm, badge_y + 9*mm, 'per road segment')

    cur_y = H - 56*mm

    body_style = ParagraphStyle('body', fontName='Helvetica', fontSize=9,
                                textColor=SLATE, leading=13.5, alignment=TA_JUSTIFY)
    head_style = ParagraphStyle('head', fontName='Helvetica-Bold', fontSize=11,
                                textColor=NAVY, leading=14, alignment=TA_LEFT)

    cur_y -= 6*mm
    h = para(c, 'What does the score measure?', M, cur_y, W - 2*M, head_style)
    cur_y -= h + 3*mm

    intro = (
        'The Speed Safety Score (SSS) measures how well a road\'s posted speed limit '
        'is aligned with three independent evidence sources: how fast traffic actually '
        'moves, what the road\'s physical environment implies about safe speed, and '
        'whether the limit protects the most vulnerable road users. A score of 100 '
        'means full alignment. A score below 40 signals that the limit warrants '
        'immediate review.'
    )
    h = para(c, intro, M, cur_y, W - 2*M, body_style)
    cur_y -= h + 6*mm

    h = para(c, 'How the score is built', M, cur_y, W - 2*M, head_style)
    cur_y -= h + 3*mm

    tier_data = [
        {
            'num': 'T1',
            'color': colors.HexColor('#1F618D'),
            'title': 'Operating speed alignment',
            'body': (
                'Compares the 85th percentile operating speed (V85) with the posted '
                'limit. When traffic consistently moves 15% or more above the limit, '
                'the road is structurally out of step with what the sign says. '
                'High speed variance between the median and V85 is also penalised, '
                'because it indicates the limit is not producing a coherent speed regime.'
            ),
            'weight': '35%',
        },
        {
            'num': 'T2',
            'color': colors.HexColor('#117A65'),
            'title': 'Road environment alignment',
            'body': (
                'Assesses whether the road\'s physical context, its functional class, '
                'land use, and urban density, supports the posted limit. A narrow urban '
                'secondary road adjacent to market activity implies a safe speed below '
                '40 km/h. If the posted limit is 70 km/h, the environment and the sign '
                'are in conflict. Street imagery analysis refines this assessment '
                'where Mapillary coverage is available.'
            ),
            'weight': '35%',
        },
        {
            'num': 'T3',
            'color': colors.HexColor('#7B241C'),
            'title': 'VRU protection threshold',
            'body': (
                'Applies Safe System biomechanical speed thresholds to the posted limit, '
                'weighted by estimated pedestrian, cyclist, and powered two-wheeler '
                'exposure. The Safe System framework establishes that pedestrians cannot '
                'survive vehicle impacts above 30 km/h, and cyclists above 40 km/h. '
                'On roads where these users are present, limits above these thresholds '
                'mean the system does not tolerate human error.'
            ),
            'weight': '30%',
        },
    ]

    tier_box_h = 24*mm
    tier_gap   = 3*mm
    tier_w     = (W - 2*M - 2*tier_gap) / 3

    for i, t in enumerate(tier_data):
        tx = M + i * (tier_w + tier_gap)
        ty = cur_y - tier_box_h
        draw_rounded_rect(c, tx, ty, tier_w, tier_box_h, 3, LGRAY, stroke_color=MGRAY)
        c.setFillColor(t['color'])
        c.roundRect(tx, ty + tier_box_h - 8*mm, tier_w, 8*mm, 3, fill=1, stroke=0)
        c.rect(tx, ty + tier_box_h - 8*mm, tier_w, 4*mm, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 9)
        c.drawString(tx + 3*mm, ty + tier_box_h - 5.5*mm, t['num'])
        c.setFont('Helvetica', 8)
        c.drawRightString(tx + tier_w - 3*mm, ty + tier_box_h - 5.5*mm,
                          f'Weight: {t["weight"]}')
        t_style = ParagraphStyle('ts', fontName='Helvetica-Bold', fontSize=7.5,
                                 textColor=NAVY, leading=10)
        para(c, t['title'], tx + 3*mm, ty + tier_box_h - 10*mm, tier_w - 6*mm, t_style)
        b_style = ParagraphStyle('tb', fontName='Helvetica', fontSize=7,
                                 textColor=SLATE, leading=10, alignment=TA_JUSTIFY)
        para(c, t['body'], tx + 3*mm, ty + tier_box_h - 16.5*mm, tier_w - 6*mm, b_style)

    cur_y -= tier_box_h + 6*mm

    formula_style = ParagraphStyle('fm', fontName='Helvetica', fontSize=8.5,
                                   textColor=DGRAY, leading=12, alignment=TA_CENTER)
    h = para(c, 'SSS = 0.35 x T1 + 0.35 x T2 + 0.30 x T3', M, cur_y, W - 2*M, formula_style)
    cur_y -= h + 6*mm

    h = para(c, 'Priority classification', M, cur_y, W - 2*M, head_style)
    cur_y -= h + 3*mm

    bands = [
        (RED,    'P1 - Immediate Review', 'SSS below 40',
         'Severe misalignment across multiple tiers. Recommend for immediate '
         'speed limit review or road safety audit.'),
        (ORANGE, 'P2 - Secondary Review', 'SSS 40 to 59',
         'Meaningful misalignment on at least one tier. Include in the next '
         'scheduled review cycle.'),
        (YELLOW, 'P3 - Monitor',          'SSS 60 to 79',
         'Some misalignment present, not yet at priority intervention level. '
         'Flag for periodic monitoring.'),
        (GREEN,  'Acceptable',            'SSS 80 and above',
         'No significant misalignment detected across the three tiers.'),
    ]

    band_h  = 11.5*mm
    band_gap = 2*mm

    for color, title, score_range, desc in bands:
        by = cur_y - band_h
        draw_rounded_rect(c, M, by, 2.5*mm, band_h, 1, color)
        c.setFillColor(color)
        c.setFont('Helvetica-Bold', 8.5)
        c.drawString(M + 5*mm, by + band_h - 4*mm, title)
        c.setFillColor(DGRAY)
        c.setFont('Helvetica', 7.5)
        c.drawString(M + 5*mm, by + band_h - 8.5*mm, score_range)
        d_style = ParagraphStyle('ds', fontName='Helvetica', fontSize=7.5,
                                 textColor=SLATE, leading=10.5, alignment=TA_JUSTIFY)
        para(c, desc, M + 46*mm, by + band_h - 3*mm, W - M - 46*mm - M, d_style)
        cur_y -= band_h + band_gap

    cur_y -= 4*mm

    h = para(c, 'Reading a segment result', M, cur_y, W - 2*M, head_style)
    cur_y -= h + 3*mm

    card_h = 28*mm
    draw_rounded_rect(c, M, cur_y - card_h, W - 2*M, card_h, 3, LGRAY, stroke_color=MGRAY)
    draw_pill(c, M + 3*mm, cur_y - 7*mm, 38*mm, 5.5*mm, RED, 'P1: Immediate Review', WHITE, 7.5)
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 9.5)
    c.drawString(M + 44*mm, cur_y - 5.5*mm, 'Phatthanakan Khu Khwang Road')
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(RED)
    c.drawRightString(W - M - 3*mm, cur_y - 5.5*mm, 'SSS: 40')

    bar_y    = cur_y - 13*mm
    bar_maxw = 55*mm
    bars = [
        ('T1', 39, colors.HexColor('#1F618D')),
        ('T2', 46, colors.HexColor('#117A65')),
        ('T3', 4,  colors.HexColor('#7B241C')),
    ]
    for j, (label, score, col) in enumerate(bars):
        bx = M + 3*mm
        brow_y = bar_y - j * 4.5*mm
        c.setFillColor(DGRAY)
        c.setFont('Helvetica', 7)
        c.drawString(bx, brow_y, label)
        c.setFillColor(MGRAY)
        c.roundRect(bx + 8*mm, brow_y, bar_maxw, 3*mm, 1.5, fill=1, stroke=0)
        c.setFillColor(col)
        fill_w = max(2*mm, bar_maxw * score / 100)
        c.roundRect(bx + 8*mm, brow_y, fill_w, 3*mm, 1.5, fill=1, stroke=0)
        c.setFillColor(SLATE)
        c.setFont('Helvetica-Bold', 7)
        c.drawString(bx + 8*mm + bar_maxw + 2*mm, brow_y, str(score))

    ex_text = (
        'Traffic moves at 102 km/h (V85) on a road posted at 80 km/h (SCR 1.28). '
        'Road environment implies a safe speed of 40-60 km/h, below the posted limit. '
        'Posted limit of 80 km/h exceeds the Safe System VRU threshold of 30 km/h '
        'given high estimated pedestrian exposure.'
    )
    ex_style = ParagraphStyle('ex', fontName='Helvetica', fontSize=7,
                              textColor=DGRAY, leading=10, alignment=TA_JUSTIFY)
    para(c, ex_text, M + 3*mm, cur_y - 16*mm, W - 2*M - 6*mm, ex_style)
    cur_y -= card_h + 5*mm

    h = para(c, 'What transport officials can do with these results',
             M, cur_y, W - 2*M, head_style)
    cur_y -= h + 3*mm

    actions = [
        ('P1 corridors', 'Commission a road safety audit on the flagged segments. '
         'The score decomposition identifies whether the priority is a limit revision, '
         'an infrastructure intervention, or both.'),
        ('P2 corridors', 'Include in the next scheduled speed limit review cycle. '
         'Monitor V85 data on these segments in the interim.'),
        ('T3-driven flags', 'Segments where T3 is the primary driver indicate that '
         'the posted limit exceeds Safe System thresholds for vulnerable users. '
         'Consider area-wide 30 km/h zones near schools and markets.'),
        ('T1-driven flags', 'Segments where T1 is the primary driver have a speed '
         'behavior problem. The road design may be inviting speeds above the limit. '
         'Engineering measures alongside limit revision.'),
    ]

    col_w = (W - 2*M - 4*mm) / 2
    for k, (title, desc) in enumerate(actions):
        col = k % 2
        row = k // 2
        ax = M + col * (col_w + 4*mm)
        action_h = 11*mm
        ay = cur_y - row * (action_h + 2*mm) - action_h
        draw_rounded_rect(c, ax, ay, col_w, action_h, 2, LGRAY, MGRAY)
        at_style = ParagraphStyle('at', fontName='Helvetica-Bold', fontSize=7.5,
                                  textColor=NAVY, leading=10)
        para(c, title, ax + 3*mm, ay + action_h - 2.5*mm, col_w - 6*mm, at_style)
        ad_style = ParagraphStyle('ad', fontName='Helvetica', fontSize=7,
                                  textColor=SLATE, leading=10, alignment=TA_JUSTIFY)
        para(c, desc, ax + 3*mm, ay + action_h - 7*mm, col_w - 6*mm, ad_style)

    cur_y -= 2 * (11*mm + 2*mm) + 5*mm

    c.setFillColor(NAVY)
    c.rect(0, 0, W, 10*mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#A9CCE3'))
    c.setFont('Helvetica', 7)
    c.drawString(M, 3.5*mm,
                 'TRACE - Tiered Road Alignment and Composite Evaluation  |  '
                 'AI for Safer Roads Innovation Challenge  |  ADB 2026')
    c.drawRightString(W - M, 3.5*mm,
                      'Safe System thresholds: WHO/ITF Road Safety Guidelines')

    c.save()
    size = os.path.getsize(OUTPUT) / 1024
    print(f"PDF saved: {OUTPUT} ({size:.0f} KB)")


if __name__ == '__main__':
    build()
