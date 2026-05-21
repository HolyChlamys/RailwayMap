package com.railwaymap.api.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class UserController {

    private final JdbcTemplate jdbc;
    private final ObjectMapper objectMapper;

    @GetMapping("/favorites")
    public List<Map<String, Object>> getFavorites(@AuthenticationPrincipal String username) {
        Long userId = getUserId(username);
        return jdbc.queryForList(
                "SELECT id, type, target_id, label, data, created_at FROM user_favorites WHERE user_id = ?",
                userId);
    }

    @PostMapping("/favorites")
    public Map<String, Object> addFavorite(@AuthenticationPrincipal String username,
                                            @RequestBody Map<String, Object> body) {
        Long userId = getUserId(username);
        String type = (String) body.get("type");
        String targetId = (String) body.get("target_id");
        String label = (String) body.get("label");

        String dataJson;
        try {
            Object data = body.getOrDefault("data", Map.of());
            dataJson = objectMapper.writeValueAsString(data);
        } catch (Exception e) {
            dataJson = "{}";
        }

        jdbc.update(
                "INSERT INTO user_favorites (user_id, type, target_id, label, data) " +
                "VALUES (?, ?, ?, ?, ?::jsonb) ON CONFLICT (user_id, type, target_id) DO NOTHING",
                userId, type, targetId, label, dataJson);

        return Map.of("success", true);
    }

    @DeleteMapping("/favorites/{id}")
    public Map<String, Object> removeFavorite(@AuthenticationPrincipal String username,
                                               @PathVariable Long id) {
        Long userId = getUserId(username);
        jdbc.update("DELETE FROM user_favorites WHERE id = ? AND user_id = ?", id, userId);
        return Map.of("success", true);
    }

    @GetMapping("/history")
    public List<Map<String, Object>> getHistory(@AuthenticationPrincipal String username) {
        Long userId = getUserId(username);
        return jdbc.queryForList(
                "SELECT id, search_type, query_text, created_at FROM user_search_history " +
                "WHERE user_id = ? ORDER BY created_at DESC LIMIT 50", userId);
    }

    @PostMapping("/history")
    public Map<String, Object> addHistory(@AuthenticationPrincipal String username,
                                           @RequestBody Map<String, String> body) {
        Long userId = getUserId(username);
        jdbc.update(
                "INSERT INTO user_search_history (user_id, search_type, query_text) VALUES (?, ?, ?)",
                userId, body.get("search_type"), body.get("query_text"));
        return Map.of("success", true);
    }

    private Long getUserId(String username) {
        return jdbc.queryForObject("SELECT id FROM users WHERE username = ?", Long.class, username);
    }
}
