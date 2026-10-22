# Biophysics Instagram Publisher

Minimal standalone Python 3.9+ CLI for one already approved Biophysics + AI
poster as a single Instagram feed image. No web app, unofficial API, scraping,
browser automation, campaign discovery, scheduling, or content generation.
Supply the exact approved caption and media yourself. The CLI does not search
outside this directory or access campaign history.

**The 10-minute target is best-effort, not a guarantee.** It depends on existing
credentials, public media hosting, account eligibility, and Meta API availability.
App review, account conversion, Page linking, and hosting setup may take longer.

## Prerequisites

- Business or Creator Instagram account connected to a Facebook Page.
- Existing Meta app configured for Instagram API with Facebook Login and the
  appropriate access level/app review for the target account.
- A valid Facebook Page access token with `instagram_basic`,
  `instagram_content_publish`, and `pages_read_engagement`. Some Business Manager
  role assignments also require `ads_management` and `ads_read`; Page discovery
  may require `pages_show_list` outside this CLI. Complete any Page Publishing
  Authorization or other requirements imposed by Meta. This tool bypasses none.
- The intended Page ID, Instagram account ID, and expected username. The supplied
  target is `gangopadhyay.poulomi`; a profile URL alone does not establish
  professional status, ownership, Page linkage, or API access.
- An unchanged approved RGB JPEG hosted on a public HTTPS server, directly
  returning HTTP 200 with `Content-Type: image/jpeg`, without cookies or auth.
  This conservative CLI accepts at most 8 MiB, width 320-1440, and aspect ratio
  4:5 through 1.91:1. It rejects redirects, query strings (including signed URLs),
  URL credentials, fragments, private/reserved DNS addresses, non-443 ports,
  corrupt files, and other formats. It never converts or crops the approved image.
  Use trusted public hosting, not an untrusted URL. DNS checks are a preflight,
  not an SSRF sandbox or a guarantee of Meta's later reachability.

## Setup

Run inside this new project directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
chmod 600 .env
```

Fill `.env` locally. Never send tokens in chat, commit them, pass them as CLI
arguments, or enable HTTP debug logging. Environment variables override `.env`.
The token is sent only in the Authorization header to `graph.facebook.com`;
it is never sent to the JPEG host. Network proxies and redirects are disabled.
All five IG_* values are required. Choose a currently supported Graph API version;
`v26.0` matches the current official publishing examples, not an automatic upgrade.

Place the already approved caption verbatim in a UTF-8 `caption.txt` file.
The CLI preserves it, including any final newline. Captions must be nonblank,
at most 2,200 characters, at most 30 hashtags and 20 mentions, without control
characters other than newline/tab. Meta may enforce additional/current limits.

## One Operator Flow

Read-only preview is the default and includes live official identity and quota
checks plus an unauthenticated image download:

```sh
.venv/bin/python publisher.py --dry-run \
  --image-url https://YOUR-PUBLIC-HOST/approved-poster.jpg \
  --caption-file caption.txt
```

Publish validates and previews the same inputs, then asks exactly once for
`PUBLISH`, before making any POST request:

```sh
.venv/bin/python publisher.py --publish \
  --image-url https://YOUR-PUBLIC-HOST/approved-poster.jpg \
  --caption-file caption.txt
```

When the operator has already explicitly authorized this exact post for this
active run, append `--confirm-publish`. This flag counts as the one confirmation;
no second prompt appears. It does not skip identity, image, quota, or Meta checks.
Do not persist this flag in automation or treat authorization as permission for
future posts. Dry runs create no containers, attempt guards, or receipts.

The CLI verifies the Page's `instagram_business_account` professional-account
link, then checks the official Instagram ID and username. It checks the
official content publishing quota, creates one container, and checks readiness
up to five times at one-minute intervals before issuing exactly one
`media_publish` request. Only read-only container readiness checks are repeated.

## Outcomes And Safety

Exit 0 means dry-run success or confirmed publishing success. Exit 2 means the
operation stopped. Errors and raw HTTP response bodies are not logged, avoiding
token leaks. The exact caption and public URL are intentionally previewed.

A non-secret `.attempts/<content-fingerprint>.json` guard is exclusively created
and flushed immediately before `media_publish`. It is **not a success receipt**;
it records only account and container IDs. A guard prevents another publish
attempt for identical account/image/caption, including concurrent invocations.
Keep it after success, failure, timeout, or interruption. Different content,
another machine, or deleting guards can defeat this local protection; it is not
a platform idempotency key or campaign history system.

**An ambiguous outcome must never be retried.** A timeout, lost connection,
missing media ID, API error during publish, or interrupted process may mean the
post exists. Stop. Use Meta's official API/tools to inspect the container ID and
target account manually. `GET /<CONTAINER_ID>?fields=status_code` can report
`PUBLISHED`; do not blindly issue `media_publish` again or start another run.
There are no automatic HTTP retries and no automatic guard-reset option.

Only a valid media ID returned by `media_publish` confirms success here. Then,
and only then, the CLI writes `receipts/<content-fingerprint>.json`, containing
IDs, username, UTC confirmation time, API version and content hashes. It omits
tokens, caption text, image URLs and raw API responses. If saving the receipt
fails after publishing, the CLI reports success with the media ID but exits 2
and retains the guard. **Do not republish.** No live publication was performed
while creating this scaffold.

## Tests

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Tests use generated in-memory JPEGs and mocked official API responses. They need
no token, browser, campaign files, network access, or real Instagram account.
They do not prove live credentials, Meta permissions, hosting or publication.

## Official References

- https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/
- https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/content-publishing/
- https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media/
- https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish/