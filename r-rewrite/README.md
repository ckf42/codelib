# R CodeLib Rewrite Project

This directory is for 

## Conventions

* Function
    * name must be of form `MainClass[.SubClass[...]].functionName`
        * all class names are `UpperCamelCase`
        * function name is in `lowerCamelCase`
        * only letters. no space, underscore allowed
        * dot can only be used to separate classes
    * parameters must be of form `short.and.descriptive.name`
        * abbreviations are allowed but discouraged. use only when the whole word is too long
            * usage must be consistent with all files
            * abbreviation must be unambiguous and recognizable
                * PLEASE only use those in the following list
    * comments and names for internal variables should follow usual programming conventions (i.e. not too many, not too few)
    * SUFFICIENT DOCUMENTATION IS NECESSARY
        * follow doxygen style
    * if some functions requires separate attentions (e.g. require Rcpp compile, heavy implementation, special dependency, or specialized sub-topic), they should be put in a separate file with (preferably) config variables for selective importing

## List of accepted abbreviations

The list should be ordered in dictionary order

* dist: distance
* distri: distribution
* prob: probability / probabilistic

## TODO

* general
    * consider putting everything in a package?
* documentation
    * check if current documentation style is correct
    * use external addons for writing documentation?
    * consider adding an author tag?
