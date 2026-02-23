# Quality Notes

## Speed
- Use `yt-dlp` subtitle extraction first (no audio download).
- Prefer existing caption tracks over heavy transcription.

## Accuracy
- Prefer manual captions when available.
- De-duplicate repeated auto-caption fragments.
- Keep section windows at ~5 minutes for scanability.

## Live stream handling
- Filter repeated filler phrases.
- Prioritize explicit announcement/product phrases.
