# Suite Artisan - Image Providers

## Pipeline

Media priority is strict: artisan uploads, Pexels, Pixabay, then a graphic
fallback. Provider acquisition happens only while the Admin creates the first
media profile for a V3 site. Public HTML never calls a provider API.

`ImageProvider` normalizes search, download, attribution and health checks.
`PexelsProvider` and `PixabayProvider` translate their API payloads into an
`ImageAsset`. Rate limits, timeouts, invalid JSON and HTTP failures are explicit
provider errors. The fallback chain continues and a total provider failure
never blocks site generation.

## Configuration

Optional environment variables:

```text
PEXELS_API_KEY=
PIXABAY_API_KEY=
SITE_MEDIA_RECENT_USAGE_WINDOW=200
SITE_MEDIA_PROVIDER_CACHE_TTL_HOURS=24
SITE_MEDIA_PROVIDER_TIMEOUT_SECONDS=8
SITE_MEDIA_PROVIDER_RESULTS_PER_QUERY=12
```

Keys are read only from settings, never stored in cache metadata, database
rows, generated HTML or logs. With no key, status is `non_configure` and the
renderer uses artisan media or a graphical fallback.

## Queries and cache

`MediaQueryProfile` derives queries from trade, art direction and usage. It
uses architectural, material and project language rather than only a generic
trade word. Search results are cached by provider plus normalized query,
orientation and result count for 24 hours. The cache stores normalized public
asset metadata, never image bytes or credentials.

## Storage and provenance

Selected provider files are downloaded during Admin generation, validated,
orientation-corrected and encoded to a web image and thumbnail through the
existing media processor. This avoids permanent Pixabay hotlinking and public
runtime dependency. Storage uses the configured Suite Artisan storage backend;
this phase creates no bucket or paid infrastructure.

The existing `site_media_library` record retains provider, provider asset ID,
photographer, source URL, provider URL, query, dimensions, license metadata,
usage count and last use. Admin selections expose source and photographer plus
a link to the original source. Public media credits are rendered discreetly
when credit metadata exists.

## Anti-repeat

The existing selection and usage tables remain the source of truth. Recent
history is configurable and defaults to 200 rows. Never-used assets rank first,
then deterministic artisan-specific ranking applies. A provider asset cannot
occupy two usages on the same site. Artisan photos always win before this
ranking is considered.

## Provider obligations

Pexels requests use its documented authorization header. Stored attribution
retains photographer, Pexels source and the Pexels License name. The product
does not reproduce Pexels search as a user-facing core feature.

Pixabay requests use safe-search photo results. Selected files are downloaded
to Suite Artisan storage rather than permanently hotlinked. Source, creator
and Pixabay Content License metadata remain attached. Provider content can
still contain third-party rights; an operator must review sensitive commercial
uses and remove an asset when rights or attribution are uncertain.

Provider contracts and limits can change. Re-check official API and license
pages before production launch or a material change in use.

## Tests and limitations

HTTP is mocked for Pexels success, rate limit, timeout and invalid response;
Pixabay fallback, no-key, zero-result and full outage are covered. A real API
test is optional and must never print a key. This implementation does not
perform automated face, trademark, property-release or aesthetic scoring.
