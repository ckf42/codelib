# txsScript

Here are some macro scripts I use with TeXStudio.

To use these scripts, simply copy the content of the scripts into the macro dialog.

Remember to choose macro type "script". If the scripts ask for permissions for e.g. executing external commands, just choose Allow.

## Note

Most scripts read some hard-coded config variables. These variables work on my machines.

These config variables are usually put in the very front of the script, before e.g. defining utilitary functions.

You need to change the variables manually to something that match your machine.

Note that Windows path separator `\` needs to be escaped as `\\`.

All these scripts target MS Windows OS and TeXStudio version 4.x.x. No sure if they work elsewhere.

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

Calls `LTeX-LS` on the current editor content and prints output in TXS console.

Requires `LTeX-LS` installed first.

#### config

* `ltexVSMainPath` = `"%USERPROFILE%\\.vscode-oss\\extensions"`
    * The path to vscode plugin extension directory. `LTeX-LS` is assumed to be installed with the vscode plugin
    * Possible path:
        * VSCode: `"%USERPROFILE%\\.vscode\\extensions"`
        * VSCodium: `"%USERPROFILE%\\.vscode-oss\\extensions"`
* `ltexScriptDir` = `""`
    * The full path to the directory that contains `ltex-cli.bat`.
    * Ignored if `ltexVSMainPath` is set to some nonempty string
* `configPath` = `""`
    * Path to the json config file used by `LTeX-CLI`
* `writeToTemp` = `false`
    * Determine if we should check buffer content by writing it to a temp file.
        * If `true`, will write buffer content to a temp file (this is old behavior).
        * If `false` (default), will only check current file. Changes that are not saved will not be checked.
    * **WARNING** This script relies on undocumented (in [the official manual](https://texstudio-org.github.io/advanced.html#script-macros)) `standardOutputRead.connect`of `ProcessX` object returned from `system` command. As it is subject to change in different versions, setting `writeToTemp` to `true` may lead to unexpected result (due to the number of `system` calls in this code path). If you want to enable this, the suggestion is to step through all privilege alert (the one dialog with `Yes, allow this call` and `No, abort the call`) on the first run of each texstudio update.

### inlineToEquationStar.js

Put cursor in inline math formula (surrounded by `$`) and convert it into `equation*`

Currently supports only `$$` and not `\(\)` syntax yet

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

