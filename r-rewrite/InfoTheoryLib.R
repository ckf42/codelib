# This file contains functions that are related to information theory.
# Please goto the corresponding function definition for detail description.

#'
#' @description compute Shannon entropy
#'
#' @param probDistribution numeric vector. the input probability distribution
#'                         Assumed all entries nonnegative
#'
#' @return a numeric representing the Shannon entropy in base 2
#'
InfoTheory.Entropy.shannon = function(prob.distri) {
    return(prob.distri[prob.distri != 0] |> (\(x) x / sum(x))() |> (\(x) -sum(x * log2(x)))())
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
InfoTheory.Entropy.renyi = function(prob.distri, alpha = 2) {
    prob.distri = prob.distri / sum(prob.distri)
    if (alpha == 1) {
        return(InfoTheory.Entropy.shannon(prob.distri))
    } else if (is.infinite(alpha)){
        return(-log2(max(prob.distri)))
    } else {
        return(log2(sum(prob.distri^alpha)) / (1 - alpha))
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
InfoTheory.Divergence.jensenShannonDivergence = function(list.of.prob.distri, distri.weight = NULL) {
    if (is.null(distri.weight)) {
        distri.weight = rep(1 / length(list.of.prob.distri), length(list.of.prob.distri))
    }
    maxProbLen = max(sapply(list.of.prob.distri, length))
    list.of.prob.distri = lapply(list.of.prob.distri, function(x) x / sum(x))
    return(
        shannonEntropy(
            Reduce(
                function(a, b) a + c(b, rep(0, maxProbLen - length(b))),
                Map('*', list.of.prob.distri, distri.weight),
                init = rep(0, maxProbLen),
                accumulate = FALSE
            )
        ) - sum(sapply(list.of.prob.distri, shannonEntropy) * distri.weight)
    )
}
