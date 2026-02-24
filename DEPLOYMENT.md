# 智能家居语音助手 - Docker 部署指南

## 目录
- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细部署步骤](#详细部署步骤)
- [配置说明](#配置说明)
- [镜像版本控制](#镜像版本控制)
- [常见问题](#常见问题)

---

## 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

---

## 快速开始

### Windows 用户

```bash
# 1. 启动服务
scripts\start.bat

# 2. 查看日志
docker-compose logs -f

# 3. 停止服务
scripts\stop.bat
```

### Linux/macOS 用户

```bash
# 1. 给脚本添加执行权限
chmod +x scripts/*.sh

# 2. 启动服务
./scripts/start.sh

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
./scripts/stop.sh
```

---

## 详细部署步骤

### 1. 环境准备

确保已安装 Docker 和 Docker Compose：

```bash
docker --version
docker-compose --version
```

### 2. 克隆或下载项目

```bash
cd AI_Assistant
```

### 3. 创建必要的目录

（脚本会自动创建，也可手动创建）

```bash
mkdir -p data models cache mosquitto/data mosquitto/log
```

### 4. 构建镜像（可选）

如果需要本地构建镜像：

**Windows:**
```bash
scripts\build.bat 1.0.0
```

**Linux/macOS:**
```bash
./scripts/build.sh 1.0.0
```

### 5. 启动服务

使用 Docker Compose 一键启动：

```bash
docker-compose up -d
```

### 6. 验证部署

检查服务状态：

```bash
docker-compose ps
```

查看日志：

```bash
docker-compose logs -f smart-home-assistant
```

### 7. 进入交互式界面

```bash
docker attach smart-home-assistant
```

按 `Ctrl+P` 然后 `Ctrl+Q` 退出（不停止容器）。

---

## 配置说明

### docker-compose.yml 配置项

| 服务 | 说明 | 端口 |
|------|------|------|
| mqtt-broker | Mosquitto MQTT 消息代理 | 1883, 9001 |
| smart-home-assistant | 主应用服务 | - |

### 环境变量

在 `docker-compose.yml` 中可配置：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| MQTT_HOST | mqtt-broker | MQTT 服务器地址 |
| MQTT_PORT | 1883 | MQTT 端口 |
| MODEL_NAME | qwen2.5:7b | 使用的 LLM 模型名称 |

### 数据持久化

以下目录会持久化到宿主机：

| 容器路径 | 宿主机路径 | 说明 |
|----------|------------|------|
| /app/data | ./data | 应用数据 |
| /app/models | ./models | 模型文件 |
| /app/cache | ./cache | 缓存文件 |
| /mosquitto/data | ./mosquitto/data | MQTT 数据 |
| /mosquitto/log | ./mosquitto/log | MQTT 日志 |

---

## 镜像版本控制

### 构建特定版本

```bash
# 构建 v1.0.0
docker build -t smart-home-assistant:1.0.0 .

# 构建 latest
docker build -t smart-home-assistant:latest .
```

### 打标签

```bash
docker tag smart-home-assistant:1.0.0 your-registry.com/smart-home-assistant:1.0.0
docker tag smart-home-assistant:1.0.0 your-registry.com/smart-home-assistant:latest
```

### 推送至仓库

```bash
docker login your-registry.com
docker push your-registry.com/smart-home-assistant:1.0.0
docker push your-registry.com/smart-home-assistant:latest
```

### 拉取并运行

```bash
docker pull your-registry.com/smart-home-assistant:1.0.0
docker-compose up -d
```

---

## 常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f smart-home-assistant
docker-compose logs -f mqtt-broker

# 查看最近 100 行
docker-compose logs --tail=100 -f
```

### 镜像管理

```bash
# 查看镜像
docker images

# 删除旧镜像
docker rmi smart-home-assistant:old-version

# 清理未使用的资源
docker system prune -a
```

---

## 常见问题

### 1. 端口被占用

如果 1883 端口被占用，修改 `docker-compose.yml`：

```yaml
ports:
  - "1884:1883"  # 将宿主机端口改为 1884
```

### 2. 权限问题

如果遇到权限问题，检查目录权限：

```bash
chmod -R 755 data models cache
```

### 3. 容器启动失败

查看日志：

```bash
docker-compose logs smart-home-assistant
```

### 4. MQTT 连接失败

确保 mqtt-broker 服务健康：

```bash
docker-compose ps
```

---

## 更新部署

### 更新到新版本

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 停止旧服务
docker-compose down

# 3. 重新构建并启动
docker-compose up -d --build
```

### 滚动更新（零停机）

```bash
docker-compose up -d --no-deps --build smart-home-assistant
```

---

## 生产环境建议

1. **使用私有镜像仓库**：不要使用 latest 标签，使用具体版本号
2. **配置资源限制**：在 docker-compose.yml 中添加 cpu/memory 限制
3. **启用日志轮转**：配置 Docker 日志驱动
4. **定期备份**：备份 data 目录
5. **监控告警**：集成 Prometheus + Grafana 监控
