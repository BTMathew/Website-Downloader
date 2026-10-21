# `website_downloader.py` cheat sheet

| Component | Role |
| --- | --- |
| `normalize_url` | Validates scheme, credentials, port, whitespace; normalizes hostname, default ports, empty path, and fragments. |
| `origin` | Returns scheme and authority to define exact website scope. |
| `Links` | HTMLParser subclass collecting anchor/area hrefs and the first base href. |
| `ScopedRedirects` | Checks each redirected target against origin and robots permission before requesting it. |
| `crawl` | Loads robots policy, uses a breadth-first queue, delays requests, limits discovery/downloads, writes HTML and manifest. |
| `main` | Handles interactive input, CLI options, validation, and exit codes. |

## Important behavior

- `deque` implements breadth-first traversal.
- `seen` bounds discovered URLs; `fetched` avoids duplicate retrievals and final redirected URLs.
- `RobotFileParser` evaluates robots policy and supported timing directives.
- Each HTML response is read up to the size cap plus one byte to detect oversize content.
- SHA-256 filenames map final URLs to safe local filenames.
- Links resolve against the final response URL and any HTML base element.
- Query-string links are skipped unless explicitly enabled.
- The manifest records saved, non-HTML, too-large, disallowed, and failed outcomes.
- A successful exit means some pages were saved, not that the entire site was captured.

```powershell
python website_downloader.py example.com --max-pages 200 --output downloads/example
```

No dependencies beyond Python. JavaScript rendering and asset mirroring are outside this version's scope.
