import requests as rq
import re
from xml.etree import ElementTree as eTree

queryType = input("Enter query type (doi/arxiv): \n")

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


if queryType == 'doi':
    metaDict = metaQueryRes.json()
    print(tuple((aDict['given'], aDict['family'])
                for aDict in metaDict['author']))
    print(re.sub('</?mml.+?>', '', metaDict['title']))
elif queryType == 'arxiv':
    aStr = '{http://www.w3.org/2005/Atom}'
    xmlEntryRoot = eTree.fromstring(metaQueryRes.text).find(f'{aStr}entry')
    print(tuple(tuple(ele.text.rsplit(' ', 1))
                for ele
                in xmlEntryRoot.findall(f'{aStr}author/{aStr}name')))
    print(re.sub('\\s+',
                 ' ',
                 xmlEntryRoot.find(f'{aStr}title').text.replace('\n', '')))
else:
    raise ValueError(f"Unknown metaType {queryType}")
