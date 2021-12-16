# Description

Some python scripts.

Most scripts accept commandline arguments. For the details on these arguments, consult the `--help` argument

## bblToBib.py

I forgor

## expandMdMathMacro.py

Read a `Markdown` file that uses math macros (stored as `json` format) and transform to plain math `KaTeX` math commands. Also allow transforming math commands with image links, or transform the file into a `HTML` file that can be rendered with `MathML` or GitHub-previewable `IPython` notebook.

Requires `pandoc` in path for file format transforming.

## extractBib.py

Extract entries in a `bib` file that are cited in the given `TeX` file and put them to `stdout` or put them in a separete file.

## extractUMM.py

Extract commands from my `usefulmathmacro` macros that are used in a given `TeX` file and output them to `stdout` or embed the commands back in the file.

## fetchDocMetadata.py

Fetch the metadata of a document identifier and display its metadata in `stdout`. Cut-down version of the same functionality in `shdl`. Useful for debugging `shdl`

Currently only support `doi`, `arxiv`, and `jstor`.

## ipythonInitScript.py

Import some python packages in `ipython` for scicomp. Just run the script after `ipython` is initiated.

## musicKeyboard*.py

A mini project I did. Use your keyboard to play some musics. Dropped because of NKRO.

Built upon `personalPylib_audio.py`. Left-hand version imports it directly.

## npPylib.py

Same as `personalPylib.py` but relies on `numpy`

## peperNameNormalizer.py

Same as `fetchDocMetadata.py` but for geting the `autoname`. Also for debugging `shdl`

## personalPylib_audio.py

A simple python I use to generate some sounds. Uses `numpy`

## personalPylib.py

Some python scripts I have written, for general purposes. May be used in other scripts.

## wormholeQR.py

Read the `wormhole send` code and generate a QR code that can be read by `wormhole-william`. Use for transferring files from computer to cellphone with `wormhole(-william)`
