# claude-config

Mes configs Claude Code : mémoires globales et skills maison.

## Skills

| Skill | Usage |
|---|---|
| [`skills/best-of-recut`](skills/best-of-recut/SKILL.md) | Recut d'une vidéo YouTube longue en **un** short vertical best-of (HyperFrames, coupes ffmpeg en fin de phrase avec fondus). |
| [`skills/social-media-carousel`](skills/social-media-carousel/SKILL.md) | Carrousels Instagram / LinkedIn (PDF) / TikTok : accroche, plan, une idée par slide, CTA, légende, puis rendu PNG + PDF via Chrome headless (aucune dépendance npm). |

Installation d'un skill :

```bash
ln -s "$(pwd)/skills/best-of-recut" ~/.claude/skills/best-of-recut
ln -s "$(pwd)/skills/social-media-carousel" ~/.claude/skills/social-media-carousel
```

## Mémoires

`memory/` — fichiers de feedback / préférences à copier dans `~/.claude/projects/<projet>/memory/`.
