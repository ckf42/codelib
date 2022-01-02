# This file contains utility functions.
# Please goto the corresponding function definition for detail description.

# preprocess - dependency registering
.LibImportTools.Global.Dependency = get0(".LibImportTools.Global.Dependency")

#'
#' @description discretize the data
#'
#' @param data.seq numeric vector
#'
#' @param bin.number the number of bins used to discretize the data
#'
#' @param to.remove.beyond.mean boolean, or a nonnegative numeric.
#'                              if numeric, all data beyond [m - s * to.remove.beyond.mean, m + s * to.remove.beyond.mean]
#'                                  will be counted as the nearest endpoint
#'                                  where m is the mean of data.seq
#'                                        s is the sample standard derivation of data.seq
#'                              if FALSE, the whole range is used
#'                              TRUE is an alias of to.remove.beyond.mean = 3
#'                              default: FALSE
#'
#' @param to.remove.outlier boolean. determine if outliers should be remove with the
#'                          same method as to.remove.beyond.mean
#'                          outliers are data deyond range [Q1 - 1.5 * (Q3 - Q1), Q3 + 1.5 * (Q3 - Q1)]
#'                          higher precedence than to.remove.beyond.mean
#'                          default: FALSE
#'
#' @return a integer vector of the same length as data.seq where each element
#'         is replaced with the index of its bin
#'         The range of the data are divided into bin.number bins of identical size
#'
MiscUtility.Transform.toHistogramBinIndices = function(data.seq, bin.number, to.remove.beyond.mean = FALSE, to.remove.outlier = FALSE) {
    maxDataRange = 0
    minDataRange = 0
    if (isTRUE(to.remove.beyond.mean)) {
        to.remove.beyond.mean = 3
    }
    if (isFALSE(to.remove.beyond.mean)) {
        maxDataRange = max(data.seq)
        minDataRange = min(data.seq)
    } else {
        meanData = mean(data.seq)
        dataRadius = to.remove.beyond.mean * sd(data.seq) * (1 - 1 / length(data.seq))
        maxDataRange = meanData + dataRadius
        minDataRange = meanData - dataRadius
    }
    if (to.remove.outlier) {
        dataQuantile = quantile(data.seq, probs = c(0.25, 0.75), names = FALSE)
        dataRadius = 1.5 * (dataQuantile[2] - dataQuantile[1])
        maxDataRange = dataQuantile[2] + dataRadius
        minDataRange = dataQuantile[1] - dataRadius
    }
    binSize = (maxDataRange - minDataRange) / bin.number
    breakPoints = seq_len(bin.number + 1) * binSize + (minDataRange - binSize)
    return(findInterval(data.seq, breakPoints, all.inside = TRUE))
}

#'
#' @description discretize a list of data
#'
#' @param list.of.data.seq a list of numeric vectors
#'
#' @param list.of.data.seq the number of bins used to discretize the data
#'
#' @param to.remove.beyond.mean boolean, or a nonnegative numeric.
#'                         if numeric, all data beyond [m - s * to.remove.beyond.mean, m + s * to.remove.beyond.mean]
#'                             will be counted as the nearest endpoint
#'                             where m is the mean of dataSeq
#'                                   s is the sample standard derivation of dataSeq
#'                         if FALSE, the whole range is used
#'                         TRUE is an alias of to.remove.beyond.mean = 3
#'                         default: FALSE
#'
#' @param to.remove.outlier boolean. determine if outliers should be remove with the
#'                      same method as to.remove.beyond.mean
#'                      outliers are data deyond range [Q1 - 1.5 * (Q3 - Q1), Q3 + 1.5 * (Q3 - Q1)]
#'                      higher precedence than to.remove.beyond.mean
#'                      default: FALSE
#'
#' @return a list of numeric vectors, each vector is transformed with transform_to_bin_indices
#'
#' @note wrapper of transform_to_bin_indices on list
#'
MiscUtility.Transform.Batch.toHistogramBinIndices = function(list.of.data.seq,
                                                             bin.number,
                                                             to.remove.beyond.mean = FALSE,
                                                             to.remove.outlier = FALSE) {
    return(lapply(
        list.of.data.seq,
        function(dataSeq) MiscUtility.Transform.toHistogramBinIndices(
            dataSeq,
            bin.number,
            to.remove.beyond.mean,
            to.remove.outlier
        )
    ))
}

#'
#' @description convert correlation matrix to distance matrix
#'
#' @param corr.matrix numeric square matrix. input correlation matrix C
#'
#' @return the distance matrix computed as sqrt(2(1-C))
#'
#' @note inverse of MiscUtility.Transform.distToCorr
#'
MiscUtility.Transform.corrToDist = function(corr.matrix) {
    return(sqrt(2 * (1 - corr.matrix)))
}

#'
#' @description convert distance matrix to correlation matrix
#'
#' @param dist.matrix numeric square matrix. input distance matrix D
#'
#' @return the correlation matrix computed as 1-D^2/2
#'
#' @note inverse of MiscUtility.Transform.corrToDist
#'
MiscUtility.Transform.distToCorr = function(dist.matrix) {
    return(1 - dist.matrix * dist.matrix / 2)
}

#'
#' @description Compute the Pearson correlation distance matrix
#'
#' @param list.of.time.series a list of equal length numeric vectors.
#'                            each vector is a time series on the same time interval
#'
#' @param segment.length integer, or Inf.
#'                       segmentation parameter. The time length concerned
#'                       each matrix is computed with only tau data points
#'                       if segment.length <= 2, will return a full-1 matrix
#'                       default: Inf
#'
#' @return a list of Pearson correlation distance matrix
#'         each matrix is named according to the names in list.of.time.series
#'         if segment.length is at least the length of the series, only one matrix is returned
#'
MiscUtility.Statistics.serialPearsonCorrMatrix = function(list.of.time.series, segment.length = Inf) {
    n = length(list.of.time.series)
    timeLen = length(list.of.time.series[[1]])
    segment.length = min(segment.length, timeLen)
    if (segment.length == timeLen) {
        if (segment.length <= 2) {
            return(matrix(1, n, n, dimnames = replicate(2, names(list.of.time.series), simplify = FALSE)))
        } else {
            corrMatrix = matrix(unlist(list.of.time.series), ncol = length(list.of.time.series), byrow = FALSE)
            corrMatrix = cor(corrMatrix, use = 'all.obs', method = 'pearson')
            colnames(corrMatrix) = rownames(corrMatrix) = names(list.of.time.series)
            return(corrMatrix)
        }
    } else {
        resCount = (timeLen + segment.length - 1) %/% segment.length
        res = replicate(resCount, NA, simplify = FALSE)
        for (idx in seq_len(resCount)) {
            res[[idx]] = MiscUtility.Statistics.serialPearsonCorrMatrix(
                lapply(
                    list.of.time.series,
                    function(x) x[(1 + (idx - 1) * segment.length):min(idx * segment.length, timeLen)]
                ), Inf
            )
        }
        return(res)
    }
}

#'
#' @description compute the partial correlation matrix
#'
#' @param corr.matrix numeric matrix. the input correlation matrix
#'
#' @param regularization.para boolean, or a numeric. parameter for regularization
#'                            TRUE is alias of 0.2, FALSE is alias of 0
#'                            default: 0
#'
#' @param mix.matrix NULL, or numeric matrix. used to mix with corr.matrix
#'                   if NULL, no mixing (same as mix.matrix = 0)
#'                   otherwise assumed to have the same shape as corr.matrix
#'                   default: NULL
#'
#' @param mix.para numeric. the coefficient for mixing
#'                 default: 0
#'
#' @return the partial correlation matrix.
#'         if regularization.para is not 0, the convex combination of corr.matrix
#'             and identity matrix is used to keep diagonal of precision nonnegative
#'         if mix.matrix is not NULL and mix.para is not 0, mix.matrix will be added before regularizing
#'
MiscUtility.Statistics.partialCorr = function(corr.matrix, regularization.para = 0, mix.matrix = NULL, mix.para = 0) {
    if (isTRUE(regularization.para)) {
        regularization.para = 0.2
    } else if (isFALSE(regularization.para)) {
        regularization.para = 0
    }
    if (!is.null(mix.matrix) && mix.para != 0) {
        if (any(dim(corr.matrix) != dim(mix.matrix))) {
            stop("in partial_corr, shape of corrMatrix does not match shape of mixMatrix")
        }
        corr.matrix = (1 - mix.para) * corr.matrix + mix.para * mix.matrix
    }
    if (regularization.para != 0) {
        corr.matrix = (1 - regularization.para) * corr.matrix + regularization.para * diag(nrow(corr.matrix))
    }
    precisionMatrix = MASS::ginv(corr.matrix)
    precisionDiagSqrt = sqrt(diag(precisionMatrix))
    return(-precisionMatrix / outer(precisionDiagSqrt, precisionDiagSqrt))
}


#'
#' @description compute partial correlation matrix from distance matrix and transform into distance matrix
#'
#' @param dist.matrix numeric matrix. the input distance matrix
#'
#' @param regularization.para boolean, or a numeric. passed to partial_corr directly
#'                            default: 0
#'
#' @param mix.matrix NULL, or numeric matrix. used to mix with corr.matrix
#'                   if NULL, no mixing (same as mix.matrix = 0)
#'                   otherwise assumed to have the same shape as corr.matrix
#'                   default: NULL
#'
#' @param mix.para numeric. the coefficient for mixing
#'                 default: 0
#'
#' @return a numeric matrix. the distance matrix of the partial correlation matrix.
#'
#' @note wrapper of partial_corr for distance matrix
#'
MiscUtility.Statistics.partialCorrDist = function(dist.matrix, regularization.para = 0, mix.matrix = NULL, mix.para = 0) {
    return(MiscUtility.Transform.corrToDist(
        MiscUtility.Statistics.partialCorr(
            MiscUtility.Transform.distToCorr(dist.matrix),
            regularization.para,
            mix.matrix,
            mix.para
        )
    ))
}

#'
#' @description normalize a vector
#'
#' @param raw.seq numeric vector. the vector to be normalized on
#'
#' @param to.zscore boolean. determine how to normalize raw.seq
#'                  if TRUE, reduce to Z-score
#'                  if FALSE, linear scale to [-1, 1]
#'                  default: TRUE
#'
#' @return a normalized numeric vector of the same length as raw.seq
#'
MiscUtility.Transform.linearNormalize = function(raw.seq, to.zscore = TRUE) {
    if (to.zscore) {
        return((raw.seq - mean(raw.seq)) / sd(raw.seq))
    } else {
        mx = max(raw.seq)
        mn = min(raw.seq)
        return((raw.seq - mn) / (mx - mn))
    }
}

#'
#' @description normalize a vector
#'
#' @param list.of.raw.seq list of numeric vectors. the vectors to be normalized on
#'
#' @param to.zscore boolean. determine how to normalize raw.seq
#'                  if TRUE, reduce to Z-score
#'                  if FALSE, linear scale to [-1, 1]
#'                  default: TRUE
#'
#' @return a list of normalized numeric vectors
#'
#' @note wrapper of MiscUtility.Transform.linearNormalize
#'
MiscUtility.Transform.Batch.linearNormalize = function(list.of.raw.seq, to.zscore = TRUE) {
    return(lapply(
        list.of.raw.seq,
        function(x) MiscUtility.Transform.linearNormalize(x, to.zscore = to.zscore)
    ))
}


#'
#' @description compute the log return
#'
#' @param raw.seq a numeric vector, represent the time sequence
#'
#' @return a numeric vector recording the log return of raw.seq.
#'         Of length length(raw.seq) - 1
#'
MiscUtility.Transform.logReturn = function(raw.seq) {
    l = length(raw.seq)
    return(log(raw.seq[2:l] / raw.seq[1:(l - 1)]))
}

#'
#' @description compute the log return
#'
#' @param list.of.raw.seq a list of numeric vector.
#'                        each representing a time sequence on the same time period
#'
#' @return a list of numeric vectors recording the log return of the sequences.
#'
MiscUtility.Transform.Batch.logReturn = function(list.of.raw.seq) {
    return(lapply(list.of.raw.seq, MiscUtility.Transform.logReturn))
}


#' @description linearly interpolate a time series
#'
#' @param data.seq numeric vector. the time series to be interpolate
#'
#' @param add.pt.count integer. the number of points to be inserted between two points
#'                     in data.seq
#'
#' @return a numeric of interpolated series, of length (length(data.seq) - 1) * (add.pt.count + 1) + 1
MiscUtility.Transform.linearInterpolate = function(data.seq, add.pt.count = 1) {
    n = length(data.seq)
    return(c(
        unlist(lapply(
            seq_len(n - 1),
            function(idx) data.seq[idx] + 0:add.pt.count * (data.seq[idx + 1] - data.seq[idx]) / (add.pt.count + 1)
        )),
        data.seq[n]
    ))
}

#'
#' @description compute the l^\infty norm
#'
#' @param var.1 numeric vector/matrix
#'
#' @param var.2 numeric vector/matrix.
#'              assumed to have (or can be convert to) same shape as input1
#'              default: 0
#'
#' @return the l^\infty norm of var.1 - var.2
#'         if var.2 is not given, the l^\infty norm of var.1
#'
MiscUtility.Norm.lInf = function(var.1, var.2 = 0) {
    return(max(abs(var.1 - var.2)))
}

#'
#' @description cutoff the matrix according to the entries
#'
#' @param target.matrix numeric matrix.
#'
#' @param weight.threshold numeric. the threshold value to transform values
#'
#' @param is.equal.or.below boolean. determine if entries same as threshold is counted as below threshold
#'                          if TRUE, entries with the same value as threshold will be replaced as lower.cap.threshold
#'                          if FALSE, entries with the same value as threshold will be replaced as upper.cap.threshold
#'
#' @param lower.cap.threshold numeric. what below-threshold values should be transformed to
#'                            default: 0
#'
#' @param upper.cap.threshold numeric. what equal-and-above-threshold values should be transformed to
#'                            default: 1
#'
#' @return a numeric matrix of the same shape as target.matrix,
#'             but every entry below weight.threshold is replaced with lower.cap.threshold,
#'             every entry equal or above is replaced with upper.cap.threshold
#'
#' @note wrapper of ifelse
#'
# TODO more generic
#
MiscUtility.Transform.matrixCutOff = function(target.matrix,
                                              weight.threshold,
                                              is.equal.or.below,
                                              lower.cap.threshold = 0,
                                              upper.cap.threshold = 1) {
    matrixMask = (target.matrix < weight.threshold)
    if (is.equal.or.below) {
        matrixMask = matrixMask | (target.matrix == weight.threshold)
    }
    return(ifelse(matrixMask, lower.cap.threshold, upper.cap.threshold))
}


#'
#' @description compute the Cronbach's alpha coefficient
#'
#' @param list.of.data.seq a list of equal length numeric vectors
#'                         each vector is data series of a feature
#'
#' @param to.compute.one.out boolean.
#'                           Determine if one-out Cronbach alpha should be computed.
#'                           default: FALSE
#'
#' @return a numeric representing the coefficient
#'         if to.compute.one.out is TRUE, a numeric vector of the same length as list.of.data.seq
#'             where the entries represent the Cronbach alpha coefficient after removing one feature
#'
MiscUtility.Statistics.cronbachAlpha = function(list.of.data.seq, to.compute.one.out = FALSE) {
    k = length(list.of.data.seq)
    seriesLength = length(list.of.data.seq[[1]])
    sumOfFeatures = sapply(
        seq_len(seriesLength),
        function(idx)
            sum(sapply(
                seq_len(k),
                function(featureIdx)
                    list.of.data.seq[[featureIdx]][[idx]]
            ))
    ) # better method?
    varVect = sapply(
        seq_len(k),
        function(featureIdx)
            var(list.of.data.seq[[featureIdx]])
    )
    res = NULL
    sumOfVar = sum(varVect)
    if (to.compute.one.out) {
        varOfOneOutSum = sapply(
            seq_len(k),
            function(featureIdx)
                var(sumOfFeatures - list.of.data.seq[[featureIdx]])
        )
        oneOutSumOfVar = sumOfVar - varVect
        res = (1 + 1 / (k - 1)) * (1 - oneOutSumOfVar / varOfOneOutSum)
    } else {
        varOfSum = var(sumOfFeatures)
        res = (1 + 1 / (k - 1)) * (1 - sumOfVar / varOfSum)
    }
    return(res)
}


#'
#' @description align string by centering
#'
#' @param vect.of.text.lines a vector of strings
#'
#' @param padding a string of length 1, or a vector of such strings
#'                Used to pad strings
#'                if a single string is provided, all strings use this pad
#'                if a vector, there should be exactly one pad for every string, inclusing empty ones
#'                default: " ", a space character
#'
#' @param with.strip.whitespace.first boolean. determine if leading and trailing white spaces shuold be trimmed first
#'                                    if TRUE, strings are processed with trimws() before padding
#'                                    if FALSE, strings are padded as inputed
#'                                    default: TRUE
#'
#' @return the same vector of strings, but the strings are centered by padding on both sides
#'         empty strings are not processed
#'
MiscUtility.Transform.certeringTextLines = function(vect.of.text.lines, padding = " ", with.strip.whitespace.first = TRUE) {
    numLines = length(vect.of.text.lines)
    if (with.strip.whitespace.first) {
        vect.of.text.lines = sapply(vect.of.text.lines, trimws)
    }
    if (any(sapply(padding, function(pad) nchar(pad) != 1))) {
        stop("padding is not of length 1")
    }
    if (length(padding) != 1) {
        if (length(padding) != numLines) {
            stop("Number of paddings does not match the numbers of lines provided")
        }
    } else {
        padding = rep(padding, numLines)
    }
    alignIndices = sapply(vect.of.text.lines, function(x) as.integer((nchar(x) + 1) / 2))
    strLen = sapply(vect.of.text.lines, nchar)
    preLen = max(alignIndices) - alignIndices
    postLen = max(strLen) - strLen - preLen
    for (lIdx in seq_along(vect.of.text.lines)) {
        if (nchar(vect.of.text.lines[lIdx]) == 0) {
            next
        }
        vect.of.text.lines[lIdx] = paste0(
            paste(rep(padding[lIdx], preLen[lIdx]), collapse = ''),
            vect.of.text.lines[lIdx],
            paste(rep(padding[lIdx], postLen[lIdx]), collapse = '')
        )
    }
    return(vect.of.text.lines)
}

#'
#' @description find the top results
#'
#' @param vect.of.val numeric vector. The values to look at
#'
#' @param N integer. The number of results to return
#'          default: 10
#'
#' @param to.take.max boolean. Determine if the largest ones should be returned
#'                    default: TRUE
#'
#' @param to.take.val.only boolean. Determine if only the values should be returned
#'                         default: FALSE
#'
#' @return  if to.take.val.only == FALSE, a list containing two equal-length vectors:
#'              values: the N largest (if to.take.max == TRUE, otherwise smallest)
#'                          values in val
#'              indices: the corresponding indices in val
#'          if to.take.val.only == FALSE, only the values vector would be returned
#'
MiscUtility.getTopVals = function(vect.of.val, N = 10, to.take.max = TRUE, to.take.val.only = FALSE) {
    targetIdx = order(vect.of.val,
        decreasing = to.take.max
    )[1:min(N, length(vect.of.val))]
    if (to.take.val.only) {
        return(vect.of.val[targetIdx])
    } else {
        return(list(
            indices = targetIdx,
            values = vect.of.val[targetIdx]
        ))
    }
}

#'
#' @description clipping to a range
#'
#' @param x numeric vector
#'
#' @param min.val numeric. the minimal value outputted.
#'                can be -Inf
#'                default: 0
#'
#' @param max.val numeric. the maximal value outputted.
#'                can be Inf
#'                assumed to be not less than min.val
#'                default: 1
#'
#' @return a numeric vector of the clipped value
#'
#' @note wrapper of pmin and pmax
#'
MiscUtility.clipValRange = function(x, min.val = 0, max.val = 1) {
    return(pmin(pmax(x, min.val), max.val))
}


#'
#' @description compute the long-run correlation between time series
#'
#' @param list.of.time.series a list of numeric vectors.
#'                            all vectors are assumed to have the same length
#'
#' @param band.width numeric. the band width. assumed to be positive
#'
#' @param kernel.func function. the function used in Andrew's estimate
#'                    assumed to be even L^2 function and values 1 at x = 0
#'
#' @param considered.range numeric, or NA. the maximal shift of the window, in units of B
#'                         also affect where the kernelFunction is evaluated
#'                         (the effective domain is [-(considerRange - 1/B), considerRange - 1/B])
#'                         if NA, will be chosen automatically if kernelFunction is predefined
#'                         if numeric, assumed to be positive.
#'                         Inf is also accepted (consider all possible range)
#'                         if kernelFunction has a bounded support (or domain of significant values),
#'                             consider specifing the bound here for speed up
#'                         default: NA
#'
#' @return a symmetric matrix of dimension n*n with diagonal 1,
#'             where n is the number of series in list.of.time.series
#'         Each entry is a number in [0, 1], higher implies stronger correlation
#'
#' @references T. Vyrosta, S. Lyocsab, E. Baumohl. Network-Based Asset Allocation Strategies
#'
#' @references D. W. K. Andrews. Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimation
#'
#' @note not sure about implementation. could/likely be wrong
#'       assuming [Z_t Z_{t-m}] means outer product
#'
#' @note current complexity: n^2 T^2
#'       can be optimize with e.g. discrete Fourier?
#'
# TODO speed up
#      current implementation is quite slow (~6 mins for 50 series of ~4000 pts, full range)
#      on computing omegaDiag, same datasets, ~6 secs
#
MiscUtility.Statistics.longRunCorrMatrix = function(list.of.time.series,
                                                    band.width,
                                                    kernel.func,
                                                    considered.range = NA) {
    n = length(list.of.time.series)
    if (n <= 1) {
        stop("Insufficient time series")
    }
    TSize = length(list.of.time.series[[1]])
    if (any(sapply(list.of.time.series, length) != TSize)) {
        stop("list.of.time.series contains series of unequal length")
    }
    if (is.na(considered.range)) {
        considered.range = switch(as.character(substitute(kernel.func, environment()))[1],
            "quadraticSpectralKernel" = 30,
            "truncatedKernel" = 1,
            "bartlettKernel" = 1,
            "parzenKernel" = 1,
            "tukeyHanningKernel" = 1,
            Inf
        )
        warning(paste("considerRange chosen as", considered.range))
    }
    considered.range = min(abs(considered.range * band.width), TSize)
    omegaDiag = sapply(
        list.of.time.series,
        function(timeSeries) {
            mean(timeSeries^2) +
                sum(kernel.func(seq_len(considered.range - 1) / band.width) * 2 / TSize *
                    sapply(
                        seq_len(considered.range - 1),
                        function(m)
                            sum(timeSeries[1:(TSize - m)] * timeSeries[(m + 1):TSize])
                    ))
        }
    )
    res = matrix(0, nrow = n, ncol = n)
    for (i in 2:n) {
        for (j in 1:(i - 1)) {
            omega = sum(kernel.func((1 - considered.range):(considered.range - 1) / band.width) / TSize *
                sapply(
                    (1 - considered.range):(considered.range - 1),
                    function(m)
                        sum(list.of.time.series[[i]][max(1, 1 - m):min(TSize, TSize - m)] *
                            list.of.time.series[[j]][max(1, 1 + m):min(TSize, TSize + m)])
                ))
            res[i, j] = res[j, i] = omega / sqrt(omegaDiag[i] * omegaDiag[j])
        }
    }
    diag(res) = 1
    return(res)
}

#'
#' @description kernel function for Andrew's estimate
#'
#' @param x numeric vector
#'
#' @return numeric vector. the values from the Quadratic Spectral kernel function
#'
#' @note this function is one of the common function used in computing Andrew's estimate
#'           (and also in longRunCorrelation)
#'       this function is an even function on real number,
#'           k(0) = 1
#'           continuous at x = 0,
#'           has at most finite discontinuous points,
#'           and is L^2
#'
#' @references D. W. K. Andrews. Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimation
#'
MiscUtility.Statistics.ParzenKernel.quadraticSpectral = function(x) {
    k = 6 * pi * x / 5
    return(ifelse(k == 0, 1, 3 / k ^ 2 * (sin(k) / k - cos(k))))
}

#'
#' @description kernel function for Andrew's estimate
#'
#' @param x numeric vector
#'
#' @return numeric vector. the values from the truncated kernel function
#'
#' @note this function is one of the common function used in computing Andrew's estimate
#'           (and also in longRunCorrelation)
#'       this function is an even function on real number,
#'           k(0) = 1
#'           continuous at x = 0,
#'           has at most finite discontinuous points,
#'           and is L^2
#'
#' @references D. W. K. Andrews. Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimation
#'
MiscUtility.Statistics.ParzenKernel.truncated = function(x) {
    return(ifelse(abs(x) <= 1, 1, 0))
}

#'
#' @description kernel function for Andrew's estimate
#'
#' @param x numeric vector
#'
#' @return numeric vector. the values from the Bartlett kernel function
#'
#' @note this function is one of the common function used in computing Andrew's estimate
#'           (and also in longRunCorrelation)
#'       this function is an even function on real number,
#'           k(0) = 1
#'           continuous at x = 0,
#'           has at most finite discontinuous points,
#'           and is L^2
#'
#' @references D. W. K. Andrews. Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimation
#'
MiscUtility.Statistics.ParzenKernel.bartlett = function(x) {
    return(ifelse(abs(x) <= 1, 1 - abs(x), 0))
}

#'
#' @description kernel function for Andrew's estimate
#'
#' @param x numeric vector
#'
#' @return numeric vector. the values from the Parzen kernel function
#'
#' @note this function is one of the common function used in computing Andrew's estimate
#'           (and also in longRunCorrelation)
#'       this function is an even function on real number,
#'           k(0) = 1
#'           continuous at x = 0,
#'           has at most finite discontinuous points,
#'           and is L^2
#'
#' @references D. W. K. Andrews. Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimation
#'
MiscUtility.Statistics.ParzenKernel.parzen = function(x) {
    return(ifelse(abs(x) <= 1 / 2,
                  1 - 6 * x ^ 2 + 6 * abs(x) ^ 3,
                  ifelse(abs(x) <= 1,
                         2 * (1 - abs(x)) ^ 3,
                         0)
    )
    )
}

#'
#' @description kernel function for Andrew's estimate
#'
#' @param x numeric vector
#'
#' @return numeric vector. the values from the Tukey-Hanning kernel function
#'
#' @note this function is one of the common function used in computing Andrew's estimate
#'           (and also in longRunCorrelation)
#'       this function is an even function on real number,
#'           k(0) = 1
#'           continuous at x = 0,
#'           has at most finite discontinuous points,
#'           and is L^2
#'
#' @references D. W. K. Andrews. Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimation
#'
MiscUtility.Statistics.ParzenKernel.tukeyHanning = function(x) {
    return(ifelse(abs(x) <= 1, (1 + cos(pi * x)) / 2, 0))
}
