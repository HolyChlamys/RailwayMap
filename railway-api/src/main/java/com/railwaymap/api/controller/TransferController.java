package com.railwaymap.api.controller;

import com.railwaymap.common.dto.TransferRequest;
import com.railwaymap.service.transfer.TransferSearchService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/transfer")
@RequiredArgsConstructor
public class TransferController {

    private final TransferSearchService transferSearchService;

    @PostMapping("/search")
    public Map<String, Object> search(@RequestBody TransferRequest request) {
        return transferSearchService.search(request);
    }
}
