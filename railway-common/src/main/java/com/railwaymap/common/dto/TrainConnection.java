package com.railwaymap.common.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * A rideable segment between any two stations on the same train.
 * Time uses cumulative minutes from a reference epoch to handle cross-midnight trains.
 *
 * For a train with N stops, N*(N-1)/2 connections are precomputed.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class TrainConnection {
    /** Train number (e.g. "G1") */
    private String trainNo;
    /** Train type letter */
    private String trainType;
    /** Boarding station name */
    private String fromStation;
    /** Alighting station name */
    private String toStation;
    /** Sequence order: from station seq in the train's stop list */
    private int fromSeq;
    /** Sequence order: to station seq in the train's stop list */
    private int toSeq;
    /** Departure time in cumulative minutes from day 0 00:00 (may exceed 1439 for cross-midnight) */
    private int departMin;
    /** Arrival time in cumulative minutes (always >= departMin) */
    private int arriveMin;
    /** Segment duration in minutes */
    private int durationMin;

    /** Day offset for display: 0 = same day as departure, 1 = next day, etc. */
    public int departDayOffset() { return departMin / 1440; }
    public int arriveDayOffset() { return arriveMin / 1440; }

    /** Clock time within the day (0-1439) */
    public int departClockMin() { return departMin % 1440; }
    public int arriveClockMin() { return arriveMin % 1440; }
}
