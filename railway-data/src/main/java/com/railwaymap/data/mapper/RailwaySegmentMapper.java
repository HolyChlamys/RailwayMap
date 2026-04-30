package com.railwaymap.data.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.railwaymap.common.entity.RailwaySegment;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface RailwaySegmentMapper extends BaseMapper<RailwaySegment> {

    List<String> getVectorTile(@Param("envelope") String envelope,
                               @Param("z") int z,
                               @Param("x") int x,
                               @Param("y") int y,
                               @Param("layer") String layer);

    List<RailwaySegment> findByBBox(@Param("envelope") String envelope,
                                    @Param("limit") int limit);
}
