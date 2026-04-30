package com.railwaymap.data.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.railwaymap.common.dto.TrainSearchResult;
import com.railwaymap.common.entity.TrainRoute;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface TrainRouteMapper extends BaseMapper<TrainRoute> {

    List<TrainSearchResult> searchTrains(@Param("keyword") String keyword,
                                          @Param("limit") int limit);
}
