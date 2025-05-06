# txsScript

Here are some macro scripts I use with TeXStudio.

To use these scripts, simply copy the ~~content of the scripts into the macro dialog~~ files into the `macro` directory. (You *may* need to rename the files as `Macro_*.txsMacro` for texstudio to see them, have not checked.)

~~Remember to choose macro type "script".~~ If the scripts ask for permissions for e.g. executing external commands, just choose `Allow` (at your own risk).

## Note

Most scripts read some hard-coded config variables. These variables Work On My Machines (TM).

These config variables are usually put in the very front of the script, before e.g. defining util functions.

You may need to change the variables manually to something that work on your machine.

Note that Windows path separator `\` needs to be escaped as `\\`.

All these scripts target MS Windows OS and TeXStudio version 4.x.x. Not sure if they work elsewhere.

## Content

### utils.js

Some common utilities

### latexindent.js

Calls `latexindent` on the current editor content and replace it with the formatted output.

Does not work on non-ascii content (because of latexindent).

Works by writing editor content to a file in `temp`.

#### config

* `texindentPath` = `"latexindent.exe"`
    * Full path to the `latexindent` executable
* `settingYamlFilePath` = `"latexindent-settings.yaml"`
    * Full path to the config yaml used by `latexindent`
* `texindentPara` = `"-s -m"`
    * Parameters passed to `latexindent`

### ltex.js

Calls `LTeX-LS` on the current editor content and prints output in a new editor buffer (also TXS console).

If the cursor has a selection, checks only the selected part.

Requires `LTeX-LS`.

#### config

* `ltexVSMainPath` = `"%USERPROFILE%\\.vscode-oss\\extensions"`
    * The path to vscode plugin extension directory. `LTeX-LS` is assumed to be installed with the vscode plugin
    * Possible path:
        * VSCode: `"%USERPROFILE%\\.vscode\\extensions"`
        * VSCodium: `"%USERPROFILE%\\.vscode-oss\\extensions"`
* `configPath` = `""`
    * Path to the json config file used by `LTeX-CLI`
* `ltexScriptPath` = `""`
    * The full path to the `ltex-cli.bat`. Set this one if you have LTeX as a standalone (instead of a vscode plugin)
    * Ignored if `ltexVSMainPath` is set to some nonempty string
* `writeToTemp` = `false`
    * Determine if we should check buffer content by writing it to a temp file.
        * If `true`, will write buffer content to a temp file (this is old behavior).
        * If `false` (default), will only check current saved file. Changes that are not saved will not be checked (as they are invisible).
    * **WARNING** This script relies on undocumented (in [the official manual](https://texstudio-org.github.io/advanced.html#script-macros)) `standardOutputRead.connect` of `ProcessX` object returned from `system` command. As it may be subject to change in different versions, setting `writeToTemp` to `true` may lead to unexpected result (due to the number of `system` calls in this code path). If you want to enable this, the suggestion is to step through all privilege alert (the one dialog with `Yes, allow this call` and `No, abort the call`) on the first run after each texstudio update.
    * **NOTE** If the cursor has a selection, the setting is *ignored* and we *always* write to a temp file (effectively setting `writeToTemp = true`).

### inlineToEquationStar.js

Put cursor in inline math formula (surrounded by `\(` and `\)`) and convert it into `equation*`

Supports only `\(\)` syntax (for `$$` syntax, convert it to use brackets first).

Does not check if the cursor in math mode or not

### toggleCustomCommentStyle.js

Toggle comment on the line(s) selected

Allows customization on comment style

If multiple lines are selected, action determined on whether the first line is commented

#### config

* `commentSignAdd` = `"% "`
    * The string used for commenting lines
* `commentSignRemoveRegex` = `new RegExp("^" + commentSignAdd)`
    * The regex used for matching commented line
    * Default to the same string as commentSignAdd

