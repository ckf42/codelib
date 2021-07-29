# R CodeLib Rewrite Project

This directory is for rewriting the old codelib/r with uniform format

## Usage

Source `LibImportTools.R` with `source(<path to LibImportTools.R>, echo = FALSE, chdir = TRUE)` for setup, then call `LibImportTools.import` (or its alias `codelibImport`) to import libraries

Alternatively, define a named list `.LibImportTools.SourceArgs` with names being the argument names of `LibImportTools.import` and values being the parameters before sourcing `LibImportTools.R`. This is equivalent to a `do.call` on `LibImportTools.import` with `.LibImportTools.SourceArgs`

To see what libraries are available, call `LibImportTools.getKnownLib`

Use `LibImportTools.getConfig` and `LibImportTools.setConfig` to control some behavior of Codelib

For detailed information, check the corresponding doc

## Documentation conventions

* Function
    * name must be of form `MainClass[.SubClass[...]].functionName`
        * all class names are in `UpperCamelCase`
            * main class must be consistent with the name of the file
            * if is a wrapper of other functions on batches of inputs, the last subclass must be `Batch`
        * function name is in `lowerCamelCase`
            * if return value is always a boolean, must start with `is`
        * only letters. no space, underscore allowed
        * dot can only be used to separate classes
    * parameters must be of form `short.and.descriptive.name`
        * abbreviations are allowed but discouraged. use only when the whole word is too long or when the abbreviation is easily recognized
            * usage must be consistent across all files
            * abbreviation must be unambiguous and recognizable
                * *PLEASE* only use those in the following abbreviation list
        * if parameter is expected to be a list or a vector, must begin with `list.of.` or `vect.of`, unless it is reasonable not to (e.g. structured as class)
        * if parameter is expected to be a boolean, must begin with `is.` (if describes other parameter), `to.` (if affects output) or `with.` (if affects routine)
            * should describe the effect in doc
        * if parameter is expected to be a function, must end with `.func` or `.method`
    * comments and names for internal variables should follow usual programming conventions (i.e. not too many, not too few)
        * names for internal functions on main algorithm are suggested to begin with `.internal.`
    * *ADD SUFFICIENT DOCUMENTATION*
        * follow doxygen style
    * if some functions requires separate attentions, they should be put in a separate file with (preferably) config variables for selective importing
        * applicable situations includes
            * require Rcpp compilation,
            * heavy (hundreds of lines) implementation,
            * special dependency,
            * may not be needed for usual interest,
            * or specialized sub-topic
* Variable
    * name must be of form `MainClass[.SubClass[...]].VariableName`
    * all names are in `UpperCamelCase`
    * other naming restrictions for functions also apply here
    * if the variable is meant to be a global variable (in particular those allow overwriting), the last subclass should be `Global`

## List of accepted abbreviations

The list should be ordered in dictionary order

* adj: adjacency
* algo: algorithm
* corr: correlation
* dist: distance
* distri: distribution
* info: information
* misc: miscellaneous
* msg: message
* para: parameter
* prob: probability / probabilistic
* pt: point
* rm: remove
* seq: sequence
* vect: vector

## TODO

Items in each category are list in descending order of importance

* migrate
    * move old code here
* general improvement
    * find better method of finding lib dir for `.LibImportTools.Const.LibDir`
    * auto parse available libraries by file names
    * import dependency when function is called?
    * consider putting everything in a package?
* documentation
    * clean up legacy names in doc
    * check if current documentation style format is correct
    * use external addons for writing documentation?
    * consider adding an author tag?
