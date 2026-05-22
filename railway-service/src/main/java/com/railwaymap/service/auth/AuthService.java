package com.railwaymap.service.auth;

import com.railwaymap.api.config.JwtUtil;
import com.railwaymap.common.entity.User;
import com.railwaymap.data.mapper.UserMapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class AuthService {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;

    public Map<String, Object> register(String username, String password) {
        if (username == null || password == null || username.length() < 3 || password.length() < 6) {
            return Map.of("success", false, "message", "用户名≥3字符, 密码≥6字符");
        }

        Long count = userMapper.selectCount(
                new LambdaQueryWrapper<User>().eq(User::getUsername, username));
        if (count > 0) {
            return Map.of("success", false, "message", "用户名已存在");
        }

        User user = new User();
        user.setUsername(username);
        user.setPasswordHash(passwordEncoder.encode(password));
        userMapper.insert(user);

        String token = jwtUtil.generateToken(username);
        return Map.of("success", true, "token", token);
    }

    public Map<String, Object> login(String username, String password) {
        try {
            User user = userMapper.selectOne(
                    new LambdaQueryWrapper<User>().eq(User::getUsername, username));
            if (user != null && passwordEncoder.matches(password, user.getPasswordHash())) {
                String token = jwtUtil.generateToken(username);
                return Map.of("success", true, "token", token);
            }
        } catch (Exception e) {
            log.error("登录查询失败: username={}", username, e);
            return Map.of("success", false, "message", "系统错误，请稍后重试");
        }

        return Map.of("success", false, "message", "用户名或密码错误");
    }
}
