# Hell City

这是一个单容器双服务的题目骨架：

- 外部入口：`PHP + cURL` SSRF 服务，监听 `0.0.0.0:3000`
- 内部服务：`Next.js`，监听 `127.0.0.1:3001`
- PHP 站点根目录：`/var/www/html`

## 启动

```bash
docker compose up --build
```

访问 `http://127.0.0.1:3000/` 即可看到 SSRF 页面，默认目标为内网 `Next.js` 首页。

## 目录

```text
.
├── Dockerfile
├── docker-compose.yml
├── docker
│   ├── entrypoint.sh
│   └── supervisord.conf
├── ssrf
│   └── index.php
└── next-app
    ├── app
    ├── next.config.js
    ├── package.json
    ├── tsconfig.json
    └── next-env.d.ts
```

## 出题侧可继续补充的点

1. 将 `next-app/package.json` 中的 `next` 版本替换为你要固定的漏洞版本。
2. 按对应漏洞链补充触发路由、构建产物或中间件配置。
3. 用真实 flag 替换 `docker-compose.yml` 里的 `FLAG` 环境变量。
