# Railway 云端真实数据看板

## 目标

部署仓库现有 React + FastAPI 看板；由云端服务运行已有 scan / prep 命令，并将 SQLite 文件持久化在 Railway Volume。

## 数据流

```mermaid
flowchart TD
  A[浏览器 Basic Auth] --> B[React dashboard]
  B --> C[FastAPI /api]
  C --> D[/data 持久卷]
  C --> E[RunJobRunner 子进程]
  E --> F[dragon-quant scan]
  E --> G[dragon-quant prep]
  F --> H[TDX + THS 数据源]
  G --> H
  F --> D
  G --> D
```

## 安全与数据边界

- DQ_PUBLIC_DEPLOYMENT=1 时必须设置用户名、至少 32 字符密码和确切 Host 白名单，否则应用拒绝启动。
- Basic Auth 保护 SPA 和所有 API；仅 /health 健康检查路径放行。
- 仅允许 DQ_ALLOWED_ORIGINS 中配置的同源页面提交 POST /api/runs/*；这些任务只运行 scan / prep / auction，不包含券商下单。
- Workspace 写入保持关闭；Web 默认只读展示策略元数据。
- DQ_DATA_DIR=/data，/data 挂到独立持久卷，包含 dragon.db、assets.db、cache、logs 和报告。

## 真实数据运行

- 数据来自现有 TDX / THS / Tencent collectors，不使用演示页虚构样例。
- 交易日 15:00（Asia/Shanghai）后可从「扫描榜单」点击龙头扫描；21:00 后可从「盘后复盘」点击 prep。
- prep 依赖当日扫描完成；扫描与 prep 共用单飞运行位，按页面提示顺序执行。
- 云端卷从空库开始；不会自动上传个人电脑本地 SQLite。首次 scan/prep 完成后数据才出现。
- TDX TCP / THS HTTPS 出站可用性需首轮采集实测；失败时页面显示真实错误，不回退为虚构行情。

## 运维

- 单副本 + SQLite WAL + 持久卷；不要横向扩容共享同一 SQLite 文件。
- 临时预览站可在 Railway 删除；删除前如需保留历史复盘，先备份 /data。