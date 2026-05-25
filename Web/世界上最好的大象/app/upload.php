<?php
require_once __DIR__ . '/function.php';
require_once __DIR__ . '/class.php';

// 上传页只负责接收文件并展示保存结果。
$message = '';
$uploadedPath = '';
$targetPath = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $targetPath = isset($_POST['target_path']) ? (string)$_POST['target_path'] : '';

    list($ok, $result) = save_upload($_FILES['image'], $targetPath);
    if ($ok) {
        $uploadedPath = $result;
        $message = 'upload success';
    } else {
        $message = $result;
    }
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Upload Image</title>
    <style>
        body {
            margin: 0;
            padding: 40px;
            background: #f6f1e8;
            color: #2d241d;
            font-family: "Microsoft YaHei", sans-serif;
        }
        .wrap {
            max-width: 760px;
            margin: 0 auto;
            background: #fffaf2;
            border: 1px solid #d8c8b7;
            border-radius: 16px;
            padding: 32px;
        }
        .box {
            padding: 16px;
            border-radius: 10px;
            background: #efe2d2;
            margin-bottom: 18px;
        }
        input[type=file], input[type=submit] {
            margin-top: 12px;
        }
    </style>
</head>
<body>
<div class="wrap">
    <h1>Upload Image</h1>

    <?php if ($message !== ''): ?>
        <div class="box">
            <strong><?php echo htmlspecialchars($message, ENT_QUOTES, 'UTF-8'); ?></strong>
            <?php if ($uploadedPath !== ''): ?>
                <p>stored path: <code><?php echo htmlspecialchars($uploadedPath, ENT_QUOTES, 'UTF-8'); ?></code></p>
            <?php endif; ?>
        </div>
    <?php endif; ?>

    <form method="post" enctype="multipart/form-data">
        <input type="file" name="image" required>
        <br>
        <input type="submit" value="upload">
    </form>

    <p><a href="/view.php">view uploaded image</a></p>
    <p><a href="/index.php">back to home</a></p>
</div>
</body>
</html>
