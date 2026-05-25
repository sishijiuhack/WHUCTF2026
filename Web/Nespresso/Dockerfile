FROM openjdk:17.0.1-jdk-slim
COPY ./target/nespresso-coffee-1.0-SNAPSHOT.jar /app/app.jar
COPY start.sh /start.sh
WORKDIR /app
EXPOSE 8083
ENTRYPOINT ["/bin/bash", "/start.sh"]
