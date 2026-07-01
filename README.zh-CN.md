# 南京理工大学校园网自动登录

这是一个用于南京理工大学校园网认证系统的命令行自动登录工具。它适合树莓派、服务器、无桌面 Linux、SSH 远程终端等无法方便打开浏览器的场景。

脚本不会绕过认证，只是复刻你在网页登录页输入账号密码并点击“登录”的行为：向校园网认证接口发送 JSON 登录请求。

## 适用场景

- CLI 环境无法通过浏览器登录校园网
- 树莓派或 Linux 服务器开机后需要自动联网
- 校园网中途掉线后需要定时检查和重新登录
- 希望避免使用 Playwright、Chrome、图形界面或远程桌面

## 已知认证信息

默认认证页：

```text
http://10.132.100.104/
```

默认登录接口：

```text
http://10.132.100.104/api/portal/v1/login
```

默认请求体：

```json
{
  "domain": "default",
  "username": "你的账号",
  "password": "你的密码"
}
```

仓库里没有写入任何真实账号或密码。上面的内容只是格式说明。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

如果是在树莓派或 Debian/Ubuntu 上，也可以先安装系统依赖：

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

## 配置账号密码

推荐使用环境变量：

```bash
export CAMPUS_USER="你的学号"
export CAMPUS_PASS="你的密码"
```

也支持：

```bash
export NJUST_USER="你的学号"
export NJUST_PASS="你的密码"
```

如果不想使用环境变量，可以复制示例文件：

```bash
cp examples/password.example.txt password.txt
chmod 600 password.txt
```

然后编辑 `password.txt`：

```text
account
你的学号
password
你的密码
```

`password.txt` 已经写入 `.gitignore`，不会被 Git 跟踪。

## 使用

检测当前是否已经连通外网：

```bash
njust-campus-login --check
```

登录校园网：

```bash
njust-campus-login
```

已联网时跳过登录：

```bash
njust-campus-login --skip-if-online
```

失败重试 3 次：

```bash
njust-campus-login --skip-if-online --retries 3 --retry-delay 8
```

登录后再检测外网是否可用：

```bash
njust-campus-login --skip-if-online --retries 3 --verify-after-login
```

直接运行兼容脚本：

```bash
python3 campus_login.py --skip-if-online
```

## 常用参数

```text
--check                 只检测外网连通性，不登录
--skip-if-online        如果已经联网，就跳过登录
--verify-after-login    登录成功后再次检测外网
--retries               登录重试次数
--retry-delay           每次重试之间等待的秒数
--timeout               HTTP 请求超时时间
--credentials-file      账号密码文件路径，默认 ./password.txt
--user                  手动指定用户名
--password-stdin        从标准输入读取密码
--log-file              同时写入日志文件
--verbose               输出更多诊断信息
```

不建议把密码直接放进命令行参数，因为命令行参数可能出现在 shell 历史或系统进程列表中。本项目没有提供 `--password` 参数，建议使用环境变量、`password.txt` 或 `--password-stdin`。

## systemd 开机自启动

假设项目部署到：

```text
/opt/njust-campus-login
```

安装项目：

```bash
sudo mkdir -p /opt/njust-campus-login
sudo cp -R . /opt/njust-campus-login
cd /opt/njust-campus-login
sudo python3 -m pip install -r requirements.txt
sudo python3 -m pip install -e .
```

创建环境变量文件：

```bash
sudo install -m 600 systemd/campus-login.env.example /etc/campus-login.env
sudo nano /etc/campus-login.env
```

填写：

```text
CAMPUS_USER=你的学号
CAMPUS_PASS=你的密码
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

如果需要每 5 分钟检查一次：

```bash
sudo cp systemd/campus-login.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now campus-login.timer
systemctl list-timers campus-login.timer
```

## 本地开发测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

测试不会访问真实校园网，HTTP 请求通过 fake session 验证。

## 安全检查

当前仓库只包含：

- 示例账号占位符，例如 `your_student_id`
- 示例密码占位符，例如 `your_password`
- 测试用假数据，例如 `alice`、`secret`
- 校园网认证接口地址
- 变量名和配置模板

不包含真实学号、真实密码、Cookie、Token、Session ID 或私钥。

提交到 GitHub 前建议再执行：

```bash
git status --short --ignored
rg -n "CAMPUS_PASS|NJUST_PASS|token|cookie|secret|password" .
```

确认 `password.txt`、日志文件和缓存目录仍然处于 ignored 状态。
