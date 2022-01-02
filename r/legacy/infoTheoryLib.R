# this script provides the following functions:
#
# shannonEntropy
# renyiEntropy
# jensenShannonDivergence
#
# You may also want to use muturalInfoLib
# Please goto the corresponding function definition for detail description

#'
#' @description compute Shannon entropy
#'
#' @param probDistribution numeric vector. the input probability distribution
#'                         Assumed all entries nonnegative
#'
#' @return a numeric representing the Shannon entropy in base 2
#'
shannonEntropy = function(probDistribution) {
    return(probDistribution[probDistribution != 0] |> (\(x) x / sum(x))() |> (\(x) -sum(x * log2(x)))())
}

#'
#' @description compute Renyi entropy
#'
#' @param probDistribution numeric vector. the input probability distribution
#'                         Assumed all entries nonnegative
#'
#' @param alpha numeric, or Inf. Assumed nonnegative
#'              if alpha == 1, will call shannonEntropy() instead
#'              default: 2
#'
#' @return a numeric representing the Renyi entropy
#'
renyiEntropy = function(probDistribution, alpha = 2) {
    probDistribution = probDistribution / sum(probDistribution)
    if (alpha == 1) {
        return(shannonEntropy(probDistribution))
    } else if (is.infinite(alpha)){
        return(-log2(max(probDistribution)))
    } else {
        return(log2(sum(probDistribution^alpha)) / (1 - alpha))
    }
}

#'
#' @description compute the Jensen-Shannon divergence
#'
#' @param list.of.prob.distri list of numeric vector.
#'                            the input probability distributions
#'                            assumed each vector is nonnegative
#'
#' @param distriWeight numeric vector, or NULL
#'                     the weight used to compute divergence
#'                     assumed nonnegative and sums to 1
#'                     assumed of the same length as list.of.prob.distri
#'                     if NULL, will use equal weights
#'                     default: NULL
#'
#' @return a numeric representing the divergence
#'
jensenShannonDivergence = function(list.of.prob.distri, distriWeight = NULL) {
    if (is.null(distriWeight)) {
        distriWeight = rep(1 / length(list.of.prob.distri), length(list.of.prob.distri))
    }
    maxProbLen = max(sapply(list.of.prob.distri, length))
    list.of.prob.distri = lapply(list.of.prob.distri, function(x) x / sum(x))
    return(
        shannonEntropy(
            Reduce(
                function(a, b) a + c(b, rep(0, maxProbLen - length(b))),
                Map('*', list.of.prob.distri, distriWeight),
                init = rep(0, maxProbLen),
                accumulate = FALSE
            )
        ) - sum(sapply(list.of.prob.distri, shannonEntropy) * distriWeight)
    )
}
