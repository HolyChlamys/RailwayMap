package com.railwaymap.api.controller;

import com.railwaymap.service.user.FavoriteService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class UserController {

    private final FavoriteService favoriteService;

    @GetMapping("/favorites")
    public List<Map<String, Object>> getFavorites(@AuthenticationPrincipal String username) {
        return favoriteService.getFavorites(username);
    }

    @PostMapping("/favorites")
    public Map<String, Object> addFavorite(@AuthenticationPrincipal String username,
                                            @RequestBody Map<String, Object> body) {
        return favoriteService.addFavorite(username, body);
    }

    @DeleteMapping("/favorites/{id}")
    public Map<String, Object> removeFavorite(@AuthenticationPrincipal String username,
                                               @PathVariable Long id) {
        return favoriteService.removeFavorite(username, id);
    }

    @GetMapping("/history")
    public List<Map<String, Object>> getHistory(@AuthenticationPrincipal String username) {
        return favoriteService.getHistory(username);
    }

    @PostMapping("/history")
    public Map<String, Object> addHistory(@AuthenticationPrincipal String username,
                                           @RequestBody Map<String, String> body) {
        return favoriteService.addHistory(username, body.get("search_type"), body.get("query_text"));
    }
}
