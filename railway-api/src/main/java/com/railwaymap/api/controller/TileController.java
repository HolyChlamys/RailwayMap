package com.railwaymap.api.controller;

import com.railwaymap.service.map.TileService;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.CacheControl;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.concurrent.TimeUnit;

@RestController
@RequestMapping("/api/tiles")
@RequiredArgsConstructor
public class TileController {

    private final TileService tileService;

    @GetMapping("/{layer}/{z}/{x}/{y}.pbf")
    public ResponseEntity<byte[]> getTile(@PathVariable String layer,
                                          @PathVariable int z,
                                          @PathVariable int x,
                                          @PathVariable int y) {
        byte[] tile = tileService.getTile(layer, z, x, y);

        if (tile == null || tile.length == 0) {
            return ResponseEntity.noContent()
                    .cacheControl(CacheControl.maxAge(1, TimeUnit.HOURS))
                    .build();
        }

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType("application/vnd.mapbox-vector-tile"))
                .cacheControl(CacheControl.maxAge(1, TimeUnit.HOURS).cachePublic())
                .body(tile);
    }
}
