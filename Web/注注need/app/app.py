import os
import secrets
import subprocess
import time
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import pymysql
import requests
from flask import Flask, flash, redirect, render_template, request, send_file, session, url_for
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.utils import secure_filename

from encrypt import encrypt_password, verify_password


APP_ROOT = Path("/app")
AVATAR_DIR = APP_ROOT / "static" / "avatars"
IMAGE_DIR = APP_ROOT / "static" / "images"
UPLOAD_DIR = APP_ROOT / "static" / "uploads"
DEFAULT_USER_AVATAR = "/static/avatars/user_default_avatar.jpg"
DEFAULT_ADMIN_AVATAR = "/static/avatars/admin_default_avatar.jpg"
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
ALLOWED_ZIP_EXTENSIONS = {".zip"}
GALLERY_PAGE_SIZE = 6
BACKGROUND_IMAGES = [
    "assets/background1.jpg",
    "assets/background2.jpg",
    "assets/background3.jpg",
    "assets/background4.jpg",
]
FLAG_VALUE = os.environ.get("GZCTF_FLAG", "whuctf{default}")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


def db_config():
    return {
        "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.environ.get("MYSQL_PORT", "3306")),
        "user": os.environ.get("MYSQL_USER", "ctf_user"),
        "password": os.environ.get("MYSQL_PASSWORD", "ctf_pass"),
        "database": os.environ.get("MYSQL_DATABASE", "ctf_challenge"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True,
    }


def get_connection():
    return pymysql.connect(**db_config())


def ensure_users_table_schema(cursor):
    cursor.execute("SHOW COLUMNS FROM users")
    existing_columns = {row["Field"]: row for row in cursor.fetchall()}

    column_definitions = {
        "nickname": "ALTER TABLE users ADD COLUMN nickname VARCHAR(128) NOT NULL DEFAULT '' AFTER password",
        "bio": "ALTER TABLE users ADD COLUMN bio TEXT NULL AFTER nickname",
        "email": "ALTER TABLE users ADD COLUMN email VARCHAR(255) NOT NULL DEFAULT '' AFTER bio",
        "avatar": "ALTER TABLE users ADD COLUMN avatar VARCHAR(255) NOT NULL DEFAULT '' AFTER email",
        "role": "ALTER TABLE users ADD COLUMN role VARCHAR(16) NOT NULL DEFAULT 'user' AFTER avatar",
    }

    for column, statement in column_definitions.items():
        if column not in existing_columns:
            cursor.execute(statement)

    if "password" in existing_columns and existing_columns["password"]["Type"] != "varchar(128)":
        cursor.execute("ALTER TABLE users MODIFY COLUMN password VARCHAR(128) NOT NULL")

    cursor.execute("SHOW INDEX FROM users WHERE Key_name = 'username'")
    username_index = cursor.fetchone()
    if not username_index:
        cursor.execute("ALTER TABLE users ADD UNIQUE KEY username (username)")


def init_db():
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin#2026!Rabbit")
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(64) UNIQUE NOT NULL,
        password VARCHAR(128) NOT NULL,
        nickname VARCHAR(128) NOT NULL DEFAULT '',
        bio TEXT,
        email VARCHAR(255) NOT NULL DEFAULT '',
        avatar VARCHAR(255) NOT NULL DEFAULT '',
        role VARCHAR(16) NOT NULL DEFAULT 'user'
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """
    for _ in range(30):
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(schema)
                    ensure_users_table_schema(cursor)
                    cursor.execute(
                        """
                        INSERT INTO users (username, password, nickname, bio, email, avatar, role)
                        VALUES (%s, %s, %s, %s, %s, %s, 'admin')
                        ON DUPLICATE KEY UPDATE password = VALUES(password)
                        """,
                        (
                            "admin",
                            admin_password,
                            "RabbitMaster",
                            "本站维护员，仅供内部测试。",
                            "admin@rabbit.local",
                            DEFAULT_ADMIN_AVATAR,
                        ),
                    )
            return
        except pymysql.MySQLError:
            time.sleep(2)
    raise RuntimeError("database initialization failed")


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, password, nickname, bio, email, avatar, role FROM users WHERE id=%s",
                (user_id,),
            )
            return cursor.fetchone()


@app.before_request
def enforce_login():
    allowed_endpoints = {"login", "register", "static", "healthz"}
    if request.endpoint in allowed_endpoints or request.endpoint is None:
        return None
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return None


def save_bytes_as_avatar(data: bytes, extension: str) -> str:
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        extension = ".png"
    filename = f"{secrets.token_hex(8)}{extension}"
    target = AVATAR_DIR / filename
    target.write_bytes(data)
    return f"/static/avatars/{filename}"


def crop_avatar_bytes(data: bytes, extension: str, crop_left: float, crop_top: float, crop_size: float) -> tuple[bytes, str]:
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        extension = ".png"
    with Image.open(BytesIO(data)) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        width, height = image.size
        side = max(1, int(min(width, height) * max(0.2, min(crop_size, 1.0))))
        max_left = max(width - side, 0)
        max_top = max(height - side, 0)
        left = int(max_left * max(0.0, min(crop_left, 1.0)))
        top = int(max_top * max(0.0, min(crop_top, 1.0)))
        cropped = image.crop((left, top, left + side, top + side)).resize((320, 320))
        buffer = BytesIO()
        output_format = "PNG" if extension == ".png" else "JPEG"
        save_extension = ".png" if output_format == "PNG" else ".jpg"
        cropped.save(buffer, format=output_format, quality=92)
    return buffer.getvalue(), save_extension


def update_avatar(user_id: int, avatar_path: str):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET avatar=%s WHERE id=%s", (avatar_path, user_id))


def list_gallery(page: int):
    items = []
    for path in IMAGE_DIR.iterdir():
        if path.name.startswith("README_PLACEHOLDER"):
            continue
        if path.is_file() or path.is_symlink():
            stat = path.stat()
            display_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            title = path.stem.replace("_", " ").replace("-", " ").strip() or path.name
            title = title.title()
            items.append(
                {
                    "name": path.name,
                    "title": title,
                    "uploaded_at": display_time,
                    "sort_key": stat.st_mtime,
                }
            )
    items.sort(key=lambda item: item["sort_key"], reverse=True)
    total = len(items)
    total_pages = max(1, (total + GALLERY_PAGE_SIZE - 1) // GALLERY_PAGE_SIZE)
    page = min(max(page, 1), total_pages)
    start = (page - 1) * GALLERY_PAGE_SIZE
    end = start + GALLERY_PAGE_SIZE
    return items[start:end], page, total_pages


@app.route("/")
def index():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        page = 1
    gallery, current_page, total_pages = list_gallery(page)
    return render_template(
        "index.html",
        user=user,
        gallery=gallery,
        current_page=current_page,
        total_pages=total_pages,
        background_images=BACKGROUND_IMAGES,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not username or not password:
            flash("用户名和密码不能为空。", "error")
            return render_template("register.html", user=current_user(), background_images=BACKGROUND_IMAGES)
        if password != confirm_password:
            flash("两次输入的密码不一致。", "error")
            return render_template("register.html", user=current_user(), background_images=BACKGROUND_IMAGES)
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
                    if cursor.fetchone():
                        flash("用户名已存在。", "error")
                        return render_template("register.html", user=current_user(), background_images=BACKGROUND_IMAGES)
                    cursor.execute(
                        """
                        INSERT INTO users (username, password, nickname, bio, email, avatar, role)
                        VALUES (%s, %s, %s, %s, %s, %s, 'user')
                        """,
                        (username, encrypt_password(password), username, "", "", DEFAULT_USER_AVATAR),
                    )
        except pymysql.MySQLError:
            flash("注册失败，数据库结构可能未完成初始化。", "error")
            return render_template("register.html", user=current_user(), background_images=BACKGROUND_IMAGES)
        flash("注册成功，请登录。", "success")
        return redirect(url_for("login"))
    return render_template("register.html", user=current_user(), background_images=BACKGROUND_IMAGES)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        query = f"SELECT id, username, password, nickname, bio, email, avatar, role FROM users WHERE username = '{username}' LIMIT 1"
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    user = cursor.fetchone()
        except pymysql.MySQLError:
            user = None
        if not user:
            flash("用户不存在", "error")
            return render_template("login.html", user=current_user(), background_images=BACKGROUND_IMAGES)
        if not verify_password(password, user["password"]):
            flash("密码错误", "error")
            return render_template("login.html", user=current_user(), background_images=BACKGROUND_IMAGES)
        session["user_id"] = user["id"]
        flash("登录成功。", "success")
        return redirect(url_for("index"))
    return render_template("login.html", user=current_user(), background_images=BACKGROUND_IMAGES)


@app.route("/logout")
def logout():
    session.clear()
    flash("已退出登录。", "success")
    return redirect(url_for("index"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = current_user()
    if request.method == "POST":
        action = request.form.get("action", "profile")
        if action == "profile":
            nickname = request.form.get("nickname", "")
            bio = request.form.get("bio", "")
            email = request.form.get("email", "")
            query = (
                "UPDATE users SET "
                f"nickname='{nickname}', "
                f"bio='{bio}', "
                f"email='{email}' "
                f"WHERE id={user['id']}"
            )
            try:
                with get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(query)
                flash("资料已更新。", "success")
            except pymysql.MySQLError as exc:
                flash(f"更新失败: {exc}", "error")
            return redirect(url_for("profile"))
        if action == "local_avatar":
            uploaded = request.files.get("avatar")
            if not uploaded or not uploaded.filename:
                flash("请选择图片文件。", "error")
                return redirect(url_for("profile"))
            extension = Path(uploaded.filename).suffix.lower()
            if extension not in ALLOWED_IMAGE_EXTENSIONS:
                flash("仅支持常见图片扩展名。", "error")
                return redirect(url_for("profile"))
            try:
                crop_left = float(request.form.get("crop_left", "0"))
                crop_top = float(request.form.get("crop_top", "0"))
                crop_size = float(request.form.get("crop_size", "1"))
            except ValueError:
                crop_left, crop_top, crop_size = 0.0, 0.0, 1.0
            try:
                avatar_bytes, avatar_extension = crop_avatar_bytes(
                    uploaded.read(), extension, crop_left, crop_top, crop_size
                )
            except UnidentifiedImageError:
                flash("无法识别该图片文件。", "error")
                return redirect(url_for("profile"))
            avatar_path = save_bytes_as_avatar(avatar_bytes, avatar_extension)
            update_avatar(user["id"], avatar_path)
            flash("头像上传成功。", "success")
            return redirect(url_for("profile"))
        if action == "remote_avatar":
            source_url = request.form.get("source_url", "").strip()
            if not source_url:
                flash("请输入资源 URL。", "error")
                return redirect(url_for("profile"))
            parsed = urlparse(source_url)
            try:
                if parsed.scheme == "file":
                    source_path = Path(parsed.path or "/").resolve()
                    if str(source_path) == "/flag":
                        flash("有hacker!!!", "error")
                        return redirect(url_for("profile"))
                    if not str(source_path).startswith(str(APP_ROOT)):
                        flash("有hacker!!!", "error")
                        return redirect(url_for("profile"))
                    data = source_path.read_bytes()
                    extension = source_path.suffix.lower() or ".png"
                else:
                    response = requests.get(source_url, timeout=5)
                    response.raise_for_status()
                    data = response.content
                    extension = Path(parsed.path).suffix.lower() or ".png"
                avatar_path = save_bytes_as_avatar(data, extension)
                update_avatar(user["id"], avatar_path)
                flash("头像导入成功。", "success")
            except (OSError, requests.RequestException) as exc:
                flash(f"导入失败: {exc}", "error")
            return redirect(url_for("profile"))
    user = current_user()
    return render_template("profile.html", user=user, background_images=BACKGROUND_IMAGES)


@app.route("/avatar", methods=["GET", "POST"])
def avatar():
    return redirect(url_for("profile"))


def zip_members_safe(zip_path: Path) -> bool:
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            name = info.filename
            if name.startswith("/") or ".." in Path(name).parts:
                return False
    return True


@app.route("/admin/upload", methods=["GET", "POST"])
def admin_upload():
    user = current_user()
    if user["role"] != "admin":
        flash("该功能仅管理员可访问。", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        uploaded = request.files.get("archive")
        if not uploaded or not uploaded.filename:
            flash("请选择 ZIP 文件。", "error")
            return redirect(url_for("admin_upload"))
        extension = Path(uploaded.filename).suffix.lower()
        if extension not in ALLOWED_ZIP_EXTENSIONS:
            flash("仅支持 ZIP 压缩包。", "error")
            return redirect(url_for("admin_upload"))

        archive_name = secure_filename(uploaded.filename) or "images.zip"
        archive_path = UPLOAD_DIR / f"{secrets.token_hex(8)}-{archive_name}"
        uploaded.save(archive_path)
        if not zip_members_safe(archive_path):
            archive_path.unlink(missing_ok=True)
            flash("压缩包中存在非法路径。", "error")
            return redirect(url_for("admin_upload"))
        try:
            subprocess.run(
                ["unzip", "-o", str(archive_path), "-d", str(IMAGE_DIR)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            flash("图片资源已解压。", "success")
        except subprocess.CalledProcessError:
            flash("解压失败。", "error")
        return redirect(url_for("admin_upload"))

    gallery, _, _ = list_gallery(1)
    return render_template(
        "admin_upload.html",
        user=user,
        gallery=gallery,
        background_images=BACKGROUND_IMAGES,
        flag_value=FLAG_VALUE,
    )


@app.route("/images/<path:filename>")
def image_view(filename: str):
    target = IMAGE_DIR / filename
    if not target.exists() and not target.is_symlink():
        flash("图片不存在。", "error")
        return redirect(url_for("index"))
    return send_file(target)


@app.route("/healthz")
def healthz():
    return {"status": "ok"}


def ensure_placeholder_files():
    placeholder_avatar = AVATAR_DIR / "README_PLACEHOLDER.txt"
    placeholder_image = IMAGE_DIR / "README_PLACEHOLDER.txt"
    if not placeholder_avatar.exists():
        placeholder_avatar.write_text("Place your avatar placeholder images here if needed.\n", encoding="utf-8")
    if not placeholder_image.exists():
        placeholder_image.write_text("Place your gallery placeholder images here if needed.\n", encoding="utf-8")


if __name__ == "__main__":
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ensure_placeholder_files()
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
