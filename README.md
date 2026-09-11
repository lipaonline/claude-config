# claude-config

Mes configs Claude Code : mémoires globales et skills maison.

## Skills

| Skill | Usage |
|---|---|
| [`skills/best-of-recut`](skills/best-of-recut/SKILL.md) | Recut d'une vidéo YouTube longue en **un** short vertical best-of (HyperFrames, coupes ffmpeg en fin de phrase avec fondus). |

Installation d'un skill :

```bash
ln -s "$(pwd)/skills/best-of-recut" ~/.claude/skills/best-of-recut
```

## Mémoires

`memory/` — fichiers de feedback / préférences à copier dans `~/.claude/projects/<projet>/memory/`.
