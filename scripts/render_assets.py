#!/usr/bin/env python3
"""STARBLOOD.OS generated telemetry panels. Standard library; offline-friendly.

Input format: data/stats.json produced by collect_stats.py. Demo fixtures may be
used for local preview only and are explicitly watermarked.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
import html
import json
from pathlib import Path
import random
import xml.etree.ElementTree as ET

BG = "#0c1412"
CARD = "#14211b"
CARD2 = "#182a20"
BORDER = "#345341"
TEXT = "#d9ebd9"
MUTED = "#91ad96"
ACCENT = "#a9d7a9"
GREEN = "#699e76"
YELLOW = "#f6de91"
BLUE = "#7195b6"
ORANGE = "#e6a15c"
HEAT = ["#1b2c23", "#345741", "#50795a", "#78a67c", "#b1dba9"]
LANG_COLORS = {"Python":"#f0d488", "TypeScript":"#7195b6", "JavaScript":"#d1bf76", "GDScript":"#8eb7c5", "Rust":"#d9a47c", "HTML":"#d58668", "CSS":"#9f96c7", "PowerShell":"#90bcdd", "Go":"#7ac0b3"}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def svg_start(width: int, height: int, title: str, description: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" style="white-space:pre" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(description)}">',
        f'<title>{esc(title)}</title><desc>{esc(description)}</desc>',
        f'<rect width="{width}" height="{height}" rx="16" fill="{BG}"/>',
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="15" fill="none" stroke="{BORDER}" stroke-width="2"/>',
        '<g font-family="Consolas, Menlo, DejaVu Sans Mono, monospace">',
    ]


def svg_end(lines: list[str]) -> str:
    return "\n".join([*lines, "</g>", "</svg>", ""])


def txt(x: int | float, y: int | float, value: object, *, size: int = 16, color: str = TEXT,
        weight: int = 400, anchor: str = "start", opacity: float = 1.0, spacing: float | None = None) -> str:
    extras = f' letter-spacing="{spacing}"' if spacing is not None else ""
    return f'<text style="white-space:pre" x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}" opacity="{opacity}"{extras}>{esc(value)}</text>'


def rect(x: int | float, y: int | float, w: int | float, h: int | float, fill: str,
         rx: int = 0, stroke: str | None = None, sw: int = 1) -> str:
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<rect x="{x}" y="{y}" width="{max(0,w)}" height="{max(0,h)}" rx="{rx}" fill="{fill}"{s}/>'


def line(x1: int, y1: int, x2: int, y2: int, color: str = BORDER, width: int = 1) -> str:
    return f'<path d="M{x1} {y1} H{x2}" stroke="{color}" stroke-width="{width}"/>' if y1 == y2 else f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>'


def status_label(stats: dict) -> str:
    return {"pending": "AWAITING FIRST API RUN", "demo": "DEMO DATA  /  NOT LIVE", "live": "GITHUB GRAPHQL  /  LIVE SNAPSHOT"}.get(stats.get("status"), "UNKNOWN DATA")


def display_value(stats: dict, key: str) -> str:
    val = stats.get(key)
    return f"{val:,}" if isinstance(val, int) and not isinstance(val, bool) else "—"


def render_stats(stats: dict) -> str:
    lines = svg_start(1040, 252, "Profile snapshot", "Public owned repositories, stars, annual contributions and forks")
    lines += [rect(24,23,7,16,ACCENT,1),txt(44,37,"PROFILE / METRICS",size=17,weight=700,color=ACCENT,spacing=1.6),
              txt(1014,37,status_label(stats),size=12,color=YELLOW if stats.get("status")!="live" else MUTED,anchor="end"),
              line(24,53,1016,53)]
    cards = [
        ("PUBLIC REPOS", "public_repositories", ACCENT, "owned / visible"),
        ("STARS RECEIVED", "total_stars", YELLOW, "on owned repos"),
        ("CONTRIBUTIONS", "year_contributions", BLUE, "last 12 months"),
        ("FORKS", "total_forks", ORANGE, "of owned repos"),
    ]
    for i,(label,key,color,hint) in enumerate(cards):
        x = 24 + i*253
        lines += [rect(x,72,235,148,CARD2,8,BORDER),rect(x+16,88,5,22,color,1),
                  txt(x+30,103,label,size=12,color=MUTED,weight=700,spacing=0.3),
                  txt(x+18,160,display_value(stats,key),size=38,color=TEXT,weight=700),
                  txt(x+18,195,hint,size=13,color=MUTED)]
    lines += [txt(24,238,"$ profile --metrics",size=12,color=GREEN),txt(1015,238,"Starblood24  //  STARBLOOD.OS",size=12,color=MUTED,anchor="end")]
    return svg_end(lines)


def render_languages(stats: dict) -> str:
    lines=svg_start(1040,272,"Language footprint","Top GitHub languages weighted by bytes of public owned non-fork, non-archived repositories")
    lines += [rect(24,23,7,16,BLUE,1),txt(44,37,"CODE / LANGUAGES",size=17,weight=700,color=ACCENT,spacing=1.6),
              txt(1014,37,"BY REPORTED SOURCE BYTES",size=12,color=MUTED,anchor="end"),line(24,53,1016,53)]
    langs = stats.get("languages") or []
    if not langs:
        message = "NO ELIGIBLE LANGUAGE DATA" if stats.get("status") == "live" else "LANGUAGE DISTRIBUTION PENDING"
        lines += [txt(520,131,message,size=19,color=ACCENT,anchor="middle",weight=700),
                  txt(520,166,"Public non-fork, non-archived repositories only.",size=13,color=MUTED,anchor="middle")]
    else:
        top = langs[:5]
        total = sum(max(0,int(x.get("bytes",0))) for x in langs)
        for i,entry in enumerate(top):
            y=80+i*34
            label=str(entry.get("name","Unknown"))[:20]
            share=100*max(0,int(entry.get("bytes",0)))/total if total else 0
            color=LANG_COLORS.get(label,[GREEN,ACCENT,ORANGE][i%3])
            lines += [txt(29,y+16,label,size=15,color=TEXT),rect(246,y,668,20,"#20352a",4),
                      rect(246,y,max(0,668*share/100),20,color,4),txt(1010,y+16,f"{share:.1f}%",size=14,color=MUTED,anchor="end")]
    lines += [line(24,240,1016,240),txt(24,260,"Languages reflect repository size, not proficiency.",size=12,color=MUTED),
              txt(1015,260,status_label(stats),size=12,color=YELLOW if stats.get("status")!="live" else MUTED,anchor="end")]
    return svg_end(lines)


def days_for_preview(stats: dict) -> list[dict]:
    if stats.get("status") != "demo" or stats.get("days"):
        return stats.get("days") or []
    # Never used for real output; deterministic decorative demonstration only.
    r=random.Random(26)
    end=date(2026,11,4)
    result=[]
    for i in range(371):
        day=end-timedelta(days=370-i)
        chance=r.random()
        count=0 if chance<.30 else (1 if chance<.51 else (2 if chance<.69 else (4 if chance<.86 else 7)))
        result.append({"date":day.isoformat(),"count":count})
    return result


def render_contributions(stats: dict) -> str:
    lines=svg_start(1040,270,"Contribution activity","Sunday-to-Saturday GitHub contribution calendar for the last year")
    lines += [rect(24,23,7,16,GREEN,1),txt(44,37,"CONTRIBUTION / ACTIVITY",size=17,weight=700,color=ACCENT,spacing=1.2),
              txt(1014,37,status_label(stats),size=12,color=YELLOW if stats.get("status")!="live" else MUTED,anchor="end"),line(24,53,1016,53)]
    days=days_for_preview(stats)
    x0=54; top=100; step=16; cell=12
    lookup={d["date"]:int(d["count"]) for d in days if isinstance(d.get("count"),int) and isinstance(d.get("date"),str)}
    if days:
        last=date.fromisoformat(days[-1]["date"])
        last_sunday=last-timedelta(days=(last.weekday()+1)%7)
        first_sunday=last_sunday-timedelta(weeks=52)
    else:
        first_sunday=date(2026,1,4) # layout-only anchor; no real dates displayed
    for week in range(53):
        for weekday in range(7):
            day=first_sunday+timedelta(days=week*7+weekday)
            v=lookup.get(day.isoformat(),0)
            level=0 if v==0 else (1 if v==1 else (2 if v<=3 else (3 if v<=6 else 4)))
            fill = HEAT[level] if not days or day.isoformat() in lookup else "none"
            lines.append(rect(x0+week*17,top+weekday*16,cell,cell,fill,2))
        if days:
            day=first_sunday+timedelta(days=week*7)
            if day.day<=7 and day+timedelta(days=7)>day.replace(day=1):
                lines.append(txt(x0+week*17,86,day.strftime("%b").upper(),size=11,color=MUTED))
    lines += [txt(24,112,"SUN",size=11,color=MUTED),txt(24,160,"WED",size=11,color=MUTED),
              txt(24,208,"SAT",size=11,color=MUTED)]
    if stats.get("status") == "pending":
        lines += [rect(279,126,482,58,BG,7,BORDER),txt(520,151,"AWAITING FIRST LIVE UPDATE",size=17,color=ACCENT,anchor="middle",weight=700),
                  txt(520,171,"No contributions invented for published assets",size=11,color=MUTED,anchor="middle")]
    lines += [line(24,233,1016,233),txt(24,253,"$ contributions --calendar",size=12,color=GREEN),
              txt(800,253,"less",size=11,color=MUTED)]
    for i,c in enumerate(HEAT):
        lines.append(rect(839+i*21,242,15,13,c,2))
    lines.append(txt(968,253,"more",size=11,color=MUTED))
    return svg_end(lines)



def render_stats_mobile(stats: dict) -> str:
    lines=svg_start(640,352,"Profile snapshot mobile","Mobile-optimized public repositories, received stars, contributions, and forks")
    lines += [rect(18,20,7,16,ACCENT,1),txt(38,34,"PROFILE / METRICS",size=17,color=ACCENT,weight=700),
              txt(619,34,"GITHUB",size=12,color=MUTED,anchor="end"),line(18,52,622,52)]
    cards=[("PUBLIC REPOS","public_repositories",ACCENT),("STARS RECEIVED","total_stars",YELLOW),
           ("CONTRIBUTIONS","year_contributions",BLUE),("FORKS","total_forks",ORANGE)]
    for i,(label,key,color) in enumerate(cards):
        x=18+(i%2)*311; y=68+(i//2)*127
        lines += [rect(x,y,293,111,CARD2,8,BORDER),rect(x+13,y+15,5,19,color,1),
                  txt(x+28,y+30,label,size=13,color=MUTED,weight=700),
                  txt(x+18,y+85,display_value(stats,key),size=38,color=TEXT,weight=700)]
    lines += [line(18,321,622,321),txt(18,341,status_label(stats),size=12,color=YELLOW if stats.get("status")!="live" else MUTED)]
    return svg_end(lines)


def render_contributions_mobile(stats: dict) -> str:
    lines=svg_start(640,244,"Contributions mobile","Mobile-optimized GitHub annual contribution calendar")
    lines += [rect(18,20,7,16,GREEN,1),txt(38,34,"CONTRIBUTION / ACTIVITY",size=16,color=ACCENT,weight=700),
              line(18,52,622,52)]
    days=days_for_preview(stats)
    lookup={d["date"]:int(d["count"]) for d in days if isinstance(d.get("count"),int) and isinstance(d.get("date"),str)}
    if days:
        last=date.fromisoformat(days[-1]["date"])
        first=last-timedelta(days=(last.weekday()+1)%7)-timedelta(weeks=52)
    else:
        first=date(2026,1,4)
    for week in range(53):
        for weekday in range(7):
            v=lookup.get((first+timedelta(days=week*7+weekday)).isoformat(),0)
            idx=0 if v==0 else (1 if v==1 else (2 if v<=3 else (3 if v<=6 else 4)))
            day_date = (first+timedelta(days=week*7+weekday)).isoformat()
            fill = HEAT[idx] if not days or day_date in lookup else "none"
            lines.append(rect(28+week*11,86+weekday*13,8,9,fill,1))
        if days:
            d=first+timedelta(days=week*7)
            if d.day<=7:
                lines.append(txt(28+week*11,76,d.strftime("%b").upper(),size=9,color=MUTED))
    if stats.get("status")=="pending":
        lines += [rect(149,109,360,48,BG,5,BORDER),txt(329,137,"AWAITING FIRST LIVE UPDATE",size=13,color=ACCENT,anchor="middle",weight=700)]
    lines += [line(18,192,622,192),txt(18,217,status_label(stats),size=11,color=YELLOW if stats.get("status")!="live" else MUTED),
              txt(18,233,"less",size=10,color=MUTED)]
    for i,col in enumerate(HEAT):
        lines.append(rect(57+i*16,222,12,10,col,1))
    lines.append(txt(151,233,"more",size=10,color=MUTED))
    return svg_end(lines)


def render_languages_mobile(stats: dict) -> str:
    lines=svg_start(640,300,"Languages mobile","Mobile-optimized language proportions by public repository source bytes")
    lines += [rect(18,20,7,16,BLUE,1),txt(38,34,"CODE / LANGUAGES",size=17,color=ACCENT,weight=700),line(18,52,622,52)]
    langs=stats.get("languages") or []
    if not langs:
        message = "NO ELIGIBLE LANGUAGE DATA" if stats.get("status") == "live" else "LANGUAGES PENDING"
        lines += [txt(320,134,message,size=19,color=ACCENT,anchor="middle"),
                  txt(320,162,"Public non-fork, non-archived repos only",size=13,color=MUTED,anchor="middle")]
    else:
        top=langs[:5];total=sum(max(0,int(x.get("bytes",0))) for x in langs)
        for i,entry in enumerate(top):
            y=74+i*33;name=str(entry.get("name","Unknown"))[:16]
            pct=100*max(0,int(entry.get("bytes",0)))/total if total else 0
            color=LANG_COLORS.get(name,[GREEN,ACCENT,ORANGE][i%3])
            lines += [txt(18,y+16,name,size=14,color=TEXT),rect(177,y,366,20,"#20352a",3),
                      rect(177,y,366*pct/100,20,color,3),txt(621,y+16,f"{pct:.1f}%",size=13,color=MUTED,anchor="end")]
    lines += [line(18,248,622,248),txt(18,267,"Public source sizes · not skill proficiency",size=12,color=MUTED)]
    lines.append(txt(18,287,status_label(stats),size=11,color=YELLOW if stats.get("status")!="live" else MUTED))
    return svg_end(lines)


def validate_stats(stats: dict) -> None:
    if not isinstance(stats, dict) or type(stats.get("schema_version")) is not int or stats["schema_version"] != 1:
        raise ValueError("Unsupported statistics schema")
    status = stats.get("status")
    if status not in ("pending", "demo", "live"):
        raise ValueError("Invalid statistics status")
    for key in ("public_repositories", "total_stars", "total_forks", "year_contributions"):
        value = stats.get(key)
        if (status == "pending" and value is not None) or (status != "pending" and (type(value) is not int or value < 0)):
            raise ValueError(f"Invalid statistic: {key}")
    if not isinstance(stats.get("days"), list) or not isinstance(stats.get("languages"), list):
        raise ValueError("Days and languages must be lists")
    previous = ""
    for day in stats["days"]:
        if not isinstance(day, dict) or not isinstance(day.get("date"), str) or type(day.get("count")) is not int or day["count"] < 0:
            raise ValueError("Invalid contribution day")
        day_date = day["date"]
        if date.fromisoformat(day_date).isoformat() != day_date or day_date <= previous:
            raise ValueError("Contribution dates must be unique and sorted ISO dates")
        previous = day_date
    if status == "live" and not stats["days"]:
        raise ValueError("Live contribution calendar is empty")
    if status == "pending" and (stats["days"] or stats["languages"]):
        raise ValueError("Pending statistics must not contain fabricated data")
    for language in stats["languages"]:
        if not isinstance(language, dict) or not isinstance(language.get("name"), str) or not language["name"] or type(language.get("bytes")) is not int or language["bytes"] <= 0:
            raise ValueError("Invalid language data")


def render_into(stats: dict, folder: Path) -> None:
    validate_stats(stats)
    folder.mkdir(parents=True,exist_ok=True)
    rendered={
        "stats.svg":render_stats(stats),
        "contributions.svg":render_contributions(stats),
        "languages.svg":render_languages(stats),
        "stats_mobile.svg":render_stats_mobile(stats),
        "contributions_mobile.svg":render_contributions_mobile(stats),
        "languages_mobile.svg":render_languages_mobile(stats),
    }
    for svg in rendered.values():
        ET.fromstring(svg)
    for filename, svg in rendered.items():
        target=folder/filename
        tmp=folder/(filename+".tmp")
        tmp.write_text(svg,encoding="utf-8")
        tmp.replace(target)


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",type=Path,default=Path("data/stats.json"))
    ap.add_argument("--out",type=Path,default=Path("assets"))
    args=ap.parse_args()
    stats=json.loads(args.data.read_text(encoding="utf-8"))
    render_into(stats,args.out)
    print("SVG panels generated:", ", ".join(("stats.svg", "contributions.svg", "languages.svg", "stats_mobile.svg", "contributions_mobile.svg", "languages_mobile.svg")))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
