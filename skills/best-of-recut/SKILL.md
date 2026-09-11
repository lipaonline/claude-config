---
name: best-of-recut
description: Recut a long YouTube talking-head video into ONE vertical best-of short (9:16) — pick the 2-3 strongest moments, cut them cleanly at sentence ends with audio fades, and wrap them in a HyperFrames composition (title card → scenes with slate / pull-quote / captions → kickers → "FULL VIDEO ON YOUTUBE." end card). Trigger on "recut", "best-of", "fais un short de cette vidéo", "meilleurs moments", "compile les meilleurs passages". Not several separate shorts, not auto-clippers (Higgsfield / Opus Clip), not overlay-only packaging (→ talking-head-recut).
---

# Best-of Recut

Une vidéo YouTube longue (talking head, démo, interview) → **une seule vidéo verticale** qui
compile les 2-3 meilleurs moments, dans le style du short `jarvis` : chrome « plateau de
tournage » persistant, title card percutante, footage réel encadré avec slate + pull-quote +
captions mot à mot, kickers entre les scènes, end card « FULL VIDEO ON YOUTUBE. ».

**Ce que ce n'est pas :**
- pas plusieurs shorts séparés (l'utilisateur veut *une* vidéo best-of) ;
- pas un clipper automatique (Higgsfield Personal Clipper, Opus Clip…) ;
- pas un simple habillage d'une vidéo qui joue en entier → `talking-head-recut` ;
- pas des sous-titres seuls → `embedded-captions`.

## Prérequis

- `yt-dlp`, `ffmpeg` / `ffprobe`
- `npx hyperframes@0.7.64` (fixer la version dans `package.json`, voir `references/package.json`)
- macOS : `export PRODUCER_BROWSER_GPU_MODE=hardware` avant le rendu

## Arborescence du projet

```
<projet>/
  package.json              # scripts check / render / preview (version hyperframes figée)
  source/
    <slug>.mp4              # vidéo source (yt-dlp, 1080p max)
    <slug>.<lang>.json3     # piste de sous-titres YouTube au mot près
    <slug>.words.json       # sortie de scripts/json3_to_words.py
  build/<name>/
    index.html              # UNE composition racine par dossier
    clipA.mp4 clipB.mp4 …   # segments coupés (scripts/cut_clip.sh)
  renders/
    <name>.mp4
```

**Règle HyperFrames :** un seul `index.html` racine par dossier de build, sinon le lint
`multiple_root_compositions` échoue. Un short = un mini-projet `build/<name>/`.

## Workflow

### 1. Récupérer la source et la transcription au mot près

```bash
yt-dlp -f "bv*[height<=1080]+ba/b" --merge-output-format mp4 -o "source/<slug>.mp4" "<url>"
yt-dlp --skip-download --write-auto-subs --write-subs --sub-lang <lang> --sub-format json3 \
  -o "source/<slug>" "<url>"
```

Si YouTube renvoie `HTTP Error 429` sur les sous-titres, ajouter
`--extractor-args "youtube:player_client=android"` (ça débloque aussi la vidéo). Prendre la piste
`<lang>-orig` quand elle existe : `fr` seul peut être une traduction automatique.

Le json3 donne normalement un `tOffsetMs` par mot : c'est ce qui permet de couper proprement.
**Ne pas retranscrire avec Whisper** si ces timings au mot existent.

**Fallback si le json3 n'a pas de timings au mot** (segs sans `tOffsetMs`, blocs de ~3 s,
typiquement sur une vidéo dont l'auteur a uploadé sa propre piste) : choisir les moments sur les
blocs (le script sort quand même un listing horodaté exploitable), puis extraire l'audio des
seules zones candidates (±3 s) et les passer dans whisperx pour obtenir le mot à mot :

```bash
ffmpeg -y -ss <t0> -to <t1> -i source/<slug>.mp4 -vn -ac 1 -ar 16000 zoneA.wav
~/dev/1440o/scripts/clip-machine/.venv/bin/whisperx zoneA.wav --model large-v3-turbo \
  --language fr --device cpu --compute_type int8 --output_format json --output_dir .
```

Ajouter l'offset `t0` à chaque mot. 30 s d'audio prennent ~15 s sur CPU. Whisperx entend mal les
chiffres (« 15 000 € » → « 15 millions ») : reprendre le texte depuis la piste YouTube.

```bash
python3 <SKILL_DIR>/scripts/json3_to_words.py source/<slug>.<lang>.json3 > source/<slug>.words.json
```

Sortie : `{ "words": [{text,start,end}], "sentences": [{text,start,end}] }` — phrases
regroupées sur la ponctuation terminale et les pauses > 0,7 s.

### 2. Choisir les moments (dans le chat, pas de CLI)

Lire `sentences` et retenir **2 à 3 segments**, total footage 35-50 s. Critères, dans l'ordre :

1. **Hook** : la phrase qui pose le problème ou la promesse en une ligne (scène 01).
2. **Démonstration / solution** : le passage le plus concret, idéalement avec une image qui
   bouge ou un chiffre (scène 02).
3. **Récap / punchline** : la phrase qu'on garde en tête (scène 03, peut être omise).

Chaque segment doit **commencer au début d'une phrase et finir à la fin d'une phrase**.
Noter pour chaque segment : `src_start`, `src_end` (timings du json3), une slate
(`SCÈNE 01 · LE RÉFLEXE`), un tag court, une pull-quote de 2 lignes dont la 2e en accent.

### 3. Couper les segments avec fondus

```bash
bash <SKILL_DIR>/scripts/cut_clip.sh source/<slug>.mp4 <start> <end> build/<name>/clipA.mp4
```

Le script :
- ajoute **0,15 s avant le premier mot** et **0,35 s après le dernier** (`PAD_IN` / `PAD_OUT`) ;
- applique `afade in 0.15 s` et `afade out 0.30 s` (`FADE_IN` / `FADE_OUT`) ;
- ré-encode (libx264 crf 18, aac 192k) pour des coupes à l'image près ;
- imprime le niveau `volumedetect` des 300 premières et dernières millisecondes. **Cible :
  mean_volume ≤ −40 dB en queue.** Si c'est plus fort, un mot est coupé : reculer `end` sur la
  fin de phrase précédente ou augmenter `PAD_OUT`. La tête est masquée par le fade-in, elle
  peut être plus forte.

Orateur qui enchaîne sans pause (gap < 0,1 s entre la fin de phrase et le mot suivant) : scanner
l'énergie par tranches de 40 ms autour du point de coupe (`ffmpeg -ss t -t 0.04 -af volumedetect`)
pour trouver le vrai creux, puis couper dedans avec `PAD_OUT=0.05 FADE_OUT=0.10`. Contrôler alors
les **80 dernières ms** (≤ −45 dB) plutôt que les 300 dernières, qui contiennent la fin du mot.

Les coupes sèches en milieu de mot ont été explicitement rejetées par l'utilisateur.

### 4. Écrire la composition

Écrire `build/<name>/storyboard.json` (schéma en tête de `scripts/compose.py`, exemple complet
dans `references/storyboard-example.json`) puis générer :

```bash
python3 <SKILL_DIR>/scripts/compose.py build/<name>/storyboard.json build/<name>/index.html
```

Le générateur remplit `references/composition-template.html`, calcule la timeline (title 1.4 s →
clip → kicker 1.2 s → … → outro 3 s), convertit tous les timings source en timings composition
(`offset = clip_start − src_start`, où `src_start` est le début *du fichier coupé* dans la source,
donc `mot_start − PAD_IN`) et réécrit les entrées GSAP. 2 ou 3 clips.

Contraintes de texte (police 96-122 px, `nowrap` sur les captions) :
- pull-quote : **≤ 15 caractères par ligne**, sinon elle passe sur 3-4 lignes ;
- kickers / title card : ≤ 12 caractères par ligne ;
- captions : **≤ 45 caractères**, une phrase ou un bout de phrase par cue, texte fidèle à la parole ;
- `outro.handle` sans flèche, le template l'ajoute.

Timeline type (3 scènes) :

```
0.0   T0 title card        1.4 s
1.4   clip A + deco A      durée A
+     K1 kicker            1.2 s
+     clip B + deco B      durée B
+     K2 kicker            1.2 s
+     clip C + deco C      durée C
+     outro                3.0 s  → fondu final à −0.6 s
```

Pistes : 0 chrome · 1 cartes plein écran · 3 captions · 5 déco par clip · 6 vidéo · 7 audio.
La vidéo est `muted`, l'audio vient d'un `<audio>` séparé sur le même fichier.

Conventions de style (héritées de jarvis) : fond `#17130e`, texte `#f2ead9`, accent `#f2a33c`
(changer l'accent pour la marque), Inter 900 pour les lignes, JetBrains Mono pour slates /
captions / timecode, entrées GSAP courtes (0.25-0.5 s, `expo.out` / `power4.out`), coupes
sèches entre cartes, un seul fondu à la fin.

### 5. Vérifier et rendre

```bash
npx hyperframes@0.7.64 check build/<name>
npx hyperframes@0.7.64 render build/<name> --quality high -o renders/<name>.mp4
```

Puis extraire 5-6 frames aux moments clés et les regarder :

```bash
for t in 0.8 <milieu A> <K1> <milieu B> <outro>; do
  ffmpeg -y -ss $t -i renders/<name>.mp4 -frames:v 1 renders/f-$t.png
done
```

Contrôler : captions lisibles et jamais sur deux lignes, vidéo bien dans son cadre, aucun
texte qui déborde, pas de noir en queue (durée totale ≤ somme réelle).

Frames de contrôle en planche contact : `ffmpeg … -filter_complex xstack=inputs=N` sur des
vignettes 360 px, puis les regarder.

### 6. Livrer

Donner le chemin du MP4, la liste des segments retenus (timecodes source) et une phrase
sur pourquoi ces moments. Proposer une variante (autre hook, autre accent couleur) seulement
si l'utilisateur le demande.

## Pièges connus

- `data-duration` d'un `<video>` supérieur à la durée réelle du clip → image figée / noir.
  Toujours reprendre la durée via `ffprobe` après la coupe.
- Placer le `.big-word` (pull-quote) à l'apparition de la phrase qu'il cite, pas au début du clip.
- `white-space: nowrap` sur les captions : couper les phrases longues en deux cues.
- json3 : ignorer les events `aAppend: 1` (retours à la ligne) — le script s'en charge.
