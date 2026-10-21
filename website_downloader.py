"""Download linked HTML pages from one website using Python's standard library."""

import argparse
import hashlib
import json
import time
from collections import deque
from html.parser import HTMLParser
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

USER_AGENT = "Website-Downloader/1.0"
MAX_BYTES = 5 * 1024 * 1024


def normalize_url(value):
    value = value.strip()
    if "://" not in value:
        value = "https://" + value
    if any(c.isspace() or ord(c) < 32 for c in value):
        raise ValueError("URLs must not contain raw whitespace or control characters.")
    p = urlsplit(value)
    if p.scheme.lower() not in ("http", "https") or not p.hostname:
        raise ValueError("Use an HTTP/HTTPS URL or hostname.")
    if p.username is not None or p.password is not None:
        raise ValueError("URLs must not contain credentials.")
    port = p.port
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("Invalid port.")
    host = p.hostname.encode("idna").decode("ascii")
    host = f"[{host}]" if ":" in host else host
    scheme = p.scheme.lower()
    if port is not None and port != (443 if scheme == "https" else 80):
        host += f":{port}"
    return urlunsplit((scheme, host, p.path or "/", p.query, ""))


def origin(url):
    p = urlsplit(url)
    return p.scheme, p.netloc


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.base = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "base" and self.base is None and attrs.get("href"):
            self.base = attrs["href"]
        if tag in ("a", "area") and attrs.get("href"):
            self.hrefs.append(attrs["href"])


class ScopedRedirects(HTTPRedirectHandler):
    def __init__(self, site_origin, allowed):
        self.site_origin = site_origin
        self.allowed = allowed

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = normalize_url(newurl)
        if origin(target) != self.site_origin or not self.allowed(target):
            raise URLError("Redirect leaves the website or is disallowed by robots.txt.")
        return super().redirect_request(req, fp, code, msg, headers, target)


def crawl(start, output, max_pages=100, delay=1.0, include_query=False):
    start = normalize_url(start)
    if not include_query:
        p = urlsplit(start)
        start = urlunsplit((p.scheme, p.netloc, p.path, "", ""))
    site_origin = origin(start)
    robots_url = urlunsplit((*site_origin, "/robots.txt", "", ""))
    robots = RobotFileParser()
    # Robots redirects are restricted to this origin before a policy is loaded.
    setup = build_opener(ScopedRedirects(site_origin, lambda url: True))
    try:
        with setup.open(Request(robots_url, headers={"User-Agent": USER_AGENT}), timeout=15) as response:
            policy = response.read(MAX_BYTES + 1)
            if len(policy) > MAX_BYTES:
                raise ValueError("robots.txt exceeds the size limit.")
            robots.parse(policy.decode("utf-8", errors="replace").splitlines())
    except HTTPError as error:
        error.close()
        if error.code in (404, 410):
            robots.parse([])
        else:
            raise ValueError(f"Cannot establish robots.txt policy (HTTP {error.code}).") from error
    allowed = lambda url: robots.can_fetch(USER_AGENT, url)
    if not allowed(start):
        raise ValueError("The starting URL is disallowed by robots.txt.")
    interval = max(delay, robots.crawl_delay(USER_AGENT) or 0)
    rate = robots.request_rate(USER_AGENT)
    if rate and rate.requests > 0:
        interval = max(interval, rate.seconds / rate.requests)
    opener = build_opener(ScopedRedirects(site_origin, allowed))
    output = Path(output)
    pages = output / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    queue = deque([start])
    seen = {start}
    fetched = set()
    records = []
    attempts = 0
    while queue and attempts < max_pages:
        url = queue.popleft()
        if url in fetched:
            continue
        if not allowed(url):
            records.append({"url": url, "result": "robots-disallowed"})
            continue
        # Delay before every navigation; redirected requests belong to that navigation.
        time.sleep(interval)
        attempts += 1
        fetched.add(url)
        print(f"[{attempts}/{max_pages}] {url}")
        try:
            with opener.open(Request(url, headers={"User-Agent": USER_AGENT}), timeout=15) as response:
                final = normalize_url(response.geturl())
                if final in fetched and final != url:
                    continue
                fetched.add(final)
                content_type = response.headers.get_content_type()
                if content_type not in ("text/html", "application/xhtml+xml"):
                    records.append({"url": url, "result": "non-html", "content_type": content_type})
                    continue
                data = response.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    records.append({"url": url, "result": "too-large"})
                    continue
                filename = hashlib.sha256(final.encode()).hexdigest() + ".html"
                destination = pages / filename
                destination.write_bytes(data)
                records.append({"url": url, "final_url": final, "result": "saved",
                                "file": "pages/" + filename, "bytes": len(data)})
                parser = Links()
                encoding = response.headers.get_content_charset() or "utf-8"
                try:
                    text = data.decode(encoding, errors="replace")
                except LookupError:
                    text = data.decode("utf-8", errors="replace")
                parser.feed(text)
                base = urljoin(final, parser.base) if parser.base else final
                for href in parser.hrefs:
                    target = urljoin(base, href)
                    if urlsplit(target).scheme.lower() not in ("http", "https"):
                        continue
                    try:
                        target = normalize_url(target)
                    except ValueError:
                        continue
                    if origin(target) != site_origin:
                        continue
                    if urlsplit(target).query and not include_query:
                        continue
                    # Bound discovery as well as request attempts to avoid huge queues.
                    if target not in seen and len(seen) < max_pages:
                        seen.add(target)
                        queue.append(target)
        except (OSError, URLError, ValueError, HTTPException) as error:
            if isinstance(error, HTTPError):
                error.close()
            records.append({"url": url, "result": "error", "message": str(error)})
    manifest = {"start_url": start, "attempts": attempts, "max_pages": max_pages,
                "discovery_limit_reached": len(seen) >= max_pages,
                "records": records}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    saved = sum(record["result"] == "saved" for record in records)
    print(f"Saved {saved} HTML pages to {output.resolve()}")
    if manifest["discovery_limit_reached"]:
        print("Discovery limit reached; increase --max-pages to explore more links.")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("website", nargs="?", help="Starting URL or hostname")
    parser.add_argument("--output", default="downloads", help="Output folder (default: downloads)")
    parser.add_argument("--max-pages", type=int, default=100, help="Discovery/request limit (default: 100)")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between navigations (default: 1)")
    parser.add_argument("--include-query", action="store_true", help="Include URLs with query strings")
    args = parser.parse_args()
    if args.max_pages < 1 or not 0 <= args.delay < float("inf"):
        parser.error("--max-pages must be positive and --delay must be finite and non-negative.")
    try:
        value = args.website if args.website is not None else input("Website: ")
        result = crawl(value, args.output, args.max_pages, args.delay, args.include_query)
        return 0 if any(r["result"] == "saved" for r in result["records"]) else 1
    except (ValueError, OSError, URLError, HTTPException) as error:
        print(f"Download failed: {error}")
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled. Already saved pages remain on disk.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
