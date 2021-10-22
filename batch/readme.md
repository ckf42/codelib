# Description

This folder contains some batch scripts. 

## bookopen.bat

This is a simple interactive script to manage the books I have. 

It works by storing the file index in a file and querying the index to speed up the loading. It also uses `fzf` for its selection interface.

You would need to set the script configs manualy. The configs are hard-coded in the script and should be at the beginning of it.

If you want to use with a remote drive, you would need to set up `rclone` first. It assumes a index file `remoteIndexName`.

## runSageTeX.bat

This script is used in coorpation with `TeXStudio` to compile TeX files that uses the `sagetex` package. It is assumed that `sagemath` is installed. You need to change the `sage` path written in the script.

