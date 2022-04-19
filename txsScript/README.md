# txsScript

Here are some macro scripts I use with TeXStudio.

To use these scripts, simply copy the content of the scripts into the macro dialog.

Remember to choose macro type "script". If the scripts ask for permissions for e.g. executing external commands, just choose Allow.

## Note

Most scripts read some hard-coded config variables. These variables work on my machines.

These config variables are usually put in the very front of the script, before e.g. defining utilitary functions.

You need to change the variables manually to something that match your machine.

Note that Windows path separator `\` needs to be escaped as `\\`.

All these scripts target MS Windows OS and TeXStudio version 4.0.x. No sure if they work elsewhere.

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

Works by writing editor content to a file in `temp`.

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

### inlineToEquationStar.js

Put cursor in inline math formula (surrounded by `$`) and convert it into `equation*`

Does not check if the cursor in math mode or not

