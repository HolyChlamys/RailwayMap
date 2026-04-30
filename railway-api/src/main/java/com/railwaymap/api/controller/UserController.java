package com.railwaymap.api.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class UserController {

    private final JdbcTemplate jdbc;

    @GetMapping("/favorites")
    public List<Map<String, Object>> getFavorites(@AuthenticationPrincipal UserDetails user) {
        Long userId = getUserId(user.getUsername());
        return jdbc.queryForList(
                "SELECT id, type, target_id, label, data, created_at FROM user_favorites WHERE user_id = ?",
                userId);
    }

    @PostMapping("/favorites")
    public Map<String, Object> addFavorite(@AuthenticationPrincipal UserDetails user,
                                            @RequestBody Map<String, Object> body) {
        Long userId = getUserId(user.getUsername());
        String type = (String) body.get("type");
        String targetId = (String) body.get("target_id");
        String label = (String) body.get("label");

        jdbc.update(
                "INSERT INTO user_favorites (user_id, type, target_id, label, data) " +
                "VALUES (?, ?, ?, ?, ?::jsonb) ON CONFLICT (user_id, type, target_id) DO NOTHING",
                userId, type, targetId, label, body.getOrDefault("data", "{}").toString());

        return Map.of("success", true);
    }

    @DeleteMapping("/favorites/{id}")
    public Map<String, Object> removeFavorite(@AuthenticationPrincipal UserDetails user,
                                               @PathVariable Long id) {
        Long userId = getUserId(user.getUsername());
        jdbc.update("DELETE FROM user_favorites WHERE id = ? AND user_id = ?", id, userId);
        return Map.of("success", true);
    }

    @GetMapping("/history")
    public List<Map<String, Object>> getHistory(@AuthenticationPrincipal UserDetails user) {
        Long userId = getUserId(user.getUsername());
        return jdbc.queryForList(
                "SELECT id, search_type, query_text, created_at FROM user_search_history " +
                "WHERE user_id = ? ORDER BY created_at DESC LIMIT 50", userId);
    }

    @PostMapping("/history")
    public Map<String, Object> addHistory(@AuthenticationPrincipal UserDetails user,
                                           @RequestBody Map<String, String> body) {
        Long userId = getUserId(user.getUsername());
        jdbc.update(
                "INSERT INTO user_search_history (user_id, search_type, query_text) VALUES (?, ?, ?)",
                userId, body.get("search_type"), body.get("query_text"));
        return Map.of("success", true);
    }

    private Long getUserId(String username) {
        return jdbc.queryForObject("SELECT id FROM users WHERE username = ?", Long.class, username);
    }
}
