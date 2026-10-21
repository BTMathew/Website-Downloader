# Website Downloader

Download HTML pages reachable through links on one website. This Python crawler follows anchor and image-map links, saves each page, and creates a URL-to-file manifest. It uses only Python's standard library: no additional installation is needed after Python 3.9+.

## Run

Open a terminal in this project folder:

```powershell
python website_downloader.py
python website_downloader.py https://example.com
python website_downloader.py https://example.com --max-pages 500 --delay 1 --output downloads/example
python website_downloader.py --help
```

Without a website argument, the script asks for one. Bare hostnames default to HTTPS. Use the final website hostname and scheme: redirects from HTTP to HTTPS or from a bare domain to www cross the origin boundary and are rejected. Custom ports and IDNA hostnames are supported. Percent-encode spaces and non-ASCII path/query characters.

## What gets downloaded

The crawler discovers links from HTML pages and stays on the exact starting origin (scheme, hostname, and port). It removes fragments and deduplicates normalized URLs. It respects robots.txt, Crawl-delay, and Request-rate when available. Missing robots.txt (404/410) permits crawling; other policy retrieval failures stop the run. Redirect destinations are checked for scope and robots permission before requesting them.

Only responses marked text/html or application/xhtml+xml are saved. Files are limited to 5 MiB each; larger pages are skipped. Images, PDFs, CSS, JavaScript, and other assets are not saved. The crawler may request a linked non-HTML URL before learning its content type. HTML links are preserved as received, so this is an archive of source pages, not a fully working offline mirror.

“Every page” means discoverable, permitted pages within the configured limits. Unlinked pages, pages discoverable only through JavaScript, login-protected content, form submissions, and other subdomains are excluded. Sitemaps are not read. No crawler can guarantee finding all pages from links alone.

## Options

| Option | Default | Purpose |
| --- | --- | --- |
| `website` | Prompt | Starting page or hostname |
| `--output` | `downloads` | Output directory relative to the terminal's current folder |
| `--max-pages` | `100` | Bounds discovered URLs and navigation attempts, including failed/non-HTML requests |
| `--delay` | `1` | Minimum seconds before each navigation; robots directives can increase it |
| `--include-query` | Off | Follows query-string links; otherwise such links are skipped and a starting query is removed |

The delay applies between navigations; redirects within a navigation can occur immediately. Socket operations have a 15-second timeout, not a total crawl deadline. Query strings can create large or infinite URL spaces, so increase limits deliberately. Ordinary GET requests only; no browser execution, authentication, or form submission.

## Output

```text
downloads/
|-- pages/
|   `-- <SHA-256-of-final-URL>.html
`-- manifest.json
```

Hashed filenames prevent URL paths from becoming local file paths. HTML bytes are saved unchanged. The manifest lists requested/final URLs, saved file paths, byte counts, skipped pages, and errors. It also reports whether the discovery cap was reached. Re-running in the same folder overwrites matching page files and the manifest; older unrelated files remain. Use separate output folders for separate snapshots. Cancellation can leave saved pages without a current manifest.

Exit 0 means at least one page was saved; it does not guarantee a complete archive. Exit 1 means no page was saved or a handled failure/cancellation occurred. Invalid CLI arguments exit with 2. Review the manifest for per-page errors and limits.

## Common issues

- **Redirect leaves the website**: start with the final URL shown in your browser, including its exact HTTPS/www form.
- **Robots disallowed/policy error**: choose a permitted website or resolve its policy/network failure.
- **Few pages saved**: inspect robots rules, the page limit, query-string behavior, and whether the site requires JavaScript or login.
- **Certificate/network error**: check hostname, network, computer clock, and Python trust store. HTTPS verification remains enabled; system proxies may apply.

## Project files

```text
Website-Downloader/
|-- website_downloader.py
|-- README.md
|-- CHEAT.md
|-- PROMPT.md
`-- .gitignore
```

[CHEAT.md](CHEAT.md) explains the code. [PROMPT.md](PROMPT.md) provides recreation prompts. Downloaded content stays local and is ignored by Git.
