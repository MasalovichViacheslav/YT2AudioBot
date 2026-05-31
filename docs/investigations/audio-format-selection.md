# Investigation: Audio format selection issues on Render

## Environment
- **Platform:** Render (Frankfurt, EU Central)
- **yt-dlp:** `>=2026.3.17`
- **Python:** 3.12

## Observed behavior
- Users almost always see only one quality option: Economy 129kbps
- Occasionally two options appear — Economy and High — but both show
  identical bitrate (129kbps) and file size, which makes no sense
- In rare cases downloaded audio is in a different language than the video

## Investigation

### Tooling
Added `/debug_url` owner command to inspect raw yt-dlp output and
`_select_formats` result directly on production without code instrumentation.
Initial version called yt-dlp without cookies, which caused YouTube to
trigger bot detection after several requests while the bot's own services
continued working. Fixed by reusing the same cookies logic as
`MetadataService`. Removed after investigation and replaced with persistent
DEBUG-level logging in `MetadataService`.

### Finding 1: duplicate quality options (format_id suffixes)
Local debug showed two m4a streams: `139` at 48kbps and `140` at 129kbps.
`_select_formats` correctly produced economy(48kbps) and standard(129kbps).

`/debug_url` on Render returned `format_id=140-0` and `format_id=140-1`
for the same 129kbps stream — two entries with different format_ids but
identical abr. The 48kbps stream (`139`) was absent entirely.

yt-dlp expands multi-language audio tracks into separate entries with
suffixed format_ids when YouTube serves multiple language variants for the
same quality level. This is confirmed in yt-dlp/yt-dlp#12105. The previous
deduplication by `format_id` let both entries through — economy and high
both resolved to 129kbps, producing the duplicate options users reported.

**Fix:** deduplicate by `int(abr)` instead of `format_id`.

### Finding 2: only one quality option available on Render
YouTube consistently serves only one m4a bitrate (~129kbps) from Render's
selected region IP. The ~48kbps stream present locally is absent. This is
YouTube's decision based on IP/region and cannot be controlled from the
application side. As a result, users on Render will almost always see a
single quality option for m4a format.

### Finding 3: wrong language track selected
Full stream dump revealed that YouTube serves multiple language variants
per quality level — e.g. `140-0` (`English (US), medium`) and `140-1`
(`Russian original (default), medium`). All variants share nearly identical
abr values (difference as small as 0.001 kbps), so `min()` with a
tie-breaker based on abr proximity is not reliable — floating point
differences determine the winner rather than language preference.

Also reproduced on YouTube Shorts with multi-language tracks.

**Fix:** refactored `_select_formats` to filter by original language track
first (`"original" in _get_note(f)`), then apply quality target selection
within the language-filtered pool. This makes language selection independent
of bitrate comparison entirely. Falls back to all streams if no track is
marked as original.

### Finding 4: DRC streams leaking through filter
yt-dlp returns DRC (Dynamic Range Compression) streams as alternatives to
standard streams at the same bitrate. These appear in multiple forms:
- `format_note` starting with `"DRC"` — caught by original filter
- `format_id` ending with `"-drc"` — caught by format_id suffix check
- `format_note` ending with `", DRC"` — missed by `startswith`, present
  on multi-language content (e.g. `"Russian original (default), medium, DRC"`)

The original filter missed the third case.

**Fix:** replaced `format_note.startswith("DRC")` with
`"drc" not in _get_note(f)` (case-insensitive substring match),
which covers all three forms. `format_id.endswith("-drc")` retained
as a secondary guard.

### Finding 5: yt-dlp uses 'note' instead of 'format_note' for some content
For standard videos yt-dlp populates `format_note` with the track
description (e.g. `"Russian original (default), medium"`). For some content
types — observed on YouTube Shorts with multi-language tracks — yt-dlp
populates `note` instead, leaving `format_note` absent entirely.

This caused the original language tie-breaker and DRC filter to silently
fail for Shorts, since both read only `format_note`.

**Fix:** added `_get_note()` helper that reads `format_note` first and
falls back to `note`, normalised to lowercase:
```python
@staticmethod
def _get_note(f: dict[str, Any]) -> str:
    return (f.get("format_note") or f.get("note") or "").lower()
```
All format note reads in `_select_formats` now go through `_get_note()`.

### Finding 6: storyboard streams passing abr filter
yt-dlp includes storyboard streams (`ext=mhtml`) in the format list with
`abr=0` and `vcodec=none`. The existing filter excluded video streams via
`vcodec == "none"` but did not explicitly guard against `abr=0`, relying
implicitly on `abr is not None`. Storyboard streams passed the filter and
could interfere with format selection if no valid audio streams were present.

**Fix:** added `abr > 0` guard to the audio stream filter.

## Root cause summary
YouTube serves a richer and different set of audio streams from Render's
selected region IP than from a local machine: multiple language variants per
quality level, DRC alternatives, and fewer distinct bitrates. The original
`_select_formats` was written against local yt-dlp output and did not
account for this. Bugs only surfaced in production. Additionally, yt-dlp
itself is inconsistent in field naming across content types, using either
`format_note` or `note` depending on the context.

## Changes made
- `services/metadata.py`: deduplicate by bitrate; add `_get_note()` helper;
  filter by original language track first; replace DRC `startswith` check
  with case-insensitive substring match via `_get_note()`; add `abr > 0`
  guard; add DEBUG logging
- `bot/routers/owner.py`: added then removed `/debug_url` command