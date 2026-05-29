# Investigation: OOM crash in MetadataService on Render free tier

## Environment
- **Platform:** Render free tier (512MB RAM)
- **yt-dlp:** `>=2026.3.17`
- **Python:** 3.12
- **JS runtime:** Deno (required by yt-dlp for YouTube JS challenges)

## Observed behavior
- Single user during tests, sequential requests
- Bot crashes with OOM consistently during metadata extraction
- Logs confirm: `metadata_start` present, `metadata_after_extract` absent — crash inside `extract_info`
- RSS grows 30–60MB per `extract_info` call and never returns to baseline
- Growth is unpredictable per call: +61MB, +36MB, 0MB — depends on YouTube response for a given video
- RSS between `metadata_after_extract` and `metadata_end` does not change — growth is strictly inside `extract_info`

## Root cause (probable, not confirmed)
Deno subprocess (V8) is spawned on every `extract_info` call to solve YouTube JS challenges. After the subprocess exits, **glibc does not return freed pages to OS** — classic glibc arena fragmentation behavior in long-running processes. This causes cumulative RSS growth across sequential requests.

The growth is not caused by the metadata payload itself (JSON with formats is at most ~500KB). It is a side effect of the infrastructure around extraction: Deno subprocess startup, HTTP sessions, SSL context — all allocated by glibc and not returned to OS after the call.

This is a known pattern with yt-dlp embedded in long-running Python processes. yt-dlp is designed as a CLI tool; embedded usage is not its primary use case. The issue has been open since 2021 (issue #1949) and is not fixed upstream, as developers consider it a Python/glibc behavior rather than a yt-dlp bug.

## What was tried

### cachedir=False (no effect)
Added `cachedir=False` to `ydl_opts` in `MetadataService` to disable JS player cache. No measurable effect on RSS growth.

### jemalloc (resolved)
Replaced glibc allocator with jemalloc via `LD_PRELOAD`. jemalloc aggressively returns free pages to OS via a background thread.

**Result:** RSS grew from 219MB to 223MB across 8 downloads including two videos over 4 hours long (one ~350MB file). Effectively flat. Problem resolved or reduced to negligible level.

## Solution

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends curl unzip libjemalloc2 \
    && curl -fsSL https://deno.land/install.sh | sh \
    && apt-get purge -y curl unzip && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2
ENV MALLOC_CONF="background_thread:true,dirty_decay_ms:1000,muzzy_decay_ms:1000"
```

- `background_thread:true` — background thread actively returns free pages to OS
- `dirty_decay_ms:1000` — dirty pages are returned to OS 1s after release (default is 10s)

No application code changes required.

## If jemalloc proves insufficient
Next steps in order of complexity:
1. Replace Deno with QuickJS — significantly lighter JS runtime, no separate V8 process
2. Run `extract_info` in a separate subprocess via `ProcessPoolExecutor` — process exits after each call, OS reclaims all memory unconditionally (requires significant refactoring)