package com.railwaymap.api;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication(scanBasePackages = "com.railwaymap")
@MapperScan("com.railwaymap.data.mapper")
@EnableScheduling
public class RailwayApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(RailwayApiApplication.class, args);
    }
}
