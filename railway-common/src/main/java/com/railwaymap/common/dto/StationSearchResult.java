package com.railwaymap.common.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class StationSearchResult {
    private Long id;
    private String name;
    private String city;
    private String province;
    private String category;
    private Double lon;
    private Double lat;
}
