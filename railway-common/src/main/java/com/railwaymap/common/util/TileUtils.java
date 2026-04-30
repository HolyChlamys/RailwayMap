package com.railwaymap.common.util;

/**
 * 矢量瓦片坐标转换工具
 */
public final class TileUtils {

    private TileUtils() {}

    /**
     * 将 z/x/y 瓦片坐标转换为 Web Mercator 边界框 (EPSG:3857)
     */
    public static double[] tileToBBox(int z, int x, int y) {
        double worldSize = Math.pow(2, z);
        double west  = x / worldSize * 360.0 - 180.0;
        double east  = (x + 1) / worldSize * 360.0 - 180.0;
        double north = Math.atan(Math.sinh(Math.PI * (1 - 2 * y / worldSize))) * 180.0 / Math.PI;
        double south = Math.atan(Math.sinh(Math.PI * (1 - 2 * (y + 1) / worldSize))) * 180.0 / Math.PI;
        return new double[]{west, south, east, north};
    }

    /**
     * 将 WGS-84 经纬度转换为瓦片坐标
     */
    public static int[] lonLatToTile(double lon, double lat, int z) {
        int x = (int) Math.floor((lon + 180.0) / 360.0 * Math.pow(2, z));
        int y = (int) Math.floor((1 - Math.log(Math.tan(Math.toRadians(lat))
                + 1 / Math.cos(Math.toRadians(lat))) / Math.PI) / 2 * Math.pow(2, z));
        return new int[]{x, y};
    }

    /**
     * 计算瓦片四角的 SQL 条件 (ST_MakeEnvelope 用)
     */
    public static String tileToEnvelopeSql(int z, int x, int y) {
        double[] bbox = tileToBBox(z, x, y);
        return String.format("ST_MakeEnvelope(%f, %f, %f, %f, 4326)",
                bbox[0], bbox[1], bbox[2], bbox[3]);
    }
}
