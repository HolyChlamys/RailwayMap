package com.railwaymap.data.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.railwaymap.common.dto.StationSearchResult;
import com.railwaymap.common.entity.Station;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface StationMapper extends BaseMapper<Station> {

    List<String> getVectorTile(@Param("envelope") String envelope,
                               @Param("z") int z,
                               @Param("x") int x,
                               @Param("y") int y,
                               @Param("layer") String layer);

    List<Station> findByBBox(@Param("envelope") String envelope,
                             @Param("limit") int limit);

    List<StationSearchResult> searchByKeyword(@Param("keyword") String keyword,
                                               @Param("limit") int limit);

    List<StationSearchResult> searchByPinyin(@Param("keyword") String keyword,
                                              @Param("limit") int limit);

    List<StationSearchResult> searchByCity(@Param("city") String city,
                                            @Param("limit") int limit);

    @Update("UPDATE stations SET name_pinyin = #{pinyin}, updated_at = NOW() WHERE id = #{id}")
    int updatePinyin(@Param("id") Long id, @Param("pinyin") String pinyin);
}
