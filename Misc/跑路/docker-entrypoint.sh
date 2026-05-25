#!/bin/sh

# Check the environment variables for the flag and assign to INSERT_FLAG
if [ "$DASFLAG" ]; then
    INSERT_FLAG="$DASFLAG"
elif [ "$FLAG" ]; then
    INSERT_FLAG="$FLAG"
elif [ "$GZCTF_FLAG" ]; then
    INSERT_FLAG="$GZCTF_FLAG"
else
    INSERT_FLAG="flag{TEST_Dynamic_FLAG}"
fi

# 将FLAG写入文件 请根据需要修改
echo $INSERT_FLAG | tee /var/flag

# 控制flag和项目源码的权限
chmod 744 /var/flag
chmod 740 /app/*

cd /app
# 运行jar程序文件
(cd ./BC && java -Xms64M -Xmx128M -jar BungeeCord.jar) &
(cd ./MC18 && java -Xms128M -Xmx256M -jar paper-1-8-8-445.jar) &
wait