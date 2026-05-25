<?php
require_once __DIR__ . '/function.php';
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Elephant Image Station</title>
    <style>
        body {
            margin: 0;
            padding: 40px;
            background: #f6f1e8;
            color: #2d241d;
            font-family: "Microsoft YaHei", sans-serif;
        }
        .wrap {
            max-width: 860px;
            margin: 0 auto;
            background: #fffaf2;
            border: 1px solid #d8c8b7;
            border-radius: 16px;
            padding: 32px;
            box-shadow: 0 10px 35px rgba(89, 62, 40, 0.08);
        }
        a {
            color: #8d4f28;
            text-decoration: none;
        }
        code {
            background: #efe2d2;
            padding: 2px 6px;
            border-radius: 6px;
        }
    </style>
</head>
<body>
<!-- 为了兼容，保留了遗留类存在了class.php，函数在function.php -->
<div class="wrap">
    <h1>Elephant Image Station</h1>
    <p>这里是世界上最好的大象安全图片托管站，用安全的随机数来保护你隐私的图片 ---by 世界上最好的大象</p>
    <p>当前上传目录：<code><?php echo htmlspecialchars(UPLOAD_DIR, ENT_QUOTES, 'UTF-8'); ?></code></p>
    <p><a href="/upload.php">进入上传页面</a></p>
    <p><a href="/view.php">进入图片查看页面</a></p>
    <hr>
    <p>站点提示：</p>
    <ul>
        <li>仅允许上传图片文件</li>
        <li>上传完成后会再次识别图片类型</li>
    </ul>
</div>
</body>
</html>
