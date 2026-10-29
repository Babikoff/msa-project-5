package com.example.batchprocessing;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.JobExecution;
import org.springframework.batch.core.JobParameters;
import org.springframework.batch.core.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/batch")
public class BatchRestController {

    private static final Logger log = LoggerFactory.getLogger(BatchRestController.class);

    private final JobLauncher jobLauncher;
    private final Job importProductJob;
    private final Tracer tracer;
    private final Counter batchTriggerCounter;
    private final Timer batchDurationTimer;

    @Autowired
    public BatchRestController(JobLauncher jobLauncher,
                               Job importProductJob,
                               MeterRegistry meterRegistry,
                               Tracer tracer) {
        this.jobLauncher = jobLauncher;
        this.importProductJob = importProductJob;
        this.tracer = tracer;
        this.batchTriggerCounter = Counter.builder("batch_trigger_total")
                .tag("application", "batch-processing")
                .register(meterRegistry);
        this.batchDurationTimer = Timer.builder("batch_job_duration_seconds")
                .tag("application", "batch-processing")
                .register(meterRegistry);
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        String traceId = UUID.randomUUID().toString();
        log.info("Health check requested. traceId={}", traceId);
        Map<String, Object> status = Map.of(
                "status", "UP",
                "service", "batch-processing",
                "timestamp", Instant.now().toString(),
                "traceId", traceId
        );
        return ResponseEntity.ok(status);
    }

    @PostMapping("/trigger")
    public ResponseEntity<Map<String, Object>> triggerBatch() {
        String traceId = UUID.randomUUID().toString();
        Span span = tracer.spanBuilder("batch.trigger")
                .setAttribute("trace.id", traceId)
                .startSpan();
        try (var scope = span.makeCurrent()) {
            log.info("Batch trigger requested. traceId={}", traceId);
            batchTriggerCounter.increment();

            Timer.Sample sample = Timer.start();
            try {
                JobParameters params = new JobParametersBuilder()
                        .addString("traceId", traceId)
                        .addLong("timestamp", System.currentTimeMillis())
                        .toJobParameters();
                JobExecution execution = jobLauncher.run(importProductJob, params);
                log.info("Batch job completed. traceId={}, status={}", traceId, execution.getStatus());
                span.setAttribute("batch.status", execution.getStatus().toString());
                return ResponseEntity.ok(Map.of(
                        "traceId", traceId,
                        "jobName", execution.getJobInstance().getJobName(),
                        "status", execution.getStatus(),
                        "startTime", execution.getStartTime().toString(),
                        "endTime", execution.getEndTime().toString()
                ));
            } catch (Exception e) {
                log.error("Batch job failed. traceId={}, error={}", traceId, e.getMessage(), e);
                span.setAttribute("batch.status", "FAILED");
                span.setAttribute("error.message", e.getMessage());
                return ResponseEntity.internalServerError()
                        .body(Map.of("traceId", traceId, "status", "FAILED", "error", e.getMessage()));
            } finally {
                sample.stop(batchDurationTimer);
                span.end();
            }
        }
    }
}