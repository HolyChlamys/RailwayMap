package com.railwaymap.api;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

@SpringBootApplication(scanBasePackages = "com.railwaymap")
@MapperScan("com.railwaymap.data.mapper")
@EnableCaching
public class RailwayApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(RailwayApiApplication.class, args);
    }
}
