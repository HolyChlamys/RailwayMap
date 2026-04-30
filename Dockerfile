# ===== 构建阶段 =====
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /build

COPY pom.xml .
COPY railway-common/pom.xml railway-common/
COPY railway-data/pom.xml    railway-data/
COPY railway-service/pom.xml railway-service/
COPY railway-api/pom.xml     railway-api/
COPY railway-batch/pom.xml   railway-batch/

RUN mvn dependency:go-offline -B -q

COPY . .
RUN mvn package -pl railway-api -am -DskipTests -B -q

# ===== 运行阶段 =====
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /build/railway-api/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
