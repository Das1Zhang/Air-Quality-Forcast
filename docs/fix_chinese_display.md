# 云主机中文显示问题解决方案

## 问题描述
在云主机上运行 Web UI 时，中文字符无法正常显示，显示为方框或问号。

## 原因分析
1. 系统缺少中文字体
2. Web 字体加载失败（Google Fonts 在国内可能无法访问）
3. CSS 字体回退机制不完善

## 解决方案

### 方案一：安装系统字体（推荐）

在 Ubuntu/Debian 系统上安装中文字体：

```bash
# 更新包列表
sudo apt update

# 安装中文字体
sudo apt install fonts-noto-cjk fonts-wqy-zenhei fonts-wqy-microhei

# 验证字体安装
fc-list :lang=zh
```

在 CentOS/RHEL 系统上：

```bash
# 安装中文字体
sudo yum install wqy-zenhei-fonts wqy-microhei-fonts

# 或者使用 dnf（较新版本）
sudo dnf install wqy-zenhei-fonts wqy-microhei-fonts
```

### 方案二：修改字体加载方式

如果 Google Fonts 无法访问，可以：

1. **使用本地字体**（已修改 CSS）
   - 已将 `webui/styles.css` 中的字体堆栈修改为包含中文字体
   - 字体优先级：Noto Sans SC → Microsoft YaHei → PingFang SC → Hiragino Sans GB

2. **禁用 Google Fonts**
   编辑 `webui/index.html`，注释掉 Google Fonts 链接：

```html
<!-- 
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
    href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Merriweather:wght@400;600&display=swap"
    rel="stylesheet" />
-->
```

### 方案三：使用国内 CDN

如果需要保留 Google Fonts，可以使用国内镜像：

```html
<link
    href="https://fonts.loli.net/css2?family=DM+Sans:wght@400;500;600&family=Merriweather:wght@400;600&display=swap"
    rel="stylesheet" />
```

## 验证步骤

1. 重启服务器：
```bash
# 如果使用 Docker
docker-compose restart

# 或直接重启 Python 服务
pkill -f server.py
python server.py
```

2. 清除浏览器缓存（Ctrl+F5）

3. 检查页面是否正常显示中文

## Docker 环境特殊处理

如果使用 Docker，需要在 Dockerfile 中添加字体安装：

```dockerfile
# 在 Dockerfile 中添加
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*
```

然后重新构建镜像：

```bash
docker-compose build --no-cache
docker-compose up -d
```

## 已应用的修改

- ✅ 修改 `webui/styles.css` 字体堆栈，添加中文字体支持
- ✅ 确认 `webui/index.html` 已设置正确的 UTF-8 编码和中文语言

## 注意事项

- 如果云主机在防火墙后，可能需要配置代理访问 Google Fonts
- 建议优先使用方案一（安装系统字体），最稳定可靠
- 修改后需要强制刷新浏览器缓存才能看到效果
