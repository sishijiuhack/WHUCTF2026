# Phar Deserialize CTF Challenge

这是一个基于 PHP 5 的 `phar` 反序列化靶场，触发点位于上传流程。

## 题目结构

- `index.php`：主页，在 HTML 注释中给出其他路由
- `function.php`：上传过滤与路径处理函数
- `upload.php`：图片上传点，只校验后缀、文件头、文件尾和体积，保存后使用 `exif_imagetype()` 复检
- `class.php`：历史兼容类，包含可构造的 POP 链

## 启动方式

```bash
docker compose up --build
```

如需对接 GZCTF，可通过环境变量 `GZCTF_FLAG` 注入题目 flag。容器启动时会自动将其写入 `/flag`。

启动后访问：

```text
http://127.0.0.1:8080/
```

## 预期考点

1. 构造图片格式的 Phar Polyglot 上传
2. 通过上传点拿到服务端可控文件路径
3. 上传成功后，后端对 `phar://.../test.txt` 执行 `exif_imagetype()`，触发 Phar 元数据反序列化
4. 利用 `class.php` 中的 POP 链执行命令，读取 `/flag`
