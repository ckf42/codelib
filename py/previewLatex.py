def previewLatex(inputExpression):
    import subprocess
    import tempfile
    import os
    import shutil
    from imgcat import imgcat

    if shutil.which('pdflatex') is None:
        print("pdflatex not found")
        return
    if shutil.which('pdftocairo') is None:
        print('pdftocairo not found')
        return

    realTmpPath = '/tmp'
    if shutil.which('cygpath') is not None:
        realTmpPath = subprocess.run(['cygpath', '-w', '/tmp'], capture_output=True, text=True).stdout.strip()
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
    fp = tempfile.NamedTemporaryFile('wt', delete=False, encoding='utf-8')
    fpPath = fp.name.replace('/tmp', realTmpPath, 1)
    print(texContent, file=fp)
    fp.close()
    subprocess.run(['pdflatex', '-synctex=0', '-interaction=nonstopmode', fpPath],
                   cwd='/tmp',
                   stdout=subprocess.PIPE)
    subprocess.run(['pdftocairo', '-png', '-singlefile', fpPath + '.pdf', fpPath],
                   cwd='/tmp',
                   stdout=subprocess.PIPE)
    print('')
    with open(fp.name + '.png', 'rb') as imgF:
        imgcat(imgF)
    print('')
    for f in ('.aux', '.log', '.pdf', '.png', ''):
        os.unlink(fp.name + f)

