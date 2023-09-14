#!/usr/bin/env python3
import argparse
import urllib.parse

import requests as rq
from bs4 import BeautifulSoup, SoupStrainer


def getArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('url', type=str, help="Target url")
    parser.add_argument('--port', '-p', type=int, help="Optional port number")
    return parser.parse_args()

strainer = SoupStrainer(lambda _, attrd: any(x in attrd for x in ('href', 'src')))
strainer = SoupStrainer(
        lambda _, attrd: \
                'src' in attrd \
                or ('href' in attrd \
                    and not attrd['href'].startswith(('#', 'javascript:', 'mailto:')))
        )

def main():
    args = getArgs()
    if not args.url.startswith('http'):
        args.url = '//' + args.url
    parsedUrl = urllib.parse.urlparse(args.url, 'http')
    baseUrl = urllib.parse.ParseResult(
            'http',
            parsedUrl.netloc + ('' if args.port is None else f':{args.port}'),
            parsedUrl.path if parsedUrl.netloc else '',
            *parsedUrl[3:]).geturl()
    res = rq.get(baseUrl)
    print("Status code:", res.status_code)
    seenLinks: set[str] = set()
    for link in BeautifulSoup(res.content,
                              features='html.parser',
                              parse_only=strainer):
        if link.has_attr('href'):
            seenLinks.add(urllib.parse.urljoin(baseUrl, link['href']))
        elif link.has_attr('src'):
            seenLinks.add(urllib.parse.urljoin(baseUrl, link['src']))
    for link in sorted(seenLinks):
        print(link)
    print(f"Total: {len(seenLinks)}")

if __name__ == '__main__':
    main()

