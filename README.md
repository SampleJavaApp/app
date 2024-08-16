# Ege Uzma Devops Engineering Study

- Hello, in this documentation i will try to  explain what i did and how i did to complete this case.

- Note: I added Step-4 questions answers to this README file at the bottom.

## Step-1

### Step-1.1

- I forked this [sample-java-app](https://github.com/SampleJavaApp/app) to my own GitHub account and started to work on develop branch.

### Step-1.2

- I created a Dockerfile with multi-stages for this application.

    - For build stage in Dockerfile i choose eclipse-temurin:11-jdk-focal because Eclipse Temurin is a popular, well-maintained OpenJDK distribution. The JDK version is used here because we need compilation tools for the build process.

    '''Dockerfile
        FROM eclipse-temurin:11-jdk-focal AS build
    '''

    - Then The working directory for the application is defined. All files within this java-app project are copied to the directory specified in the image.

    '''Dockerfile
        WORKDIR /app
        COPY . .
    '''
    - The execute permission is granted to Maven Wrapper. This will able to build our app in Jenkins env. After permission i used mvnw to build and package the java application. There are 2 main reason why i choose to do that.
        - The Maven Wrapper ensures that everyone uses the same version of Maven. So that there will be no build failure or inconsistencies
        - With mvnw, we don't need to have Maven installed globally on our machine or on our CI/CD environment. It uses the wrapper scripts.
    '''Dockerfile
       RUN chmod +x mvnw
       RUN ./mvnw clean package -DskipTests
    '''
    - Next is to run already compiled application in previous stage. I used the JRE version in the build as we only need to run the compiled application, not build it. This results in a smaller final image. 

    '''Dockerfile
        FROM eclipse-temurin:11-jre-focal
    '''
    - Because this stage is for runtime, other files except JAR file are not needed. Only JAR file is copied.
    
    '''Dockerfile
        COPY --from=build /app/target/app-0.0.1-SNAPSHOT.jar ./app.jar
    '''
    - Last but not least, According to application.properties file, I exposed the application to 9001 port and execute the JAR. 

    '''Dockerfile
        EXPOSE 9001
        CMD ["java", "-jar", "app.jar"]
    '''
- Here is the [Dockerfile](https://github.com/Lastroke/app/blob/develop/Dockerfile)

## Step-2

## Step-3

## Step-4