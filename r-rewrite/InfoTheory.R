# This file contains functions that are related to information theory.
# Please goto the corresponding function definition for detail description.

#' list of dependency
InfoTheory.Dependency = c(
    "MiscUtility", # MiscUtility.Transform.Batch.toHistrogramBinIndices
)

#'
#' @description compute Shannon entropy
#'
#' @param prob.distri numeric vector. the input probability distribution
#'                    Assumed all entries nonnegative
#'
#' @return a numeric representing the Shannon entropy in base 2
#'
InfoTheory.Entropy.shannon = function(prob.distri) {
    return(prob.distri[prob.distri != 0] |> (\(x) x / sum(x))() |> (\(x) -sum(x * log2(x)))())
}

#'
#' @description compute Renyi entropy
#'
#' @param prob.distri numeric vector. the input probability distribution
#'                    Assumed all entries nonnegative
#'
#' @param alpha numeric, or Inf. Assumed nonnegative
#'              if alpha == 1, will call InfoTheory.Entropy.shannon() instead
#'              default: 2
#'
#' @return a numeric representing the Renyi entropy
#'
InfoTheory.Entropy.renyi = function(prob.distri, alpha = 2) {
    prob.distri = prob.distri / sum(prob.distri)
    if (alpha == 1) {
        return(InfoTheory.Entropy.shannon(prob.distri))
    } else if (is.infinite(alpha)) {
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
#' @param distri.weight numeric vector, or NULL
#'                      the weight used to compute divergence
#'                      assumed nonnegative and sums to 1
#'                      assumed of the same length as list.of.prob.distri
#'                      if NULL, will use equal weights
#'                      default: NULL
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
        InfoTheory.Entropy.shannon(
            Reduce(
                function(a, b) a + c(b, rep(0, maxProbLen - length(b))),
                Map('*', list.of.prob.distri, distri.weight),
                init = rep(0, maxProbLen),
                accumulate = FALSE
            )
        ) - sum(sapply(list.of.prob.distri, InfoTheory.Entropy.shannon) * distri.weight)
    )
}

#'
#' @description Compute the joint entropy between a list of time series
#'
#' @param list.of.time.series a list of equal length numeric vectors.
#'                            each vector is a time series on the same time interval
#'
#' @param bin.number integer.
#'                   the number of bins used to estimate probability density
#'                   ignored when is.already.discretized is TRUE
#'                   default: 10
#'
#' @param is.already.discretized boolean. determine if discretization is needed.
#'                               if FALSE, data will be discretized into unifrom bins in range
#'                               if TRUE, data will not be discretized (assuming it is already discretized)
#'                               default: FALSE
#'
#' @return a nxn matrix of the joint entropy, where n is the number of input in list.of.time.series
#'
#' @note depends on MiscUtility.Transform.Batch.toHistrogramBinIndices
#'
InfoTheory.Entropy.jointEntropy = function(list.of.time.series, bin.number = 10, is.already.discretized = FALSE) {
    n = length(list.of.time.series)
    if (!is.already.discretized) {
        list.of.time.series = MiscUtility.Transform.Batch.toHistrogramBinIndices(list.of.time.series, bin.number)
    }
    indexToCompute = combn(n, 2)
    returnMatrix = matrix(0, n, n)
    entryOfIndex = apply(
        indexToCompute, 2,
        function(idx) InfoTheory.Entropy.shannon(table(list.of.time.series[c(idx[1], idx[2])]))
    )
    returnMatrix[(indexToCompute[1, ] - 1) * n + indexToCompute[2, ]] = entryOfIndex
    returnMatrix = returnMatrix + t(returnMatrix)
    diag(returnMatrix) = sapply(list.of.time.series, function(dataSeq) InfoTheory.Entropy.shannon(table(dataSeq)))
    return(returnMatrix)
}

#'
#' @description Compute similarity by Normalized Mutural Information (NMI)
#'
#' @param list.of.time.series a list of equal length numeric vectors.
#'                            each vector is a time series on the same time interval
#'
#' @param bin.number integer
#'                   the number of bins used to estimate probability density.
#'                   ignored when is.already.discretized is TRUE
#'                   default: 10
#'
#' @param is.already.discretized boolean. determine if discretization is needed.
#'                               if FALSE, data will be discretized into unifrom bins in range
#'                               if TRUE, data will not be discretized (assuming it is already discretized)
#'                               default: FALSE
#'
#' @return a nxn matrix of the NMI, where n is the number of input in list.of.time.series
#'
#' @references
#'
#' @note depends on MiscUtility.Transform.Batch.toHistrogramBinIndices
#'
InfoTheory.Similarity.normalizedMuturalInformation = function(list.of.time.series, bin.number = 10, is.already.discretized = FALSE) {
    n = length(list.of.time.series)
    if (!is.already.discretized) {
        list.of.time.series = MiscUtility.Transform.Batch.toHistrogramBinIndices(list.of.time.series, bin.number)
    }
    # compute lower trig only
    entropyList = sapply(
        seq_len(n),
        function(stockIdx) InfoTheory.Entropy.shannon(table(list.of.time.series[[stockIdx]]))
    )
    indexToCompute = combn(n, 2)
    returnMatrix = matrix(0, n, n)
    entryOfIndex = apply(
        indexToCompute, 2,
        function(idx)
            InfoTheory.Entropy.shannon(table(list.of.time.series[c(idx[1], idx[2])])) / (entropyList[idx[1]] + entropyList[idx[2]])
    )
    returnMatrix[(indexToCompute[1, ] - 1) * n + indexToCompute[2, ]] = 2 - 2 * entryOfIndex
    returnMatrix = returnMatrix + t(returnMatrix)
    diag(returnMatrix) = 1
    return(returnMatrix)
}

#'
#' @description Compute the normalized mutural information distance matrix
#'
#' @param list.of.time.series a list of equal length numeric vectors.
#'                            each vector is a time series on the same time interval
#'
#' @param bin.number integer.
#'                   the number of bins used to estimate probability density.
#'                   ignored if is.already.discretized is TRUE
#'                   default: 10
#'
#' @param is.already.discretized boolean. determine if discretization is needed.
#'                               if FALSE, data will be discretized into unifrom bins in range
#'                               if TRUE, data will not be discretized (assuming it is already discretized)
#'                               default: FALSE
#'
#' @return a nxn matrix of the normalized mutural information distances of
#'         the stocks, where n is the number of stocks
#'
#' @note depends on MiscUtility.Transform.Batch.toHistrogramBinIndices
#'
#' @note 1 / (2 - normalized_MI_distance) = 1 - NMI_similarity / 2
#'
InfoTheory.Divergence.normalizedMIDistance = function(list.of.time.series, bin.number = 10, is.already.discretized = FALSE) {
    n = length(list.of.time.series)
    # maxData = sapply(list.of.time.series, max)
    # minData = sapply(list.of.time.series, min)
    # binSize = (maxData - minData) / binNumber
    # breakPoints = lapply(seq_len(n), function(seqIdx)seq_len(binNumber + 1) * binSize[seqIdx] + (minData[seqIdx] - binSize[seqIdx]))
    # binIndices = lapply(seq_len(n),
    #                     function(seqIdx)findInterval(list.of.time.series[[seqIdx]],
    #                                                  breakPoints[[seqIdx]],
    #                                                  all.inside = TRUE))
    if (!is.already.discretized) {
        list.of.time.series = MiscUtility.Transform.Batch.toHistrogramBinIndices(list.of.time.series, bin.number)
    }
    entropyList = sapply(
        seq_len(n),
        function(seqIdx) InfoTheory.Entropy.shannon(table(list.of.time.series[[seqIdx]]))
    )
    # compute lower trig only
    indexToCompute = combn(n, 2)
    returnMatrix = matrix(0, n, n)
    entryOfIndex = apply(
        indexToCompute, 2,
        function(idx) (entropyList[idx[1]] + entropyList[idx[2]]) /
            InfoTheory.Entropy.shannon(table(list.of.time.series[c(idx[1], idx[2])]))
    )
    returnMatrix[(indexToCompute[1, ] - 1) * n + indexToCompute[2, ]] = 2 - entryOfIndex
    returnMatrix = returnMatrix + t(returnMatrix)
    # diag(returnMatrix) = 0
    return(returnMatrix)
}

#'
#' @description convert NMI distance marix to NMI similarity matrix
#'
#' @param NMI.dist.matrix numeric matrix. each entry must be in range [0,1]
#'
#' @return the corresponding NMI similarity matrix
#'
#' @note identical to InfoTheory.Transform.NMI.similarityToDist
#'
InfoTheory.Transform.NMI.distToSimilarity = function(NMI.dist.matrix) {
    return(2 - 2 / (2 - NMI.dist.matrix))
}
#'
#' @description convert NMI similarity marix to NMI distance matrix
#'
#' @param NMI.similarity.matrix numeric matrix. each entry must be in range [0,1]
#'
#' @return the corresponding NMI distance matrix
#'
#' @note identical to InfoTheory.Transform.NMI.distToSimilarity
#'
InfoTheory.Transform.NMI.similarityToDist = function(NMI.similarity.matrix) {
    return(2 - 2 / (2 - NMI.similarity.matrix))
}

#'
#' @description compute NMI similarity with spread blurred
#'
#' @param list.of.time.series a list of equal length numeric vectors.
#'                            each vector is a time series on the same time interval
#'
#' @param bin.number integer.
#'                   the number of bins used to estimate probability density.
#'                   ignored if is.already.discretized is TRUE
#'                   default: 10
#'
#' @param is.already.discretized boolean. determine if discretization is needed.
#'                               if FALSE, data will be discretized into uniform bins in range
#'                               if TRUE, data will not be discretized (assuming it is already discretized)
#'                               default: FALSE
#'
#' @param leave.prob numeric. The probability of changing states
#'                   default: 1/4
#'
#' @return a nxn matrix of the NMI similarity of the spread distribution, where n is the number of input in list.of.time.series
#'         the values should be lower than the non-spread ones in general
#'
#' @note depends on MiscUtility.Transform.Batch.toHistrogramBinIndices
#'
InfoTheory.Similarity.spreadNormalizedMuturalInformation = function(list.of.time.series,
                                                                    bin.number = 10,
                                                                    is.already.discretized = FALSE,
                                                                    leave.prob = 1 / 4) {
    n = length(list.of.time.series)
    if (!is.already.discretized) {
        list.of.time.series = MiscUtility.Transform.Batch.toHistrogramBinIndices(list.of.time.series, bin.number)
    }
    kernelMatrix = c(leave.prob / 2, 1 - leave.prob, leave.prob / 2) %o% c(leave.prob / 2, 1 - leave.prob, leave.prob / 2)
    returnMatrix = matrix(0, n, n)
    for (i in 1:(n - 1)) {
        for (j in (i + 1):n) {
            origTable = table(list.of.time.series[c(i, j)])
            # better method for convolution?
            nR = nrow(origTable)
            nC = ncol(origTable)
            paddedTable = matrix(0, nR + 2, nC + 2)
            paddedTable[2:(nR + 1), 2:(nC + 1)] = origTable
            spreadedTable = outer(
                1:nR,
                1:nC,
                Vectorize(function(k, l) sum(paddedTable[k:(k + 2), l:(l + 2)] * kernelMatrix))
            )
            spreadedTable = spreadedTable / sum(spreadedTable)
            returnMatrix[i, j] = InfoTheory.Entropy.shannon(spreadedTable) / (
                InfoTheory.Entropy.shannon(rowSums(spreadedTable)) + InfoTheory.Entropy.shannon(colSums(spreadedTable))
            )
            returnMatrix[i, j] = 2 * (1 - returnMatrix[i, j])
        }
    }
    returnMatrix = returnMatrix + t(returnMatrix)
    diag(returnMatrix) = 1
    return(returnMatrix)
}
