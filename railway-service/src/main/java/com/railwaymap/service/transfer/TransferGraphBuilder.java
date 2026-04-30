package com.railwaymap.service.transfer;

import com.railwaymap.common.entity.TrainStop;
import com.railwaymap.common.entity.Station;
import com.railwaymap.data.mapper.StationMapper;
import com.railwaymap.data.mapper.TrainRouteMapper;
import com.railwaymap.data.mapper.TrainStopMapper;
import com.railwaymap.data.mapper.TrainFareMapper;
import com.railwaymap.common.entity.TrainRoute;
import com.railwaymap.common.entity.TrainFare;
import lombok.RequiredArgsConstructor;
import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultDirectedWeightedGraph;
import org.jgrapht.graph.DefaultWeightedEdge;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.time.LocalTime;
import java.util.*;

/**
 * 构建铁路时间依赖图
 *
 * 节点: "STATION:stationName" (车站节点)
 * 边:
 *   - 运行边: 车次在 A→B 站间运行 (权重 = 运行时间 分钟)
 *   - 等待边: 同站换乘等待 (权重 = 最小换乘时间)
 */
@Component
@RequiredArgsConstructor
public class TransferGraphBuilder {

    private static final Logger log = LoggerFactory.getLogger(TransferGraphBuilder.class);

    private final TrainRouteMapper routeMapper;
    private final TrainStopMapper stopMapper;
    private final StationMapper stationMapper;
    private final TrainFareMapper fareMapper;

    // 最小换乘时间 (分钟)
    private static final int MIN_TRANSFER_MINUTES = 30;

    /**
     * 构建图 — 包含所有有效车次
     */
    public Graph<String, DefaultWeightedEdge> buildGraph() {
        Graph<String, DefaultWeightedEdge> graph =
                new DefaultDirectedWeightedGraph<>(DefaultWeightedEdge.class);

        List<TrainRoute> routes = routeMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TrainRoute>()
                        .eq(TrainRoute::getIsValid, true));

        for (TrainRoute route : routes) {
            List<TrainStop> stops = stopMapper.selectList(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TrainStop>()
                            .eq(TrainStop::getTrainNo, route.getTrainNo())
                            .orderByAsc(TrainStop::getSeq));

            for (int i = 0; i < stops.size() - 1; i++) {
                TrainStop from = stops.get(i);
                TrainStop to = stops.get(i + 1);

                String fromNode = "STATION:" + from.getStationName();
                String toNode = "STATION:" + to.getStationName();

                graph.addVertex(fromNode);
                graph.addVertex(toNode);

                // 计算运行时间 (分钟)
                int duration = computeDuration(from.getDepartTime(), to.getArriveTime());

                DefaultWeightedEdge edge = graph.addEdge(fromNode, toNode);
                if (edge != null && duration > 0) {
                    graph.setEdgeWeight(edge, duration);
                }
            }
        }

        // 添加同站换乘边 (等待时间)
        for (String vertex : graph.vertexSet()) {
            DefaultWeightedEdge transferEdge = graph.addEdge(vertex, vertex);
            if (transferEdge != null) {
                graph.setEdgeWeight(transferEdge, MIN_TRANSFER_MINUTES);
            }
        }

        log.info("[GRAPH] 构建完成: {} 顶点, {} 边",
                graph.vertexSet().size(), graph.edgeSet().size());
        return graph;
    }

    private int computeDuration(LocalTime depart, LocalTime arrive) {
        if (depart == null || arrive == null) return 60; // fallback
        int mins = arrive.toSecondOfDay() / 60 - depart.toSecondOfDay() / 60;
        return Math.max(mins, 1);
    }
}
