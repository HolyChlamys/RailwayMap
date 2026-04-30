package com.railwaymap.batch.listener;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.core.*;
import org.springframework.batch.core.listener.StepExecutionListenerSupport;
import org.springframework.batch.item.ExecutionContext;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * 进度日志 + 失败记录监听器
 */
public class ImportProgressListener extends StepExecutionListenerSupport {

    private static final Logger log = LoggerFactory.getLogger(ImportProgressListener.class);

    private final Path logPath;
    private final List<String> failedGrids = new ArrayList<>();
    private int gridIndex = 0;
    private int totalGrids;
    private int totalWritten;

    public ImportProgressListener(Path logPath, int totalGrids) {
        this.logPath = logPath;
        this.totalGrids = totalGrids;
    }

    @Override
    public void beforeStep(StepExecution stepExecution) {
        String now = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        appendLog(String.format("[%s] [IMPORT] ========== 开始导入 ==========", now));
        appendLog(String.format("[%s] [IMPORT] 待处理网格: %d 个", now, totalGrids));
    }

    @Override
    public ExitStatus afterStep(StepExecution stepExecution) {
        String now = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        appendLog(String.format("[%s] [IMPORT] ========== 导入完成 ==========", now));
        appendLog(String.format("[%s] [IMPORT] 成功: %d 格, 失败: %d 格 → 见 import_errors.log",
                now, gridIndex - failedGrids.size(), failedGrids.size()));
        long duration = java.time.temporal.ChronoUnit.SECONDS.between(
                stepExecution.getStartTime(), stepExecution.getLastUpdated());
        appendLog(String.format("[%s] [IMPORT] 总写入记录: %d 条, 总耗时 %ds",
                now, totalWritten, duration));

        if (!failedGrids.isEmpty()) {
            appendLog(String.format("[%s] [IMPORT] 失败网格: %s", now, String.join(", ", failedGrids)));
        }
        return ExitStatus.COMPLETED;
    }

    public void onGridStart(String gridId, long fileSize) {
        gridIndex++;
        String now = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        String msg = String.format("[%s] [IMPORT] [%d/%d] %s (%.1fMB): 开始导入",
                now, gridIndex, totalGrids, gridId, fileSize / 1_000_000.0);
        log.info(msg);
        appendLog(msg);
    }

    public void onGridProgress(String gridId, int written, int total) {
        String now = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        int pct = total > 0 ? written * 100 / total : 0;
        log.info("[{}] [IMPORT] [{}] {}/{} ({}%)", now, gridId, written, total, pct);
    }

    public void onGridComplete(String gridId, int railways, int stations) {
        String now = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        String msg = String.format("[%s] [IMPORT] [%d/%d] %s: %d 铁路线, %d 车站 ✓",
                now, gridIndex, totalGrids, gridId, railways, stations);
        log.info(msg);
        appendLog(msg);
        totalWritten += railways + stations;
    }

    public void onGridFailed(String gridId, String reason) {
        failedGrids.add(gridId + "(" + reason + ")");
        appendLog(String.format("[%s] [ERROR] %s: %s",
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")),
                gridId, reason));
    }

    private void appendLog(String msg) {
        try {
            Path parent = logPath.getParent();
            if (parent != null) Files.createDirectories(parent);
            Files.writeString(logPath, msg + "\n",
                    StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (Exception e) {
            log.warn("写入导入日志失败: {}", e.getMessage());
        }
    }
}
