import requests as rq
import re
from html import unescape

import unicodedata as ud

from xml.etree import ElementTree as eTree

queryType = input("Enter query type (doi/arxiv/jstor): \n")

reDOISanitizePattern, metaQueryURL, reqHeader = {
    'doi': (
        '^(https?://)?(dx\\.|www\\.)?doi(\\.org/|:|/)\\s*',
        'https://doi.org/{id}',
        {"Accept": "application/vnd.citationstyles.csl+json"}
    ),
    'arxiv': (
        '^(https?://)?arxiv(\\.org/abs/|:)?\\s*',
        'http://export.arxiv.org/api/query?id_list={id}',
        None
    ),
    'jstor': (
        '^(https://)?(www.)?jstor(.org/stable/|:\\s*)',
        'https://www.jstor.org/citation/ris/{id}',
        {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) "
         "Gecko/20100101 Firefox/88.0"}
    )
}.get(queryType.lower(), (None, None, None))

docIden = input("Enter document identifier: \n")

if reDOISanitizePattern is None:
    quit()
docIden = re.sub(reDOISanitizePattern,
                 '',
                 docIden.strip(),
                 flags=re.IGNORECASE)
metaQueryRes = rq.get(metaQueryURL.format(id=docIden),
                      headers=reqHeader)

print(f"id: {docIden}")
print(f"URL: {metaQueryRes.url}")

if queryType == 'doi':
    metaDict = metaQueryRes.json()
    for k in sorted(metaDict.keys()):
        print(k, metaDict[k])
    print(metaDict['published-print'].get('date-parts', [['']])[0][0])
    print(tuple((aDict['given'], aDict['family'])
                for aDict in metaDict['author']))
    # print(re.sub('</?mml.+?>', '', metaDict['title']))
    print(''.join((f' {ud.name(c).title()}'
                   if not c.isascii() and ud.category(c) == 'Sm'
                   else c)
                  for c
                  in re.sub('</?.+?>', '', unescape(metaDict['title']))))
elif queryType == 'arxiv':
    for line in metaQueryRes.text.splitlines():
        print(line)
    aStr = '{http://www.w3.org/2005/Atom}'
    xmlEntryRoot = eTree.fromstring(metaQueryRes.text).find(f'{aStr}entry')
    print(tuple(tuple(ele.text.rsplit(' ', 1))
                for ele
                in xmlEntryRoot.findall(f'{aStr}author/{aStr}name')))
    print(re.sub('\\s+',
                 ' ',
                 xmlEntryRoot.find(f'{aStr}title').text.replace('\n', '')))
elif queryType == 'jstor':
    for line in metaQueryRes.text.splitlines():
        print(line)
else:
    raise ValueError(f"Unknown metaType {queryType}")
