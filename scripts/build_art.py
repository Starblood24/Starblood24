#!/usr/bin/env python3
"""Build static STARBLOOD.OS art from the user's actual avatar. Requires Pillow.

Uses colored monospace glyphs, not an embedded raster inside the SVG.
This builder only runs locally; the daily workflow needs no Pillow.
"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path

from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/"source/avatar_reference.jpg"
OUTPUT=ROOT/"assets"
THEME=json.loads((ROOT/"config/theme.json").read_text(encoding="utf-8"))

BG=THEME["background"]; TEXT=THEME["text"]; MUTED=THEME["muted"]
ACC=THEME["accent"]; BORDER=THEME["border"]
YELLOW=THEME["yellow"]; BLUE=THEME["blue"]; ORANGE=THEME["orange"]
FONT="Consolas, Menlo, DejaVu Sans Mono, monospace"


def t(x,y,message,size=16,color=TEXT,weight=400,anchor="start",letter_spacing=None):
    ls = f' letter-spacing="{letter_spacing}"' if letter_spacing is not None else ""
    return (f'<text style="white-space:pre" x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{ls}>'
            f'{escape(str(message))}</text>')


def r(x,y,w,h,fill,rx=0,stroke=None,sw=1):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"'
            + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else "")+'/>')


def lin(x1,y1,x2,y2,color=BORDER,sw=1):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"/>'


def wrap(width,height,body,title,description):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" style="white-space:pre" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="{escape(description)}">\n<title>{escape(title)}</title><desc>{escape(description)}</desc>\n'
            + '\n'.join(body) + '\n</svg>\n')


def quantize_color(rgb):
    red,green,blue=rgb
    maximum=max(rgb); minimum=min(rgb); sat=maximum-minimum
    lum=.299*red+.587*green+.114*blue
    if minimum>242 or (lum>241 and sat<18):
        return None, None
    if lum<111:
        return "#52443b", "█" # pencil outlines from the original portrait
    if red>140 and red>green*1.09 and (red>blue*1.25 or green<145):
        if red>205 and green>130:
            return ORANGE,"▓"
        return "#a7775d", "▓"
    if blue>red*1.04 and blue>=green*1.01 and 70<blue<240:
        return ("#7294b2" if lum>130 else "#527695"), "▓"
    if red>185 and green>170 and blue<183 and red>blue*1.20:
        return ("#f6de91" if lum>175 else "#ebcc80"),"▓"
    if abs(red-green)<24 and abs(blue-green)<26:
        if lum<158:
            return "#8f9896","▒"
        if lum<238:
            return "#bdc5c0","░"
        return None,None
    if red>193 and green>172 and blue<192:
        return "#f6de91","▓"
    if lum>224:
        return None,None
    return ("#96a5a0" if lum>159 else "#71807b"),"▒"


def cells_for_avatar(cols=54, rows=40):
    image=Image.open(SOURCE).convert('RGB')
    image=image.resize((cols,rows),Image.Resampling.BOX)
    result=[]
    for j in range(rows):
        for i in range(cols):
            rgb=image.getpixel((i,j))
            color,ch=quantize_color(rgb)
            if color is None:
                continue
            result.append((i,j,ch,color))
    return result


def glyph_group(x,y,scale=1.0, cols=54, rows=40):
    # Monospace advances: 6.7 px horizontal, 9.3 px vertical.
    dx=6.80;dy=9.40
    glyphs=[f'<g transform="translate({x} {y}) scale({scale})" font-family="DejaVu Sans Mono, Consolas, monospace" font-size="10.3" font-weight="bold">']
    for i,j,ch,color in cells_for_avatar(cols,rows):
        glyphs.append(f'<text x="{i*dx:.2f}" y="{(j+1)*dy:.2f}" fill="{color}">{escape(ch)}</text>')
    glyphs.append('</g>')
    return '\n'.join(glyphs)


def build_avatar():
    body=[glyph_group(22,17,1.0),t(24,417,"POMPOMPURIN.SYS // COLOR ASCII",size=13,color=MUTED)]
    result=wrap(426,444,body,"Pompompurin ASCII avatar","Color Unicode character portrait of the user's GitHub avatar, Pompompurin in a blue suit and orange tie behind a laptop")
    (OUTPUT/"avatar_ascii.svg").write_text(result,encoding="utf-8")


def build_hero():
    body=[r(0,0,1120,430,BG,18),r(1,1,1118,428,"none",17,BORDER,2),
          r(0,0,1120,51,"#13231b",17),r(1,37,1118,16,"#13231b"),
          lin(1,52,1119,52),r(27,23,9,9,ACC,5),r(45,23,9,9,ORANGE,5),r(63,23,9,9,"#a97864",5),
          t(88,33,"~/Starblood24 / profile",14,color=MUTED),t(1084,33,"[ ONLINE ]",14,color=ACC,anchor="end"),
          t(43,115,"WELCOME TO",15,color=ACC,weight=700,letter_spacing=3),
          t(39,175,"STARBLOOD.OS",59,color=TEXT,weight=700,letter_spacing=-2.2),
          r(43,198,61,5,ACC,0),r(108,198,34,5,YELLOW,0),r(146,198,18,5,BLUE,0),
          t(43,244,"> whoami",18,color=ACC),
          t(43,278,"Hamza Emir Ünal",23,color=TEXT,weight=700),
          t(43,308,"Computer Science · Creative Developer",17,color=MUTED),
          t(43,336,"Game Dev / Cybersecurity / UX-minded Tools",16,color=MUTED),
          r(43,361,139,39,"#1b3526",7,BORDER),t(112,387,"[ PYTHON ]",14,color=ACC,anchor="middle",weight=700),
          r(193,361,137,39,"#243325",7,BORDER),t(261,387,"[ GODOT ]",14,color=YELLOW,anchor="middle",weight=700),
          r(342,361,167,39,"#1d2e37",7,BORDER),t(425,387,"[ SECURITY ]",14,color="#a7c8dd",anchor="middle",weight=700),
          r(690,70,390,321,"#14221b",12,BORDER,1),r(712,88,12,12,"#a9d7a9",2),
          t(738,99,"pompompurin.sys",14,color=ACC,weight=700),
          t(1062,99,":: ASCII",12,color=MUTED,anchor="end"),
          lin(709,113,1062,113,"#294638"),
          glyph_group(765,115,0.64),
          t(892,383,"soft pixels / hard problems",10,color=MUTED,anchor="middle")]
    (OUTPUT/"hero.svg").write_text(wrap(1120,430,body,"STARBLOOD.OS profile header","Custom terminal-themed GitHub profile header for Starblood24 with colored ASCII avatar of Pompompurin"),encoding="utf-8")


def build_featured():
    body=[r(0,0,1040,264,BG,16),r(1,1,1038,262,"none",15,BORDER,2),
          r(1,1,1038,46,"#13231b",15),r(1,33,1038,15,"#13231b"),lin(1,48,1039,48),
          r(22,20,9,9,ACC,5),r(39,20,9,9,ORANGE,5),r(56,20,9,9,BLUE,5),
          t(79,31,"~/projects/typr",14,color=MUTED),t(1009,31,"FEATURED / 01",13,color=ACC,anchor="end"),
          t(40,107,"typr",48,weight=700,color=TEXT),r(42,120,75,4,ACC),
          t(42,155,"A quiet, keyboard-first terminal typing utility.",19,color=MUTED),
          t(42,182,"Built with Python + Textual. Designed around thoughtful TUI interaction.",14,color=MUTED),
          t(42,220,"PYTHON",14,color=YELLOW,weight=700),t(140,220,"TEXTUAL",14,color=BLUE,weight=700),
          t(245,220,"TUI / UX",14,color=ACC,weight=700),
          r(671,70,324,166,"#172820",9,BORDER),
          t(691,96,"$ typr --classic  [sample]",13,color=ACC),
          t(691,124,"WPM       ACCURACY",12,color=MUTED),
          t(691,158,"  86         98%",23,color=TEXT,weight=700),
          t(692,189,"████████████░░░░░░",17,color=ACC),
          t(692,215,"esc pause",11,color=MUTED)]
    (OUTPUT/"featured_typr.svg").write_text(wrap(1040,264,body,"Featured: typr","Featured repository typr: a Python Textual keyboard-first typing tool, with a sample illustrative TUI only"),encoding="utf-8")


def build_stack():
    body=[r(0,0,1040,178,BG,16),r(1,1,1038,176,"none",15,BORDER,2),
          r(24,25,7,16,BLUE,1),t(44,39,"SYSTEM / TOOLBOX",17,color=ACC,weight=700,letter_spacing=1.5),
          t(1013,39,"TOOLS I BUILD WITH",12,color=MUTED,anchor="end"),lin(24,54,1015,54)]
    stack=[("PYTHON",YELLOW), ("TEXTUAL",BLUE),("TYPESCRIPT",BLUE),("JAVASCRIPT",YELLOW),("GODOT",ACC),("GIT",ORANGE),("POWERSHELL",BLUE)]
    x=24
    for i,(name,color) in enumerate(stack):
        w=130 if name=="TYPESCRIPT" else 126 if name=="POWERSHELL" else 116
        if name=="JAVASCRIPT": w=130
        body += [r(x,76,w,60,"#192b22",8,BORDER),r(x+12,94,6,24,color,2),t(x+25,112,name,13,color=TEXT,weight=700)]
        x += w+9
    body += [t(24,161,"$ ls ~/skills  --focus practical tools, accessible interfaces, and fun details",12,color=MUTED)]
    (OUTPUT/"stack.svg").write_text(wrap(1040,178,body,"Technology stack","Languages and tools: Python, Textual, TypeScript, JavaScript, Godot, Git and PowerShell"),encoding="utf-8")



def build_mobile_art():
    hero=[
        r(0,0,640,686,BG,15),r(1,1,638,684,"none",14,BORDER,2),
        r(1,1,638,48,"#13231b",14),r(1,35,638,14,"#13231b"),lin(1,49,639,49),
        r(20,20,8,8,ACC,4),r(36,20,8,8,ORANGE,4),r(52,20,8,8,BLUE,4),
        t(72,30,"~/Starblood24",14,color=MUTED),t(615,30,"ONLINE",12,color=ACC,anchor="end"),
        t(26,98,"WELCOME TO",14,color=ACC,weight=700,letter_spacing=2.5),
        t(22,159,"STARBLOOD.OS",48,color=TEXT,weight=700,letter_spacing=-2),
        r(26,175,66,4,ACC),r(97,175,27,4,YELLOW),r(129,175,18,4,BLUE),
        t(26,226,"> whoami",17,color=ACC),
        t(26,257,"Hamza Emir Ünal",21,color=TEXT,weight=700),
        t(26,285,"Computer Science · Creative Developer",14,color=MUTED),
        t(26,313,"Games / Security / UX-minded Tools",14,color=MUTED),
        r(21,335,599,323,"#14221b",12,BORDER),
        r(42,353,9,9,ACC,2),t(61,363,"pompompurin.sys",14,color=ACC,weight=700),
        t(595,363,"ASCII",12,color=MUTED,anchor="end"),lin(41,377,599,377),
        glyph_group(195,378,0.66),
        t(319,644,"soft pixels / hard problems",12,color=MUTED,anchor="middle")
    ]
    (OUTPUT/"hero_mobile.svg").write_text(wrap(640,686,hero,"STARBLOOD.OS mobile header","Mobile layout of Starblood developer header and Pompompurin color ASCII art"),encoding="utf-8")

    feat=[r(0,0,640,471,BG,15),r(1,1,638,469,"none",14,BORDER,2),
          r(1,1,638,46,"#13231b",14),r(1,34,638,13,"#13231b"),lin(1,48,639,48),
          r(19,19,8,8,ACC,4),r(34,19,8,8,ORANGE,4),r(49,19,8,8,BLUE,4),
          t(70,30,"~/projects/typr",14,color=MUTED),
          t(618,30,"FEATURED / 01",12,color=ACC,anchor="end"),
          t(27,108,"typr",49,weight=700),r(29,118,71,4,ACC),
          t(27,160,"A quiet, keyboard-first",20,color=MUTED),
          t(27,187,"terminal typing utility.",20,color=MUTED),
          t(27,218,"Python + Textual · Thoughtful TUI interactions",14,color=MUTED),
          t(29,254,"PYTHON",15,color=YELLOW,weight=700),t(138,254,"TEXTUAL",15,color=BLUE,weight=700),
          t(259,254,"TUI / UX",15,color=ACC,weight=700),
          r(26,286,588,157,"#172820",9,BORDER),
          t(47,312,"$ typr --classic  [sample]",15,color=ACC),
          t(47,338,"WPM         ACCURACY",12,color=MUTED),
          t(47,374,"86             98%",27,color=TEXT,weight=700),
          t(47,403,"████████████░░░░░░",18,color=ACC),
          t(47,425,"esc pause",11,color=MUTED)]
    (OUTPUT/"featured_typr_mobile.svg").write_text(wrap(640,471,feat,"typr mobile feature","Mobile-friendly featured typr project card"),encoding="utf-8")

    stack=[r(0,0,640,268,BG,15),r(1,1,638,266,"none",14,BORDER,2),
           r(21,22,7,16,BLUE,1),t(41,36,"SYSTEM / TOOLBOX",17,color=ACC,weight=700),lin(21,50,619,50)]
    labels=[("PYTHON",YELLOW),("TEXTUAL",BLUE),("TYPESCRIPT",BLUE),("JAVASCRIPT",YELLOW),
            ("GODOT",ACC),("GIT",ORANGE),("POWERSHELL",BLUE)]
    for i,(name,color) in enumerate(labels):
        # first row 4 panels, second row 3; give long name enough width
        row=i//4; col=i%4
        if row==0: x=18+col*155;w=145
        else: x=18+col*207;w=197
        y=72+row*86
        stack += [r(x,y,w,66,"#192b22",8,BORDER),r(x+11,y+20,6,23,color,2),
                  t(x+26,y+40,name,14,color=TEXT,weight=700)]
    stack += [t(20,245,"focus: useful tools & delightful interfaces",12,color=MUTED)]
    (OUTPUT/"stack_mobile.svg").write_text(wrap(640,268,stack,"Mobile technology toolbox","Mobile-friendly labels for developer technologies"),encoding="utf-8")


# Preserve the original rasterized glyphs; only the eye patches are animated.
# shortcut: eye boxes match this portrait, recalibrate if idle_base.png changes.
EYE_BOXES = ((214, 130, 230, 145), (305, 149, 321, 167))
BLINK_LEVELS = (0, .25, .5, .75, 1, .75, .5, .25, 0)
BLINK_DURATIONS = (2100, 30, 30, 30, 70, 40, 40, 40, 1620)


def blink_frame(base, closure):
    frame = base.copy()
    for x0, y0, x1, y1 in EYE_BOXES:
        eye = base.crop((x0, y0, x1, y1))
        # Nearby skin preserves the colored-glyph texture behind the eyelid.
        skin = base.crop((x0-21, y0, x1-21, y1))
        height = max(2, round(eye.height * (1-closure)))
        eye = eye.resize((eye.width, height), Image.Resampling.BOX)
        skin.paste(eye, (0, (skin.height-height)//2))
        frame.paste(skin, (x0, y0))
    return frame


def build_gif():
    with Image.open(ROOT/'source/idle_base.png') as image:
        base = image.convert('RGB')
    palette = base.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    frames = [blink_frame(base, level).quantize(palette=palette, dither=Image.Dither.NONE)
              for level in BLINK_LEVELS]
    frames[0].save(OUTPUT/'pompompurin_idle.gif', save_all=True,
                   append_images=frames[1:], loop=0, duration=BLINK_DURATIONS,
                   disposal=1, optimize=False)
    frames[0].convert('RGB').save(OUTPUT/'pompompurin_idle_poster.png', optimize=True)


def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    build_avatar()
    build_hero()
    build_featured()
    build_stack()
    build_mobile_art()
    build_gif()
    print("Built desktop/mobile hero, avatar, featured_typr, stack, and Pompompurin GIF + poster")


if __name__=="__main__":
    main()
