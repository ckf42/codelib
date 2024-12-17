def previewLatex(inputExpression):
    import pathlib
    import shutil
    import subprocess
    import tempfile

    from sympy import latex as splatex


    if shutil.which('pdflatex') is None:
        print("pdflatex not found")
        return
    if shutil.which('pdftocairo') is None:
        print('pdftocairo not found')
        return

    texContent = '\n'.join((
        r'\documentclass{article}',
        r'\usepackage{amsmath, amssymb, amsfonts}',
        r'\usepackage[active,tightpage]{preview}',
        r'\usepackage{varwidth}',
        r'\AtBeginDocument{\begin{preview}\begin{varwidth}{\linewidth}}',
        r'\AtEndDocument{\end{varwidth}\end{preview}}',
        r'\pagestyle{empty}',
        r'\begin{document}',
        '$' + splatex(inputExpression) + '$',
        r'\end{document}',
    ))
    try:
        fp = tempfile.NamedTemporaryFile(
                'wt',
                delete=False,
                encoding='utf-8',
                prefix='previewLatex_')
        fpPath = fp.name
        tempDir = pathlib.Path(fpPath).parent
        with fp:
            fp.write(texContent)
        subprocess.run(
                ['pdflatex', '-synctex=0', '-interaction=nonstopmode', fpPath],
                cwd=tempDir,
                stdout=subprocess.PIPE)
        subprocess.run(
                ['pdftocairo', '-png', '-singlefile', fpPath + '.pdf', fpPath],
                cwd=tempDir,
                stdout=subprocess.PIPE)
        subprocess.run(['wezterm', 'imgcat', fp.name + '.png'])
        print('')
    finally:
        for ext in ('.aux', '.log', '.pdf', '.png', ''):
            if (p := pathlib.Path(fp.name + ext)).exists():
                p.unlink()

