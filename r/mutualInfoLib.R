# this script provides the following functions:
#
# transform_to_bin_indices
# transform_to_bin_indices_list
# joint_entropy
# NMI_similarity
# normalized_MI_distance
# NMI_dist_to_NMI_sim
# NMI_sim_to_NMI_dist
#
# Please goto the corresponding function definition for detail description

#'
#' @description discretize the data
#'
#' @param dataSeq numeric vector
#'
#' @param binNumber the number of bins used to discretize the data
#'
#' @param removeBeyondMean boolean, or a nonnegative numeric.
#'                         if numeric, all data beyond [m - s * removeBeyondMean, m + s * removeBeyondMean]
#'                             will be counted as the nearest endpoint
#'                             where m is the mean of dataSeq
#'                                   s is the sample standard derivation of dataSeq
#'                         if FALSE, the whole range is used
#'                         TRUE is an alias of removeBeyondMean = 3
#'                         default: FALSE
#'
#' @param removeOutlier boolean. determine if outliers should be remove with the
#'                      same method as removeBeyondMean
#'                      outliers are data deyond range [Q1 - 1.5 * (Q3 - Q1), Q3 + 1.5 * (Q3 - Q1)]
#'                      override removeBeyondMean
#'                      default: FALSE
#'
#' @return a integer vector of the same length as dataSeq where each element
#'         is replaced with the index of its bin
#'         The range of the data are divided into binNumber bins of identical size
#'
transform_to_bin_indices = function(dataSeq, binNumber, removeBeyondMean = FALSE, removeOutlier = FALSE){
    maxDataRange = 0
    minDataRange = 0
    if (isTRUE(removeBeyondMean)){
        removeBeyondMean = 3
    }
    if (isFALSE(removeBeyondMean)){
        maxDataRange = max(dataSeq)
        minDataRange = min(dataSeq)
    } else {
        meanData = mean(dataSeq)
        dataRadius = removeBeyondMean * sd(dataSeq) * (1 - 1 / length(dataSeq))
        maxDataRange = meanData + dataRadius
        minDataRange = meanData - dataRadius
    }
    if (removeOutlier){
        dataQuantile = quantile(dataSeq, probs = c(0.25, 0.75), names = FALSE)
        dataRadius = 1.5 * (dataQuantile[2] - dataQuantile[1])
        maxDataRange = dataQuantile[2] + dataRadius
        minDataRange = dataQuantile[1] - dataRadius
    }
    binSize = (maxDataRange - minDataRange) / binNumber
    breakPoints = seq_len(binNumber + 1) * binSize + (minDataRange - binSize)
    return(findInterval(dataSeq, breakPoints, all.inside = TRUE))
}

#'
#' @description discretize a list of data
#'
#' @param listOfData a list of numeric vectors
#'
#' @param binNumber the number of bins used to discretize the data
#'
#' @param removeBeyondMean boolean, or a nonnegative numeric.
#'                         if numeric, all data beyond [m - s * removeBeyondMean, m + s * removeBeyondMean]
#'                             will be counted as the nearest endpoint
#'                             where m is the mean of dataSeq
#'                                   s is the sample standard derivation of dataSeq
#'                         if FALSE, the whole range is used
#'                         TRUE is an alias of removeBeyondMean = 3
#'                         default: FALSE
#'
#' @param removeOutlier boolean. determine if outliers should be remove with the
#'                      same method as removeBeyondMean
#'                      outliers are data deyond range [Q1 - 1.5 * (Q3 - Q1), Q3 + 1.5 * (Q3 - Q1)]
#'                      override removeBeyondMean
#'                      default: FALSE
#'
#' @return a list of numeric vectors, each vector is transformed with transform_to_bin_indices
#'
#' @note wrapper of transform_to_bin_indices on list
#'
transform_to_bin_indices_list = function(listOfData, binNumber, removeBeyondMean = FALSE, removeOutlier = FALSE){
    return(lapply(listOfData, function(dataSeq)transform_to_bin_indices(dataSeq, binNumber, removeBeyondMean, removeOutlier)))
}

#'
#' @description Compute the joint entropy between a list of time series
#'
#' @param listOfSeries a list of equal length numeric vectors.
#'                      each vector is a time series on the same time interval
#'
#' @param binNumber a integer. the number of bins used to estimate probability
#'                  density. default 10
#'
#' @param alreadyDiscretized boolean. determine if discretization is needed.
#'                           if FALSE, data will be discretized into unifrom bins in range
#'                           if TRUE, data will not be discretized (assuming it is already discretized)
#'                           default: FALSE
#'
#' @return a nxn matrix of the joint entropy, where n is the number of input in listOfSeries
#'
joint_entropy = function(listOfSeries, binNumber = 10, alreadyDiscretized = FALSE){
    shannonEntropy = function(probDistribution){
        probDistribution = probDistribution[probDistribution != 0]
        return(-sum(probDistribution * log2(probDistribution)))
    }
    n = length(listOfSeries)
    nDays = length(listOfSeries[[1]])
    if (!alreadyDiscretized){
        listOfSeries = lapply(listOfSeries, function(dataSeq)transform_to_bin_indices(dataSeq, binNumber))
    }
    entropyList = sapply(seq_len(n),
                         function(seqIdx)shannonEntropy(table(listOfSeries[[seqIdx]]) / nDays))
    indexToCompute = combn(n, 2)
    returnMatrix = matrix(0, n, n)
    entryOfIndex = apply(indexToCompute, 2,
                         function(idx)shannonEntropy(table(listOfSeries[c(idx[1], idx[2])]) / nDays))
    returnMatrix[(indexToCompute[1, ] - 1) * n + indexToCompute[2, ]] = entryOfIndex
    returnMatrix = returnMatrix + t(returnMatrix)
    diag(returnMatrix) = sapply(listOfSeries, function(dataSeq)shannonEntropy(table(dataSeq) / nDays))
    return(returnMatrix)
}

#'
#' @description Compute similarity by Normalized Mutural Information (NMI)
#'
#' @param listOfSeries a list of equal length numeric vectors.
#'                      each vector is a time series on the same time interval
#'
#' @param binNumber a integer. the number of bins used to estimate probability
#'                  density. default 10
#'
#' @param alreadyDiscretized boolean. determine if discretization is needed.
#'                           if FALSE, data will be discretized into unifrom bins in range
#'                           if TRUE, data will not be discretized (assuming it is already discretized)
#'                           default: FALSE
#'
#' @return a nxn matrix of the NMI, where n is the number of input in listOfSeries
#'
#' @references
#'
NMI_similarity = function(listOfSeries, binNumber = 10, alreadyDiscretized = FALSE){
    shannonEntropy = function(probDistribution){
        probDistribution = probDistribution[probDistribution != 0]
        return(-sum(probDistribution * log2(probDistribution)))
    }
    n = length(listOfSeries)
    nDays = length(listOfSeries[[1]])
    if (!alreadyDiscretized){
        listOfSeries = lapply(listOfSeries, function(dataSeq)transform_to_bin_indices(dataSeq, binNumber))
    }
    # compute lower trig only
    entropyList = sapply(seq_len(n),
                         function(stockIdx)shannonEntropy(table(listOfSeries[[stockIdx]]) / nDays))
    indexToCompute = combn(n, 2)
    returnMatrix = matrix(0, n, n)
    entryOfIndex = apply(indexToCompute, 2,
                         function(idx)shannonEntropy(table(listOfSeries[c(idx[1], idx[2])]) / nDays) /
                                      (entropyList[idx[1]] + entropyList[idx[2]]))
    returnMatrix[(indexToCompute[1, ] - 1) * n + indexToCompute[2, ]] = 2 - 2 * entryOfIndex
    returnMatrix = returnMatrix + t(returnMatrix)
    diag(returnMatrix) = 1
    return(returnMatrix)
}

#'
#' @description Compute the normalized mutural information distance matrix
#'
#' @param listOfSeries a list of equal length numeric vectors.
#'                      each vector is a time series on the same time interval
#'
#' @param binNumber a integer.
#'                  the number of bins used to estimate probability density.
#'                  default: 10
#'
#' @param alreadyDiscretized boolean. determine if discretization is needed.
#'                           if FALSE, data will be discretized into unifrom bins in range
#'                           if TRUE, data will not be discretized (assuming it is already discretized)
#'                           default: FALSE
#'
#' @return a nxn matrix of the normalized mutural information distances of
#'         the stocks, where n is the number of stocks
#'
#' @note 1 / (2 - normalized_MI_distance) = 1 - NMI_similarity / 2
#'
normalized_MI_distance = function(listOfSeries, binNumber = 10, alreadyDiscretized = FALSE){
    shannonEntropy = function(probDistribution){
        probDistribution = probDistribution[probDistribution != 0]
        return(-sum(probDistribution * log2(probDistribution)))
    }
    n = length(listOfSeries)
    nDays = length(listOfSeries[[1]])
    # maxData = sapply(listOfSeries, max)
    # minData = sapply(listOfSeries, min)
    # binSize = (maxData - minData) / binNumber
    # breakPoints = lapply(seq_len(n), function(seqIdx)seq_len(binNumber + 1) * binSize[seqIdx] + (minData[seqIdx] - binSize[seqIdx]))
    # binIndices = lapply(seq_len(n),
    #                     function(seqIdx)findInterval(listOfSeries[[seqIdx]],
    #                                                  breakPoints[[seqIdx]],
    #                                                  all.inside = TRUE))
    if (!alreadyDiscretized){
        listOfSeries = lapply(listOfSeries, function(dataSeq)transform_to_bin_indices(dataSeq, binNumber))
    }
    entropyList = sapply(seq_len(n),
                         function(seqIdx)shannonEntropy(table(listOfSeries[[seqIdx]]) / nDays))
    # compute lower trig only
    indexToCompute = combn(n, 2)
    returnMatrix = matrix(0, n, n)
    entryOfIndex = apply(indexToCompute, 2,
                         function(idx)(entropyList[idx[1]] + entropyList[idx[2]]) /
                                      shannonEntropy(table(listOfSeries[c(idx[1], idx[2])]) / nDays))
    returnMatrix[(indexToCompute[1, ] - 1) * n + indexToCompute[2, ]] = 2 - entryOfIndex
    returnMatrix = returnMatrix + t(returnMatrix)
    # diag(returnMatrix) = 0
    return(returnMatrix)
}


#'
#' @description convert NMI distance marix to NMI similarity matrix
#'
#' @param NMIDistMatrix numeric matrix. each entry must be in range [0,1]
#'
#' @return the corresponding NMI similarity matrix
#'
#' @note identical to NMI_sim_to_NMI_dist
#'
NMI_dist_to_NMI_sim = function(NMIDistMatrix){
    return(2 - 2 / (2 - NMIDistMatrix))
}
#'
#' @description convert NMI similarity marix to NMI distance matrix
#'
#' @param NMISimMatrix numeric matrix. each entry must be in range [0,1]
#'
#' @return the corresponding NMI distance matrix
#'
#' @note identical to NMI_dist_to_NMI_sim
#'
NMI_sim_to_NMI_dist = function(NMISimMatrix){
    return(2 - 2 / (2 - NMISimMatrix))
}

#'
#' @description compute NMI similarity with spreaded blurred
#'
#' @param listOfSeries a list of equal length numeric vectors.
#'                      each vector is a time series on the same time interval
#'
#' @param binNumber a integer.
#'                  the number of bins used to estimate probability density.
#'                  default: 10
#'
#' @param alreadyDiscretized boolean. determine if discretization is needed.
#'                           if FALSE, data will be discretized into unifrom bins in range
#'                           if TRUE, data will not be discretized (assuming it is already discretized)
#'                           default: FALSE
#'
#' @param leaveProb numeric. The probability of changing states
#'                  default: 1/4
#'
#' @return a nxn matrix of the NMI similarity of the spreaded distribution, where n is the number of input in listOfSeries
#'         the values should be lower than the un-spreaded ones in general
#'
spread_NMI_similarity = function(listOfSeries, binNumber = 10, alreadyDiscretized = FALSE, leaveProb = 1/4){
    shannonEntropy = function(probDistribution){
        probDistribution = probDistribution[probDistribution != 0]
        return(-sum(probDistribution * log2(probDistribution)))
    }
    n = length(listOfSeries)
    if (!alreadyDiscretized){
        listOfSeries = lapply(listOfSeries, function(dataSeq)transform_to_bin_indices(dataSeq, binNumber))
    }
    kernelMatrix = c(leaveProb / 2, 1 - leaveProb, leaveProb / 2) %o% c(leaveProb / 2, 1 - leaveProb, leaveProb / 2)
    returnMatrix = matrix(0, n, n)
    for (i in 1 : (n-1)){
        for (j in (i+1) : n){
            origTable = table(listOfSeries[c(i, j)])
            # better method for convolution?
            nR = nrow(origTable)
            nC = ncol(origTable)
            paddedTable = matrix(0, nR + 2, nC + 2)
            paddedTable[2:(nR + 1), 2:(nC + 1)] = origTable
            spreadedTable = outer(1:nR, 1:nC, Vectorize(function(k, l)sum(paddedTable[k:(k+2), l:(l+2)] * kernelMatrix)))
            spreadedTable = spreadedTable / sum(spreadedTable)
            returnMatrix[i, j] = shannonEntropy(spreadedTable) / (shannonEntropy(rowSums(spreadedTable)) + shannonEntropy(colSums(spreadedTable)))
            returnMatrix[i, j] = 2 * (1 - returnMatrix[i, j])
        }
    }
    returnMatrix = returnMatrix + t(returnMatrix)
    diag(returnMatrix) = 1
    return(returnMatrix)
}
