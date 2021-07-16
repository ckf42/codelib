# R CodeLib Rewrite Project

This directory is for rewriting the old codelib/r with unifrom format

## Conventions

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
        * abbreviations are allowed but discouraged. use only when the whole word is too long
            * usage must be consistent with all files
            * abbreviation must be unambiguous and recognizable
                * PLEASE only use those in the following list
        * if parameter is expected to be a list or a vector, must begin with `list.of.` or `vect.of`, unless it is reasonable not to (e.g. structured as class)
        * if parameter is expected to be a boolean, must begin with `is.` (if describes other parameter), `to.` (if affects output) or `with.` (if affects routine)
        * if parameter is expected to be a function, must end with `.func` or `.method`
    * comments and names for internal variables should follow usual programming conventions (i.e. not too many, not too few)
        * names for internal functions are suggested to begin with `.internal.`
    * SUFFICIENT DOCUMENTATION IS NECESSARY
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
* seq: sequence
* vect: vector

## TODO

* implementation
    * dependency checker / auto import dependency?
    * change `to.` to `with.` to some boolean parameters
* general
    * consider putting everything in a package?
* documentation
    * check if current documentation style is correct
    * use external addons for writing documentation?
    * consider adding an author tag?
