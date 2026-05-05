package com.railwaymap.api;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(scanBasePackages = "com.railwaymap")
@MapperScan("com.railwaymap.data.mapper")
public class RailwayApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(RailwayApiApplication.class, args);
    }
}
