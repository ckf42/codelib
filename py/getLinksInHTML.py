#!/usr/bin/env python3
import argparse
import requests as rq
import urllib.parse
from bs4 import BeautifulSoup, SoupStrainer

parser = argparse.ArgumentParser()
parser.add_argument('url', type=str, help="Target url")
parser.add_argument('--port', '-p', type=int, help="Optional port number")
args = parser.parse_args()

if not args.url.startswith('http'):
    args.url = '//' + args.url
parsedUrl = urllib.parse.urlparse(args.url, 'http')
baseUrl = urllib.parse.ParseResult('http',
                                   parsedUrl.netloc + ('' if args.port is None else f':{args.port}'),
                                   parsedUrl.path if parsedUrl.netloc else '',
                                   *parsedUrl[3:]).geturl()
forbidLink = ['#', 'javascript:', 'mailto:']

res = rq.get(baseUrl)
print("Status code:", res.status_code)

for link in BeautifulSoup(res.content, features='html.parser').select('[href], [src]'):
    if link.has_attr('href') and not any(link.get('href').startswith(forbid) for forbid in forbidLink):
        print(urllib.parse.urljoin(baseUrl, link['href']))
    elif link.has_attr('src'):
        print(urllib.parse.urljoin(baseUrl, link['src']))

