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
ENTRYPOINT ["java", "-jar", "/app/app.jar"]