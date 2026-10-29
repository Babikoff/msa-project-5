package com.example.batchprocessing;

import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.trace.Tracer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.beans.factory.annotation.Value;

@Configuration
public class TracingConfiguration {

    @Value("${otel.service.name:batch-processing}")
    private String serviceName;

    @Bean
    public Tracer tracer() {
        return GlobalOpenTelemetry.getTracer(serviceName);
    }
}