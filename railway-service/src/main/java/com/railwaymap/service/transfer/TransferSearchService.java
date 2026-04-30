package com.railwaymap.service.transfer;

import com.railwaymap.common.dto.TransferRequest;
import com.railwaymap.common.dto.TransferResult;
import com.railwaymap.common.entity.*;
import com.railwaymap.data.mapper.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jgrapht.Graph;
import org.jgrapht.GraphPath;
import org.jgrapht.alg.shortestpath.YenKShortestPath;
import org.jgrapht.graph.DefaultWeightedEdge;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class TransferSearchService {

    private final TransferGraphBuilder graphBuilder;
    private final TransferRankingService rankingService;
    private final TrainStopMapper stopMapper;
    private final TrainFareMapper fareMapper;

    public Map<String, Object> search(TransferRequest req) {
        long startTime = System.currentTimeMillis();

        Graph<String, DefaultWeightedEdge> graph = graphBuilder.buildGraph();

        String fromNode = "STATION:" + req.getFrom();
        String toNode = "STATION:" + req.getTo();

        if (!graph.containsVertex(fromNode) || !graph.containsVertex(toNode)) {
            return Map.of("results", List.of(), "total_found", 0,
                    "search_time_ms", System.currentTimeMillis() - startTime,
                    "error", "出发站或到达站不在图中");
        }

        YenKShortestPath<String, DefaultWeightedEdge> ksp =
                new YenKShortestPath<>(graph);

        List<GraphPath<String, DefaultWeightedEdge>> paths =
                ksp.getPaths(fromNode, toNode, req.getMaxResults() * 3);

        List<TransferResult> results = paths.stream()
                .map(p -> toTransferResult(p, req))
                .filter(r -> r.getTransferCount() <= req.getMaxTransfers())
                .filter(r -> r.getTotalTimeMin() <= 72 * 60) // 总耗时 ≤72h
                .collect(Collectors.toList());

        // 偏好排序
        results = rankingService.rank(results, req.getPreference());

        // 截取前 N
        if (results.size() > req.getMaxResults()) {
            results = results.subList(0, req.getMaxResults());
        }

        long elapsed = System.currentTimeMillis() - startTime;
        log.info("[TRANSFER] {}→{} 找到 {} 条方案, 耗时 {}ms",
                req.getFrom(), req.getTo(), results.size(), elapsed);

        return Map.of(
                "results", results,
                "total_found", results.size(),
                "search_time_ms", elapsed
        );
    }

    private TransferResult toTransferResult(GraphPath<String, DefaultWeightedEdge> path,
                                             TransferRequest req) {
        TransferResult result = new TransferResult();
        result.setId(UUID.randomUUID().toString().substring(0, 8));
        result.setTotalTimeMin((int) path.getWeight());

        List<TransferResult.TransferSegment> segments = new ArrayList<>();
        List<String> vertexList = path.getVertexList();
        int transferCount = 0;

        for (int i = 0; i < vertexList.size() - 1; i++) {
            String fromName = vertexList.get(i).replace("STATION:", "");
            String toName = vertexList.get(i + 1).replace("STATION:", "");

            // 查找车次 (取 E-value 最小的边)
            List<TrainStop> candidates = stopMapper.selectList(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TrainStop>()
                            .eq(TrainStop::getStationName, fromName)
                            .last("AND EXISTS (SELECT 1 FROM train_stops ts2 WHERE ts2.train_no = train_stops.train_no AND ts2.station_name = '" + toName + "' AND ts2.seq = train_stops.seq + 1)")
                            .last("LIMIT 3"));

            if (!candidates.isEmpty()) {
                // 取最快的车次
                TrainStop best = candidates.get(0);

                TransferResult.TransferSegment seg = new TransferResult.TransferSegment();
                seg.setTrainNo(best.getTrainNo());

                String trainType = best.getTrainNo().substring(0, 1);
                seg.setTrainType(trainType);
                seg.setFromStation(fromName);
                seg.setToStation(toName);

                if (best.getDepartTime() != null) {
                    seg.setDepartTime(best.getDepartTime().toString());
                }
                // 查找到达时间
                List<TrainStop> arrivals = stopMapper.selectList(
                        new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TrainStop>()
                                .eq(TrainStop::getTrainNo, best.getTrainNo())
                                .eq(TrainStop::getStationName, toName)
                                .last("LIMIT 1"));
                if (!arrivals.isEmpty() && arrivals.get(0).getArriveTime() != null) {
                    seg.setArriveTime(arrivals.get(0).getArriveTime().toString());
                }
                seg.setDurationMin(computeDuration(best.getTrainNo(), fromName, toName));

                // 票价
                TrainFare fare = fareMapper.selectOne(
                        new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TrainFare>()
                                .eq(TrainFare::getTrainNo, best.getTrainNo())
                                .eq(TrainFare::getFromStation, fromName)
                                .eq(TrainFare::getToStation, toName));
                if (fare != null) {
                    TransferResult.TransferSegment.PriceInfo price =
                            new TransferResult.TransferSegment.PriceInfo();
                    price.setSecond(fare.getPriceSecond());
                    price.setFirst(fare.getPriceFirst());
                    price.setBusiness(fare.getPriceBusiness());
                    price.setSoftSleeperDown(fare.getPriceSoftSleeperDown());
                    price.setHardSleeperDown(fare.getPriceHardSleeperDown());
                    price.setHardSeat(fare.getPriceHardSeat());
                    seg.setPrice(price);
                }

                segments.add(seg);
            }

            if (i > 0) transferCount++;
        }

        result.setTransferCount(Math.max(0, transferCount));
        result.setSegments(segments);

        // 总计票价
        BigDecimal totalPrice = BigDecimal.ZERO;
        for (TransferResult.TransferSegment seg : segments) {
            if (seg.getPrice() != null && seg.getPrice().getSecond() != null) {
                totalPrice = totalPrice.add(seg.getPrice().getSecond());
            }
        }
        result.setTotalPriceYuan(totalPrice);
        result.setScore(0.0);

        return result;
    }

    private int computeDuration(String trainNo, String from, String to) {
        List<TrainStop> stops = stopMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TrainStop>()
                        .eq(TrainStop::getTrainNo, trainNo)
                        .orderByAsc(TrainStop::getSeq));
        int departMin = 0, arriveMin = 0;
        for (TrainStop s : stops) {
            if (s.getStationName().equals(from) && s.getDepartTime() != null) {
                departMin = s.getDepartTime().toSecondOfDay() / 60;
            }
            if (s.getStationName().equals(to) && s.getArriveTime() != null) {
                arriveMin = s.getArriveTime().toSecondOfDay() / 60;
            }
        }
        return Math.max(arriveMin - departMin, 1);
    }
}
