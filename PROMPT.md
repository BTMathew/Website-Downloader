# AI prompt guide: building `website_downloader.py`

## 1. Project skeleton

```text
Create Website-Downloader with website_downloader.py, README.md, CHEAT.md, PROMPT.md, and .gitignore. Use Python 3.9+ standard library only. Keep work local until publication is requested.
```

## 2. Website scope and robots

```text
Normalize HTTP/HTTPS URLs, default bare hosts to HTTPS, reject credentials/whitespace/invalid ports, support IDNA and IPv6, remove default ports and fragments. Define scope as exact scheme/hostname/port. Load robots.txt with restricted redirects, permit missing 404/410 policy, fail closed for other policy retrieval errors, and respect can_fetch, crawl_delay, and request_rate. Check redirects before requesting each target, requiring same origin and robots permission.
```

## 3. Crawl and save

```text
Use a breadth-first queue and deduplicate URLs. Default to 100 discovered URLs/navigation attempts and a one-second navigation delay, increased by robots policy. Use a 15-second socket timeout and 5 MiB HTML cap. Parse anchor/area links and the first base href using HTMLParser. Resolve against final URLs, stay within origin, and ignore query links unless --include-query is enabled. Save only HTML/XHTML responses as original bytes in pages/<SHA256-final-URL>.html. Do not mirror assets, execute JavaScript, submit forms, or authenticate. Record per-page results in manifest.json. Bound discovery queue and request attempts.
```

## 4. CLI and documentation

```text
Accept optional website argument or prompt; add --output, --max-pages, --delay, and --include-query. Validate positive limits and finite nonnegative delay. Return 0 if any page is saved, otherwise 1; keep argparse errors at 2. Document limitations, partial success, scope/redirect behavior, output overwrite behavior, query traps, and that link discovery cannot guarantee every site page. Add cheat sheet and prompts. Ignore downloaded files and environments.
```

## 5. Verify

```text
Use local HTTP servers to test link discovery, cycles/fragments, external links/redirect rejection, query handling, robots disallow rules, HTML/non-HTML handling, size limits, and manifests. Do not crawl external websites for routine tests.
```
