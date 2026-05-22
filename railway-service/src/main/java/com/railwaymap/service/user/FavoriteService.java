package com.railwaymap.service.user;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class FavoriteService {

    private final JdbcTemplate jdbc;
    private final UserService userService;
    private final ObjectMapper objectMapper;

    public List<Map<String, Object>> getFavorites(String username) {
        Long userId = userService.getUserId(username);
        return jdbc.queryForList(
                "SELECT id, type, target_id, label, data, created_at FROM user_favorites WHERE user_id = ?",
                userId);
    }

    public Map<String, Object> addFavorite(String username, Map<String, Object> body) {
        Long userId = userService.getUserId(username);
        String type = (String) body.get("type");
        String targetId = (String) body.get("target_id");
        String label = (String) body.get("label");

        String dataJson;
        try {
            dataJson = objectMapper.writeValueAsString(body.getOrDefault("data", Map.of()));
        } catch (JsonProcessingException e) {
            log.warn("Failed to serialize favorite data", e);
            dataJson = "{}";
        }

        jdbc.update(
                "INSERT INTO user_favorites (user_id, type, target_id, label, data) " +
                "VALUES (?, ?, ?, ?, ?::jsonb) ON CONFLICT (user_id, type, target_id) DO NOTHING",
                userId, type, targetId, label, dataJson);
        return Map.of("success", true);
    }

    public Map<String, Object> removeFavorite(String username, Long id) {
        Long userId = userService.getUserId(username);
        jdbc.update("DELETE FROM user_favorites WHERE id = ? AND user_id = ?", id, userId);
        return Map.of("success", true);
    }

    public List<Map<String, Object>> getHistory(String username) {
        Long userId = userService.getUserId(username);
        return jdbc.queryForList(
                "SELECT id, search_type, query_text, created_at FROM user_search_history " +
                "WHERE user_id = ? ORDER BY created_at DESC LIMIT 50", userId);
    }

    public Map<String, Object> addHistory(String username, String searchType, String queryText) {
        Long userId = userService.getUserId(username);
        jdbc.update(
                "INSERT INTO user_search_history (user_id, search_type, query_text) VALUES (?, ?, ?)",
                userId, searchType, queryText);
        return Map.of("success", true);
    }
}
