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
(`Russian original (default), medium`). All variants share the same abr,
so `min()` picks the first entry in the list, which is not guaranteed to
be the original language track. Observed in production: Russian video
downloaded in English.

**Fix:** (to be implemented) extend `min()` sort key to prefer streams 
with `"original"` in format_note` when abr values are equal.

### Finding 4: DRC streams leaking through filter
yt-dlp returns DRC (Dynamic Range Compression) streams as alternatives to
standard streams at the same bitrate. These appear in two forms:
- `format_note` starting with `"DRC"` — already filtered
- `format_id` ending with `"-drc"` with empty `format_note` — not filtered

The existing filter missed the second case, allowing streams like `140-drc`
to pass through.

**Fix:** add `format_id.endswith("-drc")` as a second filter condition.

## Root cause summary
YouTube serves a richer and different set of audio streams from Render's
selected region IP than from a local machine: multiple language variants per
quality level, DRC alternatives, and fewer distinct bitrates. The original
`_select_formats` was written against local yt-dlp output and did not
account for this. Bugs only surfaced in production.

## Changes made/ to be made
- `services/metadata.py`: deduplicate by bitrate, prefer original language
  track in `min()`, filter DRC by `format_id` suffix, add DEBUG logging
- `services/downloader.py`: add `format_note*=original` as primary selector
- `bot/routers/owner.py`: added then removed `/debug_url` command