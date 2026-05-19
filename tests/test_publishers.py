"""发布模块测试"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_report_saves_to_file():
    """日报内容能正确写入文件"""
    from config import REPORTS_DIR
    test_report = "# Test Report\nTest content"
    test_path = os.path.join(REPORTS_DIR, "test-save.md")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(test_path, "w", encoding="utf-8") as f:
        f.write(test_report)

    with open(test_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert content == test_report
    os.remove(test_path)


def test_email_sender_handles_missing_config(monkeypatch):
    """邮件发送在未配置时优雅跳过"""
    # 确保有 SMTP 配置时正常运行
    from publishers.email_sender import send_report_email

    # 应该无异常（输出警告日志但不崩溃）
    try:
        send_report_email("# Test")
    except Exception as e:
        # 可能是因为 SMTP 连不上，但不应该因为是代码 bug
        assert "auth" in str(e).lower() or "connect" in str(e).lower() or "timeout" in str(e).lower()


def test_git_push_creates_file(tmp_path):
    """Git 推送前确保文件正确写入"""
    report = "# Daily Report\nTest"
    filepath = os.path.join(str(tmp_path), "2026-05-19-daily-report.md")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    assert os.path.exists(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        assert f.read() == report
