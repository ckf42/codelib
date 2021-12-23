# Description

This folder contains some batch scripts.

## bookopen.bat

This is a simple interactive script I use to manage some books I have on my drive.

It queries a local file index built with option `/r`. Uses `fzf` for selecting files interactively.

You would need to set the script configs manually and build the index first. The configs are hard-coded in the script and should be located near the beginning of it.

If you want to use it with a remote drive (e.g. for fetching files from remote), you would need to set up the corresponding variables first. By default, it uses `rclone` and assumes a valid `remoteIndexName`.

## runSageTeX.bat

This script is used as a part of `TeXStudio` build command to compile TeX files that uses the `sagetex` package. It is assumed that `sagemath` is installed properly. You may need to change the `sage` path hard-coded in the script.

## mikTexFix.bat

The MiKTeX distribution on the office computer is broken with some outdated packages cannot be update without starting the MiKTeX console with admin mode (which requires admin privilege I do not have). Somehow I cannot install newer version of these packages in user mode with the console. This script tries to install those packages manually.

Running / double clicking on this batch file should fix the issue. Haven't test on other computers though.

## pipup.bat

`pip list -o` with `fzf` for updating python packages. Assumes `fzf` installed

