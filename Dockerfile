# Stage 1: Build the application
FROM eclipse-temurin:11-jdk-focal AS build

WORKDIR /app

COPY . .

# Build the application using the Maven wrapper. You can check why i choose this option in the documentation.
RUN chmod +x mvnw

RUN ./mvnw clean package -DskipTests

# Stage 2: Create the runtime image
FROM eclipse-temurin:11-jre-focal

WORKDIR /app

# Copy the built artifact from the build stage
COPY --from=build /app/target/app-0.0.1-SNAPSHOT.jar ./app.jar

# According to application properties it should be set 9001
EXPOSE 9001

CMD ["java", "-jar", "app.jar"]