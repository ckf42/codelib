def previewLatex(inputExpression):
    import subprocess
    import tempfile
    import os
    import shutil
    import base64
    import sys

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
    try:
        fp = tempfile.NamedTemporaryFile('wt', delete=False, encoding='utf-8')
        fpPath = fp.name.replace('/tmp', realTmpPath, 1)
        print(texContent, file=fp)
        fp.close()
        texCompile = subprocess.run(['pdflatex', '-synctex=0', '-interaction=nonstopmode', fpPath],
                                    cwd='/tmp',
                                    stdout=subprocess.PIPE,
                                    text=True,
                                    encoding='UTF-8')
        if '! LaTeX Error: File' in texCompile.stdout:
            pkgNameIdx = texCompile.stdout.find('! LaTeX Error: File `') + 21
            pkgNameSeg = texCompile.stdout[pkgNameIdx + 21:]
            pkgNameEndIdx = pkgNameSeg.find("'")
            raise RuntimeError(f"Package {pkgNameSeg[:pkgNameEndIdx - 4]} not found")
        subprocess.run(['pdftocairo', '-png', '-singlefile', fpPath + '.pdf', fpPath],
                        cwd='/tmp',
                        stdout=subprocess.PIPE)
        if not os.path.exists(fp.name + '.png'):
            raise RuntimeError("pdftocairo failed")
        fSize = os.path.getsize(fp.name + '.png')
        fContent = b''
        with open(fp.name + '.png', 'rb') as imgF:
            fContent = imgF.read()
        outputSeq = b''.join((
            b'\x1b]1337;File=size=',
            bytes(str(fSize), 'ASCII'),
            b';inline=1;height=auto:',
            base64.b64encode(fContent),
            b'\x07\x0a'
        ))
        print('')
        sys.stdout.buffer.write(outputSeq)
        print('')
    except Exception as e:
        print(e)
    finally:
        for f in ('.aux', '.log', '.pdf', '.png', ''):
            if os.path.isfile(fp.name + f):
                os.unlink(fp.name + f)

