<?php

function render_home(): void
{
    $default = 'http://baidu.com/';
    ?>
<!doctype html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Hell City Gateway</title>
    <style>
        :root {
            --bg: #050608;
            --panel: rgba(10, 12, 16, 0.88);
            --line: rgba(255, 95, 95, 0.22);
            --text: #f4eadf;
            --muted: rgba(244, 234, 223, 0.66);
            --blood: #b93030;
            --ember: #ff8f6b;
            --shadow: rgba(0, 0, 0, 0.65);
        }

        * {
            box-sizing: border-box;
        }

        html,
        body {
            margin: 0;
            min-height: 100%;
        }

        body {
            font-family: "Georgia", "Times New Roman", serif;
            color: var(--text);
            background:
                radial-gradient(circle at 20% 18%, rgba(163, 21, 21, 0.28), transparent 28%),
                radial-gradient(circle at 78% 12%, rgba(255, 133, 92, 0.14), transparent 22%),
                linear-gradient(180deg, #111218 0%, #06070a 50%, #030406 100%);
            overflow-x: hidden;
        }

        body::before,
        body::after {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
        }

        body::before {
            background:
                repeating-linear-gradient(
                    180deg,
                    rgba(255, 255, 255, 0.02) 0,
                    rgba(255, 255, 255, 0.02) 1px,
                    transparent 1px,
                    transparent 4px
                );
            opacity: 0.18;
            mix-blend-mode: screen;
        }

        body::after {
            background:
                radial-gradient(circle at center, transparent 48%, rgba(0, 0, 0, 0.45) 100%);
        }

        .shell {
            position: relative;
            width: min(980px, calc(100% - 32px));
            margin: 40px auto;
            padding: 32px;
            border: 1px solid var(--line);
            background: var(--panel);
            box-shadow:
                0 24px 60px var(--shadow),
                inset 0 0 0 1px rgba(255, 255, 255, 0.03),
                inset 0 0 48px rgba(185, 48, 48, 0.05);
        }

        .shell::before {
            content: "";
            position: absolute;
            inset: 12px;
            border: 1px solid rgba(255, 255, 255, 0.03);
            pointer-events: none;
        }

        .eyebrow {
            margin: 0 0 12px;
            font-size: 12px;
            letter-spacing: 0.42em;
            text-transform: uppercase;
            color: var(--ember);
        }

        h1 {
            margin: 0;
            font-size: clamp(44px, 9vw, 88px);
            line-height: 0.95;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            text-shadow:
                0 0 14px rgba(185, 48, 48, 0.45),
                0 0 28px rgba(255, 143, 107, 0.14);
        }

        .glitch {
            position: relative;
            display: inline-block;
        }

        .glitch::after {
            content: "Gatewa_";
            position: absolute;
            left: 0.04em;
            top: 0.02em;
            color: rgba(255, 143, 107, 0.22);
            clip-path: inset(50% 0 0 0);
        }

        .lead {
            max-width: 760px;
            margin: 20px 0 10px;
            color: var(--muted);
            font-size: 18px;
            line-height: 1.8;
        }

        .warning-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px;
            margin: 28px 0;
        }

        .warning-card {
            border: 1px solid rgba(255, 143, 107, 0.14);
            background: rgba(255, 255, 255, 0.02);
            padding: 16px 18px;
        }

        .warning-card strong {
            display: block;
            margin-bottom: 8px;
            font-size: 12px;
            letter-spacing: 0.26em;
            text-transform: uppercase;
            color: var(--ember);
        }

        .warning-card span {
            color: var(--muted);
            font-size: 14px;
            line-height: 1.7;
        }

        form {
            margin-top: 26px;
        }

        label {
            display: block;
            margin-bottom: 10px;
            color: #f8d6ca;
            font-size: 13px;
            letter-spacing: 0.22em;
            text-transform: uppercase;
        }

        input {
            width: 100%;
            padding: 16px 18px;
            border: 1px solid rgba(255, 143, 107, 0.18);
            background: rgba(4, 5, 8, 0.88);
            color: var(--text);
            font-size: 16px;
            letter-spacing: 0.04em;
            outline: none;
            box-shadow: inset 0 0 22px rgba(0, 0, 0, 0.35);
        }

        input:focus {
            border-color: rgba(255, 143, 107, 0.42);
            box-shadow:
                0 0 0 1px rgba(255, 143, 107, 0.16),
                0 0 28px rgba(185, 48, 48, 0.12),
                inset 0 0 22px rgba(0, 0, 0, 0.35);
        }

        .actions {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 14px;
            margin-top: 16px;
        }

        button {
            padding: 12px 20px;
            border: 1px solid rgba(255, 143, 107, 0.25);
            background: linear-gradient(180deg, #381010 0%, #1d0909 100%);
            color: #f8e6dc;
            font-size: 15px;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.32);
        }

        button:hover {
            transform: translateY(-1px);
            border-color: rgba(255, 143, 107, 0.42);
            box-shadow:
                0 14px 28px rgba(0, 0, 0, 0.4),
                0 0 20px rgba(185, 48, 48, 0.16);
        }

        .hint {
            color: var(--muted);
            font-size: 14px;
            line-height: 1.7;
        }

        pre {
            background: #111;
            color: #ddd;
            padding: 16px;
            overflow: auto;
        }
        code {
            background: rgba(255, 255, 255, 0.08);
            color: #ffd8cc;
            padding: 2px 6px;
        }

        .footer-note {
            margin-top: 28px;
            padding-top: 18px;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            color: rgba(255, 255, 255, 0.38);
            font-size: 12px;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }

        @media (max-width: 720px) {
            .shell {
                margin: 18px auto;
                padding: 22px 18px;
            }

            .lead {
                font-size: 16px;
            }
        }
    </style>
</head>
<body>
    <main class="shell">
        <p class="eyebrow">Hell City Internal Relay</p>
        <h1>Hell City <span class="glitch">Gateway</span></h1>
        <p class="lead">
            有人说，商场官网在深夜会替访客去看一些本不该被看见的东西。
            你只需要留下一个地址，它就会替你发出请求。
            如果页面开始回应你未曾发送过的内容，就说明你已经离里面太近了。
        </p>

        <section class="warning-grid">
            <article class="warning-card">
                <strong>Observation</strong>
                <span>系统会代替访客访问目标地址，回显它看见的内容。</span>
            </article>
            <article class="warning-card">
                <strong>Protocol Drift</strong>
                <span>有些陈旧协议并未消失，只是被埋进了更深的地方。</span>
            </article>
            <article class="warning-card">
                <strong>After Midnight</strong>
                <span>入口通常比看起来更深，返回内容也未必来自你以为的地方。</span>
            </article>
        </section>

        <form method="get" action="/">
            <label for="url">Target Address</label>
            <input id="url" name="url" type="text" value="<?php echo htmlspecialchars($_GET['url'] ?? $default, ENT_QUOTES); ?>">
            <div class="actions">
                <button type="submit">Open The Gate</button>
                <span class="hint">支持协议取决于底层 cURL。异常地址有时会得到异常回应。</span>
            </div>
        </form>

        <p class="footer-note">Monitor Status: unstable signal detected</p>
    </main>
</body>
</html>
    <?php
}

function do_curl(string $url): array
{
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_TIMEOUT => 5,
        CURLOPT_CONNECTTIMEOUT => 3,
        CURLOPT_PROTOCOLS => CURLPROTO_HTTP | CURLPROTO_HTTPS | CURLPROTO_GOPHER,
        CURLOPT_REDIR_PROTOCOLS => CURLPROTO_HTTP | CURLPROTO_HTTPS,
        CURLOPT_USERAGENT => 'HellCity-Gateway/1.0',
    ]);

    $body = curl_exec($ch);
    $error = curl_error($ch);
    $info = curl_getinfo($ch);
    curl_close($ch);

    return [$body, $error, $info];
}

if (!isset($_GET['url'])) {
    render_home();
    exit;
}

$url = trim((string) $_GET['url']);
[$body, $error, $info] = do_curl($url);

header('Content-Type: text/plain; charset=utf-8');
echo "[Request]\n";
echo $url . "\n\n";
echo "[Info]\n";
echo 'HTTP_CODE=' . ($info['http_code'] ?? 0) . "\n";
echo 'PRIMARY_IP=' . ($info['primary_ip'] ?? 'n/a') . "\n";
echo 'TOTAL_TIME=' . ($info['total_time'] ?? 0) . "\n\n";

if ($error !== '') {
    echo "[Error]\n";
    echo $error . "\n";
    exit;
}

echo "[Body]\n";
echo $body;
