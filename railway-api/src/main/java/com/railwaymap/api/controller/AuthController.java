package com.railwaymap.api.controller;

import com.railwaymap.api.config.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final JdbcTemplate jdbc;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;

    @PostMapping("/register")
    public Map<String, Object> register(@RequestBody Map<String, String> body) {
        String username = body.get("username");
        String password = body.get("password");

        if (username == null || password == null || username.length() < 3 || password.length() < 6) {
            return Map.of("success", false, "message", "用户名≥3字符, 密码≥6字符");
        }

        try {
            jdbc.update("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    username, passwordEncoder.encode(password));
            String token = jwtUtil.generateToken(username);
            return Map.of("success", true, "token", token);
        } catch (Exception e) {
            return Map.of("success", false, "message", "用户名已存在");
        }
    }

    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody Map<String, String> body) {
        String username = body.get("username");
        String password = body.get("password");

        try {
            String hash = jdbc.queryForObject(
                    "SELECT password_hash FROM users WHERE username = ?",
                    String.class, username);
            if (hash != null && passwordEncoder.matches(password, hash)) {
                String token = jwtUtil.generateToken(username);
                return Map.of("success", true, "token", token);
            }
        } catch (Exception ignored) {}

        return Map.of("success", false, "message", "用户名或密码错误");
    }
}
