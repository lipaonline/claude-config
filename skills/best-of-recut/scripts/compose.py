#!/usr/bin/env python3
"""Build a HyperFrames best-of composition from a storyboard JSON + the reference template.

usage: compose.py storyboard.json build/<name>/index.html

Storyboard shape (all times in SOURCE seconds; the script converts to timeline seconds):
{
  "side_label": "BRAND · TOPIC · RECUT BY MARTY",
  "t0":   {"ghost": "TAKE 1", "slate": "BRAND · YOUTUBE", "l1": "LINE ONE", "l2": "LINE TWO."},
  "kickers": [{"ghost": "…", "l1": "…", "l2": "…"}, …],          # len(clips) - 1 entries
  "outro": {"handle": "@handle", "credits": "recut by Marty · brand"},
  "clips": [
    {"file": "clipA.mp4", "src_start": 0.06, "duration": 22.8,     # src_start = where the cut file begins, in source time
     "ghost": "…", "slate": "SCÈNE 01 · …", "tag": "…",
     "quote_l1": "…", "quote_l2": "…", "quote_at": 14.08,        # source time when the pull-quote appears
     "cues": [{"start": 0.21, "end": 2.01, "text": "…"}, …]}      # source times, one per caption line
  ]
}
Timeline: title 1.4 s → clip → kicker 1.2 s → clip … → outro 3.0 s.
"""
import json
import os
import re
import sys

T0, KICK, OUTRO = 1.4, 1.2, 3.0
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "composition-template.html")
LETTERS = "ABC"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def js(s):
    return json.dumps(s, ensure_ascii=False)


def main():
    sb = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]
    clips = sb["clips"]
    assert 2 <= len(clips) <= 3, "2 or 3 clips supported"
    assert len(sb["kickers"]) == len(clips) - 1, "need len(clips)-1 kickers"

    # ---- timeline ----
    t = T0
    for i, c in enumerate(clips):
        c["start"] = round(t, 3)
        c["offset"] = round(c["start"] - c["src_start"], 3)
        t += c["duration"]
        if i < len(clips) - 1:
            sb["kickers"][i]["start"] = round(t, 3)
            t += KICK
    outro_start = round(t, 3)
    total = round(t + OUTRO, 2)

    html = open(TEMPLATE, encoding="utf-8").read()
    r = {
        "__TOTAL__": str(total),
        "__GLOW_REPEAT__": str(max(1, int(total / 2.5))),
        "__DOT_REPEAT__": str(max(1, int(total / 0.75))),
        "__SIDE_LABEL__": esc(sb["side_label"]),
        "__T0_GHOST__": esc(sb["t0"]["ghost"]), "__T0_SLATE__": esc(sb["t0"]["slate"]),
        "__T0_L1__": esc(sb["t0"]["l1"]), "__T0_L2__": esc(sb["t0"]["l2"]),
        "__O_START__": str(outro_start),
        "__O_HANDLE__": esc(sb["outro"]["handle"]), "__O_CREDITS__": esc(sb["outro"]["credits"]),
    }
    for i, k in enumerate(sb["kickers"], 1):
        r[f"__K{i}_START__"] = str(k["start"])
        r[f"__K{i}_GHOST__"] = esc(k["ghost"]); r[f"__K{i}_L1__"] = esc(k["l1"]); r[f"__K{i}_L2__"] = esc(k["l2"])
    for L, c in zip(LETTERS, clips):
        r[f"__{L}_START__"] = str(c["start"]); r[f"__{L}_DUR__"] = str(round(c["duration"], 3))
        r[f"__{L}_GHOST__"] = esc(c["ghost"]); r[f"__{L}_SLATE__"] = esc(c["slate"]); r[f"__{L}_TAG__"] = esc(c["tag"])
        r[f"__{L}_QUOTE_L1__"] = esc(c["quote_l1"]); r[f"__{L}_QUOTE_L2__"] = esc(c["quote_l2"])
        html = html.replace(f'src="clip{L}.mp4"', f'src="{c["file"]}"')
    for k, v in r.items():
        html = html.replace(k, v)

    # clip A start is hard-coded to 1.4 in the template (data-start="1.4") — fine, T0 == 1.4.

    # ---- drop the third clip when only two ----
    if len(clips) == 2:
        for pat in [r'\s*<!-- K2 · kicker -->.*?</div>\s*</div>\s*</div>', r'\s*<div id="decoC".*?</div>\s*</div>',
                    r'\s*<video id="vC".*?</video>', r'\s*<audio id="aC".*?</audio>']:
            html = re.sub(pat, "", html, flags=re.S)

    # ---- cues ----
    cue_lines = []
    for c in clips:
        for q in c["cues"]:
            cue_lines.append(f'        {{ t: {round(q["start"] + c["offset"], 2)}, end: {round(q["end"] + c["offset"], 2)}, text: {js(q["text"])} }},')
    html = html.replace("        // __CUES__", "\n".join(cue_lines))

    # ---- rebuild the absolute-time GSAP section (kickers → outro) ----
    lines = ["      // ---- kickers: percussive stamps, hard cuts ----"]
    for i, k in enumerate(sb["kickers"], 1):
        s = k["start"]
        lines.append(f'      tl.fromTo("#k{i}-l1", {{ x: -90, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.3, ease: "expo.out" }}, {s + 0.05:.2f});')
        lines.append(f'      tl.fromTo("#k{i}-l2", {{ scale: 1.35, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.32, ease: "power4.out" }}, {s + 0.25:.2f});')
    lines.append("\n      // ---- video entrances ----")
    for L, c in zip(LETTERS, clips):
        lines.append(f'      tl.fromTo("#v{L}", {{ scale: 0.96, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "power2.out" }}, {c["start"]:.2f});')
    lines.append("\n      // ---- per-clip deco entrances ----")
    for L, c in zip(LETTERS, clips):
        s = c["start"]; qa = round(c["quote_at"] + c["offset"], 2)
        lines.append(f'      tl.fromTo("#deco{L} .slate", {{ scale: 1.7, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "power4.out" }}, {s + 0.15:.2f});')
        lines.append(f'      tl.fromTo("#tag{L}", {{ x: -40, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.4, ease: "power3.out" }}, {s + 0.4:.2f});')
        lines.append(f'      tl.fromTo("#word{L}", {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.5, ease: "expo.out" }}, {qa:.2f});')
    o = outro_start
    lines += ["\n      // ---- outro ----",
        f'      tl.fromTo("#o-slate", {{ scale: 1.7, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "power4.out" }}, {o + 0.1:.2f});',
        f'      tl.fromTo("#o-l1", {{ x: -80, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.45, ease: "expo.out" }}, {o + 0.25:.2f});',
        f'      tl.fromTo("#o-l2", {{ x: 80, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.45, ease: "power3.out" }}, {o + 0.45:.2f});',
        f'      tl.fromTo("#o-chip", {{ y: 60, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.5, ease: "back.out(1.6)" }}, {o + 0.8:.2f});',
        f'      tl.fromTo("#o-credits", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.45, ease: "power1.out" }}, {o + 1.2:.2f});',
        "      // final fade",
        f'      tl.to("#outro-content", {{ opacity: 0, duration: 0.5, ease: "power1.in" }}, {total - 0.6:.2f});',
        f'      tl.to("#bg", {{ opacity: 0, duration: 0.4, ease: "power1.in" }}, {total - 0.5:.2f});']
    html = re.sub(r"      // ---- kickers: percussive stamps, hard cuts ----.*?tl\.to\(\"#bg\".*?\);\n", "\n".join(lines) + "\n", html, flags=re.S)

    left = re.findall(r"__[A-Z0-9_]+__", html)
    assert not left, f"unfilled placeholders: {sorted(set(left))}"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    open(out, "w", encoding="utf-8").write(html)
    print(f"{out}: total {total}s | " + " | ".join(f"{L} {c['start']}+{round(c['duration'],2)}" for L, c in zip(LETTERS, clips)) + f" | outro {outro_start}")


if __name__ == "__main__":
    main()
