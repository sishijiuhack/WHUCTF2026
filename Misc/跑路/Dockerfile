FROM docker.1ms.run/library/amazoncorretto:17

# 拷贝程序和启动脚本至根目录
COPY ./BC /app/BC
COPY ./MC18 /app/MC18
COPY ./docker-entrypoint.sh /docker-entrypoint.sh

EXPOSE 25577

# 指定容器入口点
ENTRYPOINT [ "/bin/bash","/docker-entrypoint.sh" ]