def previewInTerm(graphicObj, suffix='.png', *args, **kwargs):
    """
    graphicObj: sage.plot.graphics.Graphics object, must have save_image method
    suffix: format of the output image. Affects how the image is obtained. See doc of save_image
    *args, **kwargs: directly pass to save_image
    """

    import pathlib
    import shutil
    import subprocess
    import tempfile

    realTmpPath = '/tmp'
    if shutil.which('cygpath') is not None:
        realTmpPath = subprocess.run(
                ['cygpath', '-w', '/tmp'],
                capture_output=True,
                text=True).stdout.strip()
    try:
        fp = tempfile.NamedTemporaryFile(
                'wt',
                delete=False,
                encoding='utf-8',
                prefix='previewInTerm_',
                suffix=suffix)
        fpPath = fp.name.replace('/tmp', realTmpPath, 1)
        graphicObj.save_image(fpPath, *args, **kwargs)  # only take str path name
        fp.close()
        pngPath = pathlib.Path(fp.name)
        fContent = b''
        with pngPath.open('rb') as imgF:
            fContent = imgF.read()
        subprocess.run(['wezterm', 'imgcat'], input=fContent)
    except Exception as e:
        print(e)
    finally:
        if pngPath.is_file():
            pngPath.unlink()

