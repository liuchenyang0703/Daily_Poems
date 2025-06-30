import smtplib
import time
import subprocess
import os
import logging
import logging.handlers  # 新增日志轮转模块
import sys
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header


# █████████████████████████ 用户配置区域 █████████████████████████
BAT_DIR = r"C:\Users\user\Desktop\定时推送\Daily_Poems"  # 存放bat脚本路径
BAT_NAME = "git_push.bat"  # 你的BAT文件名
LOG_DIR = r"C:\Users\user\Desktop\定时推送"  # 存放日志文件的路径

# 邮件配置（需要QQ邮箱开启SMTP服务）
EMAIL_SETTINGS = {
    "smtp_server": "smtp.163.com",
    "smtp_port": 465,
    "sender_email": "liucy_zabbixcs@163.com",
    "sender_password": "GYZHXXXFOGWDALUS",
    "receiver_email": "2162059863@qq.com"
}

# 日志配置
LOG_CONFIG = {
    "log_dir": os.path.join(LOG_DIR, "Logs"),  # 日志存放目录
    "log_file": "auto_push.log",               # 日志文件名
    "backup_count": 7                          # 保留最近7天的日志
}
# █████████████████████████████████████████████████████████████

# █████████████████████████ 日志颜色配置 █████████████████████████
class ColorFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',   # 蓝色
        'INFO': '\033[92m',    # 绿色
        'WARNING': '\033[93m', # 黄色
        'ERROR': '\033[91m',   # 红色
        'CRITICAL': '\033[95m',# 紫色
        'RESET': '\033[0m'
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        message = super().format(record)
        return f"{color}{message}{self.COLORS['RESET']}"


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 清理已有处理器
    if logger.hasHandlers():
        logger.handlers.clear()

    # 创建日志目录
    os.makedirs(LOG_CONFIG["log_dir"], exist_ok=True)
    log_path = os.path.join(LOG_CONFIG["log_dir"], LOG_CONFIG["log_file"])

    # 控制台处理器（带颜色）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter(
        '[%(asctime)s] %(levelname)-8s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

    # 文件处理器（带日志轮转）
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_path,
        when='midnight',  # 每天午夜轮转
        backupCount=LOG_CONFIG["backup_count"],
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # 显示日志路径
    logging.info(f"📁 日志文件保存在：{log_path}")


# █████████████████████████ 时间格式转换 █████████████████████████
def seconds_to_hms(seconds):
    """将秒数转换为小时分钟格式"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{int(hours)}小时{int(minutes)}分钟"


# █████████████████████████ 发送通知邮件 █████████████████████████
def send_email(success=True, next_run=None, error_message=None):
    """发送结果通知邮件"""
    try:
        # 构建邮件内容
        subject = "✅ Git每日自动推送成功" if success else "❌ Git每日自动推送失败"
        content = f"""
        <h3>Git每日自动推送执行结果通知</h3>
        <p>执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>执行结果：{'成功完成Git每日自动推送操作' if success else '每日自动推送过程中发生错误，请检查！'}</p>
        """
        if error_message:
            content += f"<p>错误信息：{error_message}</p>"
        if next_run:
            content += f'<p>下次执行时间：{next_run.strftime("%Y-%m-%d %H:%M:%S")}</p>'
        content += '<hr><small>此邮件由Liucy研发的自动推送系统发送，请勿直接回复</small>'

        # 创建邮件对象
        msg = MIMEText(content, 'html', 'utf-8')
        msg['From'] = Header(EMAIL_SETTINGS["sender_email"])
        msg['To'] = Header(EMAIL_SETTINGS["receiver_email"])
        msg['Subject'] = Header(subject, 'utf-8')

        # 发送邮件
        with smtplib.SMTP_SSL(EMAIL_SETTINGS["smtp_server"], EMAIL_SETTINGS["smtp_port"]) as server:
            server.login(EMAIL_SETTINGS["sender_email"], EMAIL_SETTINGS["sender_password"])
            server.sendmail(
                EMAIL_SETTINGS["sender_email"],
                EMAIL_SETTINGS["receiver_email"],
                msg.as_string()
            )
        logging.info("📧 成功发送通知邮件")

    except Exception as e:
        logging.error(f"📧 邮件发送失败: {str(e)}")


# █████████████████████████ 编码处理模块 █████████████████████████
def decode_with_fallback(byte_data):
    """三级解码策略：GBK → UTF-8 → Latin-1"""
    encodings = ['gbk', 'utf-8', 'latin-1']
    for encoding in encodings:
        try:
            return byte_data.decode(encoding)
        except UnicodeDecodeError:
            continue
    # 终极保底方案：替换错误字符
    return byte_data.decode('latin-1', errors='replace')


# █████████████████████████ BAT执行模块 █████████████████████████
def execute_bat():
    """执行BAT脚本并捕获输出"""
    process = None
    try:
        bat_path = os.path.join(BAT_DIR, BAT_NAME)
        if not os.path.exists(bat_path):
            logging.error(f"❌ 关键错误：BAT文件不存在于 {bat_path}")
            return False, "BAT 文件不存在"

        logging.info("🔄 开始执行BAT脚本...")
        process = subprocess.Popen(
            bat_path,
            shell=True,
            cwd=BAT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        # 超时时间（秒）
        timeout = 60  # 可以根据实际情况调整
        start_time = time.time()

        outputs = []  # 保存所有输出
        while True:
            if time.time() - start_time > timeout:
                logging.error("❌ 执行超时，强制终止")
                return False, "执行超时"

            raw_output = process.stdout.readline()
            if not raw_output and process.poll() is not None:
                break
            if raw_output:
                cleaned_line = decode_with_fallback(raw_output).strip()
                logging.info(f"   → {cleaned_line}")
                outputs.append(cleaned_line)  # 保存输出

        # 检查执行结果
        if process.returncode != 0:
            logging.error(f"❌ 执行失败 (退出码: {process.returncode})")
            return False, f"非零退出码: {process.returncode}"

        # 检查输出中是否存在 git 推送失败的关键信息
        for line in outputs:
            if any(error in line for error in ["Failed to connect", "Connection timed out", "fatal"]):
                logging.error("❌ 发现错误信息，执行失败")
                return False, f"推送失败: {line}"

        logging.info("✅ 执行成功")
        return True, None

    except Exception as e:
        logging.error(f"🔥 执行异常: {str(e)}", exc_info=True)
        return False, f"执行异常: {str(e)}"
    finally:
        if process:
            try:
                process.kill()
            except:
                pass


# █████████████████████████ 主控制循环 █████████████████████████
def main_loop():
    """主循环控制逻辑"""
    setup_logging()
    logging.info("🚀 守护程序启动")

    try:
        while True:
            # 计算精确执行时间
            current_time = datetime.now()
            logging.info(f"⏰ 本次执行时间：{current_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # 执行BAT脚本
            success, error_message = execute_bat()

            # 计算下次执行时间
            next_run = current_time + timedelta(seconds=86400)
            sleep_seconds = (next_run - datetime.now()).total_seconds()

            # 发送邮件
            if success:
                send_email(success=True, next_run=next_run)
            else:
                send_email(success=False, error_message=error_message)

            # 格式化休眠时间显示
            hms = seconds_to_hms(sleep_seconds)
            logging.info(f"⏳ 下次执行时间：{next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"💤 进入休眠状态，等待 {hms}")

            time.sleep(max(0, sleep_seconds))

    except KeyboardInterrupt:
        logging.info("\n🛑 用户手动终止程序")
    except Exception as e:
        logging.error(f"💥 主循环异常: {str(e)}", exc_info=True)
        send_email(success=False, error_message=f"主循环异常: {str(e)}")
        time.sleep(3600)  # 错误后休眠1小时再重试


if __name__ == "__main__":
    # 首次运行检查
    if not os.path.exists(BAT_DIR):
        print(f"❌ 错误：配置的BAT目录不存在 {BAT_DIR}")
        sys.exit(1)

    if not os.path.isfile(os.path.join(BAT_DIR, BAT_NAME)):
        print(f"❌ 错误：BAT文件不存在 {BAT_NAME}")
        sys.exit(1)

    main_loop()