package com.railwaymap.api.controller;

import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/sync")
public class SyncController {

    @PostMapping("/trigger")
    public Map<String, String> triggerSync() {
        // Phase 1 实现: 触发数据同步
        return Map.of("status", "triggered");
    }
}
