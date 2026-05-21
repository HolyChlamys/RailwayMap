package com.railwaymap.api.controller;

import com.railwaymap.common.dto.IsochroneRequest;
import com.railwaymap.common.dto.IsochroneResponse;
import com.railwaymap.service.transfer.IsochroneService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/isochrone")
@RequiredArgsConstructor
public class IsochroneController {

    private final IsochroneService isochroneService;

    @PostMapping
    public IsochroneResponse compute(@RequestBody IsochroneRequest request) {
        return isochroneService.compute(request);
    }

    /** Convenience GET for simple queries: /api/isochrone?station=武汉&minutes=240 */
    @GetMapping
    public IsochroneResponse computeGet(
            @RequestParam String station,
            @RequestParam(defaultValue = "480") int departMin,
            @RequestParam(defaultValue = "240") int minutes,
            @RequestParam(defaultValue = "2") int maxTransfers) {
        IsochroneRequest req = new IsochroneRequest();
        req.setStation(station);
        req.setDepartMin(departMin);
        req.setMaxMinutes(minutes);
        req.setMaxTransfers(maxTransfers);
        req.setGroupByDirection(true);
        return isochroneService.compute(req);
    }
}
