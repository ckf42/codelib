# this file provides interfaces to legacy functions
#
# must be included as the last file
#
#
.LibImportTools.LegacyInterface.Const.ReplacementDict = list(
    # InfoTheory
    "InfoTheory.Divergence.jensenShannonDivergence" = "jensenShannonDivergence",
    "InfoTheory.Divergence.normalizedMIDistance" = "normalized_MI_distance",
    "InfoTheory.Entropy.jointEntropy" = "joint_entropy",
    "InfoTheory.Entropy.renyi" = "renyiEntropy",
    "InfoTheory.Entropy.shannon" = "shannonEntropy",
    "InfoTheory.Similarity.normalizedMuturalInformation" = "NMI_similarity",
    "InfoTheory.Similarity.spreadNormalizedMuturalInformation" = "spread_NMI_similarity",
    "InfoTheory.Transform.NMI.distToSimilarity" = "NMI_dist_to_NMI_sim",
    "InfoTheory.Transform.NMI.similarityToDist" = "NMI_sim_to_NMI_dist",

    # MiscUtility
    "MiscUtility.clipValRange" = "clipRange",
    "MiscUtility.getTopVals" = "topResults",
    "MiscUtility.Norm.lInf" = "l_inf_norm",
    "MiscUtility.Statistics.cronbachAlpha" = "CronbachAlpha",
    "MiscUtility.Statistics.longRunCorrMatrix" = "longRunCorrelation",
    "MiscUtility.Statistics.partialCorr" = "partial_corr",
    "MiscUtility.Statistics.partialCorrDist" = "pcor_dist",
    "MiscUtility.Statistics.ParzenKernel.bartlett" = "bartlettKernel",
    "MiscUtility.Statistics.ParzenKernel.parzen" = "parzenKernel",
    "MiscUtility.Statistics.ParzenKernel.quadraticSpectral" = "quadraticSpectralKernel",
    "MiscUtility.Statistics.ParzenKernel.truncated" = "truncatedKernel",
    "MiscUtility.Statistics.ParzenKernel.tukeyHanning" = "tukeyHanningKernel",
    "MiscUtility.Statistics.serialPearsonCorrMatrix" = "Pearson_correlation_matrix",
    "MiscUtility.Transform.Batch.linearNormalize" = "linearNormalize_list",
    "MiscUtility.Transform.Batch.logReturn" = "toLogReturn_list",
    "MiscUtility.Transform.Batch.toHistogramBinIndices" = "transform_to_bin_indices_list",
    "MiscUtility.Transform.certeringTextLines" = "centerLinesOfStrings",
    "MiscUtility.Transform.corrToDist" = "corrToDist",
    "MiscUtility.Transform.distToCorr" = "distToCorr",
    "MiscUtility.Transform.linearInterpolate" = "linearInterpolate",
    "MiscUtility.Transform.linearNormalize" = "linearNormalize",
    "MiscUtility.Transform.logReturn" = "toLogReturn",
    "MiscUtility.Transform.matrixCutOff" = "matrixCutOff",
    "MiscUtility.Transform.toHistogramBinIndices" = "transform_to_bin_indices",

    # Graph
    "Graph.Characteristic.completeNetwork" = "complete_network",
    "Graph.Characteristic.connectivityThresholdNetwork" = "threshold_algo",
    "Graph.Characteristic.longRunCorrNetwork" = "longRunCorrelationNetwork",
    "Graph.Characteristic.optimalThresholdNetwork" = "optimalThresholdNetwork",
    "Graph.Characteristic.planarMaximallyFilteredGraph" = "planar_maximally_filtered_graph",
    "Graph.Characteristic.proportionalDegreeNetwork" = "proportional_degree_network",
    "Graph.Characteristic.thresholdSignificanceGraph" = "thresholdSignificanceGraph",
    "Graph.getSubordinatedComponentMembers" = "getComponentMembers",
    "Graph.getSubordinatedComponentSize" = "getComponentSize",
    "Graph.isForest" = "is.forest",
    "Graph.isTree" = "is.tree",
    "Graph.Layout.asRootCenteredTree" = "layout_as_tree_with_center_root",
    "Graph.Metric.networkNodeDispersion" = "networkNodeDispersion",
    "Graph.Metric.schieberNetworkDissimilarity" = "schieberNetworkDissimilarity",
    "Graph.Clustering.Plot.clusterResult" = "plot_cluster",
    "Graph.Clustering.Plot.overlapCommunity" = "plot_overlapComm",
    "Graph.Clustering.Plot.overlapCommunityFromAlgo" = "plot_overlapComm_algo",
    "Graph.Clustering.Plot.plotAfterClustering" = "plot_after_clustering",
    "Graph.Plot.tree" = "plot_tree",
    "Graph.Transform.edgeCutOff" = "graphEdgeCutOff",
    "Graph.treeCenter" = "get_tree_center",

    # Graph.Clustering
    "Graph.Clustering.Algo.acuebClusteringWithMetaNetwork" = "ACUEB_with_meta",
    "Graph.Clustering.Algo.acuebClusteringWithoutMetaNetwork" = "ACUEB_without_meta",
    "Graph.Clustering.Algo.greedyNOVERClustering" = "NOVER_clustering",
    "Graph.Clustering.Algo.maximalMSTSplitClustering" = "maximal_split_clustering",
    "Graph.Clustering.Algo.maximalTreeSplit" = "maximal_split_on_tree",
    "Graph.Clustering.Algo.normalizedSpectralClustering" = "normalized_spectral_clustering_graph",
    "Graph.Clustering.Algo.normalizedSpectralClusteringOnMatrix" = "normalized_spectral_clustering",
    "Graph.Clustering.Algo.noverSingleLinkClustering" = "NOVER_single_link_clustering",
    "Graph.Clustering.Animation.evolutions" = "cluster_evolution",
    "Graph.Clustering.Animation.plotEvolution" = "plot_cluster_evolution",
    "Graph.Clustering.Clique.filterBySize" = "filter_clique_by_size",
    "Graph.Clustering.Clique.getMaxCliques" = "get_max_cliques",
    "Graph.Clustering.Measure.noverScore" = "NOVER_score",
    "Graph.Clustering.Metric.adjustedRandIndex" = "adjusted_Rand_index",
    "Graph.Clustering.Metric.cliqueHomogeneity" = "clique_homogeneity",
    "Graph.Clustering.Metric.clusterNMISimilarity" = "clustering_NMI_similarity",
    "Graph.Clustering.Transform.clusteringResultToCommunityList" = "clusteringToCommList",
    "Graph.Clustering.Transform.communityListToMembershipVect" = "membershipFromCommList",
    "Graph.Clustering.Transform.membershipVectToCommunityList" = "commListFromMembership",
    "Graph.Clustering.Algo.stbaClustering" = "STBA_clustering",
    "Graph.Clustering.Algo.novelLouvainClustering" = "novel_Louvain",

    "Graph.Clustering.Metric.Batch.similarity" = "batch_sim",
    "Graph.Clustering.Overlap.getCommunityInfo" = "overlapCommInfo",
    "Graph.Clustering.Overlap.Transform.belongMatrixToVectList" = "belongVectListFromMatrix",
    "Graph.isPlanarGraphDMP" = "is_planar_graph_DMP"
)

.LibImportTools.LegacyInterface.Const.ReverseDict = setNames(
    names(.LibImportTools.LegacyInterface.Const.ReplacementDict),
    .LibImportTools.LegacyInterface.Const.ReplacementDict
)

sapply(
    Filter(exists, names(.LibImportTools.LegacyInterface.Const.ReplacementDict)),
    function(newCmdName) assign(
        .LibImportTools.LegacyInterface.Const.ReplacementDict[[newCmdName]],
        get(newCmdName),
        pos = .GlobalEnv
    )
)
