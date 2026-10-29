# FROM openjdk:24-slim
# # 8080
# WORKDIR .
# COPY build/libs/*.jar app.jar
# ENTRYPOINT ["java","-jar","/app.jar"]

FROM gradle:8.10-jdk17 AS builder
WORKDIR /home/gradle/project
COPY --chown=gradle:gradle . .
RUN gradle --no-daemon clean bootJar -x test

FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=builder /home/gradle/project/build/libs/*.jar /app/app.jar

# OpenTelemetry Java Agent for Jaeger tracing
RUN mkdir -p /opentelemetry
ADD https://repo1.maven.org/maven2/io/opentelemetry/javaagent/opentelemetry-javaagent/1.28.0/opentelemetry-javaagent-1.28.0.jar /opentelemetry/opentelemetry-javaagent.jar

ENTRYPOINT ["java", "-javaagent:/opentelemetry/opentelemetry-javaagent.jar", "-Dotel.service.name=batch-processing", "-Dotel.exporter.otlp.endpoint=http://jaeger:4317", "-Dotel.traces.sampler=always_on", "-jar", "/app/app.jar"]