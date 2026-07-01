# NJUST Campus Network Auto Login

[简体中文说明](README.zh-CN.md)

南京理工大学校园网命令行自动登录脚本。它会复刻网页登录页提交账号密码的 JSON 请求，解决服务器、树莓派、无桌面 Linux 或 SSH 环境里无法打开浏览器完成认证的问题。

项目只用于登录你本人有权限使用的校园网账号，不绕过认证，不内置账号密码。

## 功能

- 使用 `requests` 向 `http://10.132.100.104/api/portal/v1/login` 发送登录请求
- 默认 payload 为 `{"domain":"default","username":"...","password":"..."}`
- 支持环境变量、`password.txt` 和标准输入读取密码
- 支持联网检测、已联网跳过、失败重试、登录后验证
- 支持日志文件和 systemd 开机自启动/定时保活

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

临时设置账号密码后运行：

```bash
export CAMPUS_USER="你的学号"
export CAMPUS_PASS="你的密码"
njust-campus-login --skip-if-online --retries 3 --verify-after-login
```

也可以直接运行兼容脚本：

```bash
python campus_login.py --skip-if-online
```

## 凭据配置

推荐使用环境变量：

```bash
export CAMPUS_USER="你的学号"
export CAMPUS_PASS="你的密码"
```

也支持 `NJUST_USER` / `NJUST_PASS`。

如果不想设置环境变量，可以复制示例文件：

```bash
cp examples/password.example.txt password.txt
chmod 600 password.txt
```

`password.txt` 支持以下格式：

```text
account
你的学号
password
你的密码
```

或：

```text
CAMPUS_USER=你的学号
CAMPUS_PASS=你的密码
```

`password.txt` 已在 `.gitignore` 中排除，避免误提交真实密码。

## 常用命令

检测外网是否已连通：

```bash
njust-campus-login --check
```

已联网则跳过登录：

```bash
njust-campus-login --skip-if-online
```

失败重试 3 次，并在成功后验证外网：

```bash
njust-campus-login --skip-if-online --retries 3 --retry-delay 8 --verify-after-login
```

把日志追加到文件：

```bash
njust-campus-login --skip-if-online --log-file ./campus-login.log
```

从标准输入读取密码，避免密码出现在 shell 历史中：

```bash
printf '%s\n' '你的密码' | njust-campus-login --user "你的学号" --password-stdin
```

## 参数

```text
--login-url             登录 API，默认 http://10.132.100.104/api/portal/v1/login
--portal-url            登录页，默认 http://10.132.100.104/
--domain                服务域，默认 default
--timeout               HTTP 超时秒数，默认 10
--retries               登录重试次数，默认 1
--retry-delay           重试间隔秒数，默认 5
--check-url             联网检测 URL
--check                 只检测联网状态，不登录
--skip-if-online        已联网时跳过登录
--verify-after-login    登录后再次检测外网
--no-warmup             登录前不预访问认证页
--credentials-file      账号密码文件路径，默认 ./password.txt
--user                  用户名；密码仍建议用环境变量、文件或 --password-stdin
--password-stdin        从标准输入读取一行密码
--log-file              追加写入日志文件
--verbose               输出更多诊断信息
```

## systemd 开机自动运行

假设项目部署在 `/opt/njust-campus-login`，并已在该目录安装依赖：

```bash
sudo mkdir -p /opt/njust-campus-login
sudo cp -R . /opt/njust-campus-login
cd /opt/njust-campus-login
sudo python3 -m pip install -r requirements.txt
sudo python3 -m pip install -e .
```

创建只允许 root 读取的环境变量文件：

```bash
sudo install -m 600 systemd/campus-login.env.example /etc/campus-login.env
sudo nano /etc/campus-login.env
```

安装服务：

```bash
sudo cp systemd/campus-login.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable campus-login.service
sudo systemctl start campus-login.service
```

查看日志：

```bash
journalctl -u campus-login.service -n 80 --no-pager
```

如果校园网会中途掉线，可以安装定时器每 5 分钟检查一次：

```bash
sudo cp systemd/campus-login.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now campus-login.timer
systemctl list-timers campus-login.timer
```

## 开发与测试

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

本地测试不会访问真实校园网，核心 HTTP 请求通过 fake session 验证。

## 安全提醒

- 不要把真实账号、密码、Cookie、Token 提交到 GitHub
- 不要把密码放进命令行参数，命令行参数可能被系统进程列表记录
- 如果曾经在截图、聊天或提交历史里暴露过密码，建议及时修改
