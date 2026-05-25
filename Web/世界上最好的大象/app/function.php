<?php
if (isset($_SERVER['SCRIPT_FILENAME']) && realpath($_SERVER['SCRIPT_FILENAME']) === __FILE__) {
    highlight_file(__FILE__);
}

// 上传目录与单文件大小上限。
define('UPLOAD_DIR', __DIR__ . '/uploads/');
define('MAX_FILE_SIZE', 512000);

function ensure_upload_dir()
{
    // 首次运行时自动创建上传目录。
    if (!is_dir(UPLOAD_DIR)) {
        mkdir(UPLOAD_DIR, 0777, true);
    }
}

function get_allowed_exts()
{
    return array('jpg', 'jpeg', 'png', 'gif');
}

function get_magic_map()
{
    // 通过文件头魔数做第一轮类型识别。
    return array(
        'jpg' => "\xFF\xD8\xFF",
        'jpeg' => "\xFF\xD8\xFF",
        'png' => "\x89PNG",
        'gif' => "GIF8"
    );
}

function get_tail_map()
{
    // 通过结尾特征做第二轮粗略校验，防止明显伪造文件。
    return array(
        'jpg' => "\xFF\xD9",
        'jpeg' => "\xFF\xD9",
        'png' => "IEND\xAE\x42\x60\x82",
        'gif' => "\x00\x3B"
    );
}

function get_extension($filename)
{
    return strtolower(pathinfo($filename, PATHINFO_EXTENSION));
}

function check_extension($filename)
{
    return in_array(get_extension($filename), get_allowed_exts());
}

function check_magic($tmpFile, $ext)
{
    $fp = fopen($tmpFile, 'rb');
    if (!$fp) {
        return false;
    }
    $head = fread($fp, 8);
    fclose($fp);

    $magicMap = get_magic_map();
    // 要求文件头从对应格式的魔数开始。
    return isset($magicMap[$ext]) && strpos($head, $magicMap[$ext]) === 0;
}

function check_tail($tmpFile, $ext)
{
    $content = @file_get_contents($tmpFile);
    if ($content === false) {
        return false;
    }

    $tailMap = get_tail_map();
    if (!isset($tailMap[$ext])) {
        return false;
    }

    $tail = $tailMap[$ext];
    $window = substr($content, -32);

    return strpos($window, $tail) !== false;
}

function random_upload_name($ext)
{
    return date('YmdHis') . '_' . mt_rand(1000, 9999) . '.' . $ext;
}

function image_upload_error($msg)
{
    return array(false, $msg);
}

function filter_upload($file)
{
    // 依次执行结构、大小、扩展名、文件头、文件尾校验。
    if (!isset($file) || !is_array($file)) {
        return image_upload_error('missing file');
    }

    if (!isset($file['error']) || $file['error'] !== UPLOAD_ERR_OK) {
        return image_upload_error('upload failed');
    }

    if ($file['size'] > MAX_FILE_SIZE) {
        return image_upload_error('file too large');
    }

    $ext = get_extension($file['name']);
    if (!check_extension($file['name'])) {
        return image_upload_error('only image extensions are allowed');
    }

    if (!check_magic($file['tmp_name'], $ext)) {
        return image_upload_error('invalid image header');
    }

    if (!check_tail($file['tmp_name'], $ext)) {
        return image_upload_error('invalid image tail');
    }

    return array(true, $ext);
}

function resolve_upload_target_path($inputPath, $ext)
{
    $inputPath = trim((string)$inputPath);
    if ($inputPath === '') {
        $targetName = random_upload_name($ext);
        return array(true, UPLOAD_DIR . $targetName, 'uploads/' . $targetName);
    }

    if (preg_match('/^[a-z0-9.+-]+:\/\//i', $inputPath)) {
        return array(false, 'invalid target path');
    }

    $normalizedPath = normalize_image_path($inputPath);
    if ($normalizedPath === false) {
        return array(false, 'invalid target path');
    }

    if (get_extension($normalizedPath) !== $ext) {
        return array(false, 'target path extension mismatch');
    }

    if (strpos($normalizedPath, '/') === 0) {
        $filesystemPath = $normalizedPath;
        $publicPath = $normalizedPath;
    } else {
        $filesystemPath = __DIR__ . '/' . ltrim($normalizedPath, '/');
        $publicPath = ltrim($normalizedPath, '/');
    }

    return array(true, $filesystemPath, $publicPath);
}

function save_upload($file, $targetPath = '')
{
    ensure_upload_dir();
    list($ok, $result) = filter_upload($file);
    if (!$ok) {
        return array(false, $result);
    }

    list($pathOk, $filesystemPath, $publicPath) = resolve_upload_target_path($targetPath, $result);
    if (!$pathOk) {
        return array(false, $filesystemPath);
    }

    $targetDir = dirname($filesystemPath);
    if (!is_dir($targetDir) && !mkdir($targetDir, 0777, true)) {
        return array(false, 'failed to prepare target dir');
    }

    if (!move_uploaded_file($file['tmp_name'], $filesystemPath)) {
        return array(false, 'failed to save upload');
    }

    $imageType = @exif_imagetype($filesystemPath);
    if ($imageType === false) {
        return array(false, 'server recheck failed');
    }

    return array(true, $publicPath);
}

function normalize_image_path($path)
{
    $path = trim((string)$path);
    if ($path === '') {
        return false;
    }

    if (preg_match('/^https?:\/\//i', $path)) {
        return false;
    }

    if (strpos($path, '..') !== false) {
        return false;
    }

    return $path;
}

function normalize_view_image_path($path)
{
    $path = trim((string)$path);
    if ($path === '') {
        return false;
    }

    if (preg_match('/^https?:\/\//i', $path)) {
        return false;
    }

    if (preg_match('/^phar:\/\//i', $path)) {
        $innerPath = substr($path, 7);
        if ($innerPath === '' || strpos($innerPath, '..') !== false) {
            return false;
        }
        return $path;
    }

    if (strpos($path, '..') !== false) {
        return false;
    }

    return $path;
}

function check_view_image($path)
{
    $normalizedPath = normalize_view_image_path($path);
    if ($normalizedPath === false) {
        return array(false, 400, 'invalid image path', null, null);
    }

    $imageType = @exif_imagetype($normalizedPath);
    if ($imageType === false) {
        return array(false, 404, 'image check failed', null, $normalizedPath);
    }

    return array(true, 200, 'ok', $imageType, $normalizedPath);
}
