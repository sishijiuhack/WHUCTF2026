<?php
require_once __DIR__ . '/function.php';
require_once __DIR__ . '/class.php';

$imagePath = isset($_GET['path']) ? (string)$_GET['path'] : '';
$normalizedPath = normalize_view_image_path($imagePath);

if (isset($_GET['raw'])) {
    list($ok, $statusCode, $message, $imageType, $checkedPath) = check_view_image($imagePath);
    if (!$ok) {
        http_response_code($statusCode);
        echo $message;
        exit;
    }

    $mimeType = image_type_to_mime_type($imageType);
    header('Content-Type: ' . $mimeType);
    readfile($checkedPath);
    exit;
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>View Image</title>
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
        .preview {
            max-width: 100%;
            border-radius: 12px;
            border: 1px solid #d8c8b7;
            background: #fff;
        }
        input[type=text] {
            width: 100%;
            margin-top: 12px;
            box-sizing: border-box;
        }
        input[type=submit] {
            margin-top: 12px;
        }
    </style>
</head>
<body>
<div class="wrap">
    <h1>View Image</h1>
    <p>输入站内图片路径即可预览</p>

    <form method="get">
        <input type="text" name="path" value="<?php echo htmlspecialchars($imagePath, ENT_QUOTES, 'UTF-8'); ?>" placeholder="uploads/example.jpg">
        <input type="submit" value="view">
    </form>

    <?php if ($imagePath !== ''): ?>
        <div class="box">
            <p>current path: <code><?php echo htmlspecialchars($imagePath, ENT_QUOTES, 'UTF-8'); ?></code></p>
            <?php if ($normalizedPath !== false): ?>
                <img class="preview" src="/view.php?raw=1&amp;path=<?php echo urlencode($imagePath); ?>" alt="preview">
            <?php else: ?>
                <strong>invalid image path</strong>
            <?php endif; ?>
        </div>
    <?php endif; ?>

    <p><a href="/index.php">back to home</a></p>
</div>
</body>
</html>
