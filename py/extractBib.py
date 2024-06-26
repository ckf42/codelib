import argparse
import pathlib
import re

import bibtexparser

assert bibtexparser.__version__.startswith('1.'), \
        f"bibtexparser (v{bibtexparser.__version__}) is not of version ~1.0"

def getArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
            'tex',
            type=str,
            help="Path to target tex file")
    parser.add_argument(
            '--out',
            type=str,
            help="Path to output bib file. "
            "Defaults to stdout")
    parser.add_argument(
            '--overwrite',
            action='store_true',
            help="Overwrite output bib file if it already exists. "
            "Will truncate the existing file. "
            "Ignored if output to stdout")
    # parser.add_argument(
    #         '--frag',
    #         action='store_true',
    #         help="Output as filecontents fragment. "
    #         "Implies output to stdout")
    # parser.add_argument(
    #         '--inject',
    #         action='store_true',
    #         help="Inject addbibresource command in file. "
    #         "Command will replace the first addbibresource command, "
    #         "and all other addbibresource command will be removed. "
    #         "Path will be absolute if out is given, "
    #         "relative otherwise. "
    #         "Ignored if output to stdout")
    # parser.add_argument(
    #         '--nobackup',
    #         action='store_true',
    #         help="Do not save a backup copy. "
    #         "Ignored if --inject is not present")
    args = parser.parse_args()
    texPath = pathlib.Path(args.tex).resolve(strict=False)
    if not texPath.exists():
        parser.error(f"Tex path ({args.tex}) does not exist")
    args.tex = texPath
    if args.out is not None:
        outPath = pathlib.Path(pathlib.Path.cwd() / args.out).resolve(strict=False)
        if outPath.exists() and not args.overwrite:
            parser.error(
                    f"Output path ({args.out}) exists but --overwrite is not given")
        args.out = outPath
    return args

def main() -> None:
    args = getArgs()
    usedBib: list[str] = []
    citedKeyList: set[str] = set()
    citedEntryDict: dict[str, dict] = dict()
    with args.tex.open('rt', encoding='utf-8') as texFile:
        for line in texFile:
            if line.lstrip().startswith(r'\addbibresource{'):
                gp = re.match(r'\\addbibresource\{(.+?\.bib)\}', line)
                assert gp is not None, f"Unable to parse line: {line}"
                usedBib.append(gp.group(1))
            else:
                for match in re.findall(
                        r'\\[a-zA-Z]*cite[a-zA-Z]*(?:\[.*?\])*?\{([a-zA-Z0-9, ]+)\}',
                        line):
                    citedKeyList.update(re.split(', ?', match))
                for match in re.findall(
                        r'(?:\\\w*cites|\\Cites|\\footcitetexts)'
                        r'((?:(?:\(.*?\)){0,2}(?:\[.*?\]){0,2}\{[a-zA-Z0-9, ]+\})+)',
                        line):
                    for key in re.findall(
                            r'\{([a-zA-Z0-9, ]+)\}',
                            match):
                        citedKeyList.add(key)
    if len(citedKeyList) != 0:
        print(f"Cited keys ({len(citedKeyList)}):")
        print(", ".join(sorted(citedKeyList)))
    else:
        print("No key cited")
        return
    if len(usedBib) != 0:
        print("Included bib:")
        for bib in usedBib:
            print(bib)
            print("")
    else:
        print("No bib is included")
        return
    bibParser = bibtexparser.bparser.BibTexParser(
            ignore_nonstandard_types=False,
            interpolate_strings=False,
            add_missing_from_crossref=True)
    for bib in usedBib:
        bibPath = (args.tex.parent / bib).resolve(strict=False)
        if not bibPath.exists():
            print(f"Used bib file {bib} does not exist")
            continue
        db = None
        with bibPath.open('rt', encoding='utf-8') as bibFile:
            db = bibtexparser.load(bibFile, parser=bibParser)
        assert db is not None, f"Cannot open bib file {str(bibPath)}"
        entryDict = db.entries_dict
        relatedEntries: set[str] = set()
        for k, v in entryDict.items():
            if k in citedKeyList:
                if k in citedEntryDict:
                    print(f"{k} already exists. "
                          f"Overwriting with data from {str(bibPath)}")
                citedEntryDict[k] = v
                if 'related' in v:
                    print(f"{k} contains related key(s) {v['related']}. Adding ...")
                    relatedEntries.update(v['related'].split(','))
        for rKey in relatedEntries:
            if rKey not in citedEntryDict:
                citedEntryDict[rKey] = entryDict[rKey]
    notFoundKeys = citedKeyList.difference(citedEntryDict.keys())
    if len(notFoundKeys) != 0:
        print("These keys are not found in any bib:")
        for k in notFoundKeys:
            print(k)
        print("")
    newDb = bibtexparser.bibdatabase.BibDatabase()
    for entry in citedEntryDict.values():
        newDb.entries.append(entry)
    if args.out is None:
        print("----- copy after this line -----")
        print(bibtexparser.dumps(newDb))
        print("----- copy before this line -----")
    else:
        with args.out.open('wt', encoding='utf-8') as outFile:
            print(r'% Encoding: UTF-8' + '\n', file=outFile)
            print(bibtexparser.dumps(newDb), file=outFile)
            print(f"{str(args.out)} written")

if __name__ == '__main__':
    main()

