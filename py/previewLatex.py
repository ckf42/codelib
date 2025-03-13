def previewLatex(inputExpression):
    import pathlib
    import shutil
    import subprocess
    import tempfile

    if shutil.which('pdflatex') is None:
        print("pdflatex not found")
        return
    if shutil.which('pdftocairo') is None:
        print('pdftocairo not found')
        return

    realTmpPath = '/tmp'
    if shutil.which('cygpath') is not None:
        realTmpPath = subprocess.run(
                ['cygpath', '-w', '/tmp'],
                capture_output=True,
                text=True).stdout.strip()
    texContent = '\n'.join((
        r'\documentclass{article}',
        r'\usepackage{amsmath, amssymb, amsfonts}',
        r'\usepackage[active,tightpage]{preview}',
        r'\usepackage{varwidth}',
        r'\AtBeginDocument{\begin{preview}\begin{varwidth}{\linewidth}}',
        r'\AtEndDocument{\end{varwidth}\end{preview}}',
        r'\pagestyle{empty}',
        r'\begin{document}',
        '$' + latex(inputExpression) + '$',
        r'\end{document}',
    ))
    try:
        fp = tempfile.NamedTemporaryFile(
                'wt',
                delete=False,
                encoding='utf-8',
                prefix='previewLatex_')
        fpPath = fp.name.replace('/tmp', realTmpPath, 1)
        print(texContent, file=fp)
        fp.close()
        texCompile = subprocess.run(
                ['pdflatex', '-synctex=0', '-interaction=nonstopmode', fpPath],
                cwd='/tmp',
                stdout=subprocess.PIPE,
                text=True,
                encoding='UTF-8')
        if '! LaTeX Error: File' in texCompile.stdout:
            pkgNameIdx = texCompile.stdout.find('! LaTeX Error: File `') + 21
            pkgNameSeg = texCompile.stdout[pkgNameIdx:]
            pkgNameEndIdx = pkgNameSeg.find("'")
            raise RuntimeError(f"Package {pkgNameSeg[:pkgNameEndIdx - 4]} not found")
        subprocess.run(
                ['pdftocairo', '-png', '-singlefile', fpPath + '.pdf', fpPath],
                cwd='/tmp',
                stdout=subprocess.PIPE)
        pngPath = pathlib.Path(fp.name + '.png')
        if not pngPath.exists():
            raise RuntimeError("pdftocairo failed")
        fContent = b''
        with pngPath.open('rb') as imgF:
            fContent = imgF.read()
        subprocess.run(['wezterm', 'imgcat'], input=fContent)
    except Exception as e:
        print(e)
    finally:
        for f in ('.aux', '.log', '.pdf', '.png', ''):
            p = pathlib.Path(fp.name + f)
            if p.is_file():
                p.unlink()

