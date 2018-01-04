import json
import time
import logging

from .errors import LoggerError

formatter = '%(asctime)s %(levelname)s: %(message)s'
file_formatter = logging.Formatter(formatter)
logging.basicConfig(level=logging.INFO, format=formatter)


class Report(object):
    _report = {
        "action_id": None
    }

    def __init__(self, action_id, work_dir):
        self._report['action_id'] = action_id
        self.report_path = "{}/report.json".format(work_dir)

    def set_status(self, status):
        self._report['status'] = status

    def save_report(self):
        self._report['finish_at'] = int(time.time())
        content = json.dumps(self._report)
        with open(self.report_path, "w") as f:
            f.write(content)


class Logger(object):
    log_path = None
    log_dir = None
    logger = None
    is_test = False
    init_config = False

    def __init__(self):
        if not self.logger:
            raise LoggerError("请先初始化 Logger")
        if not self.init_config:
            self.init_logger()
        Logger.init_config = True

    def init_logger(self):
        if not self.is_test:
            if not self.log_path:
                raise LoggerError("找不到日志文件目录")
            fh = logging.FileHandler(self.log_path)
            fh.setFormatter(file_formatter)
            self.logger.addHandler(fh)
        ch = logging.StreamHandler()
        self.logger.addHandler(ch)

    @classmethod
    def set_log_path(cls, log_dir):
        cls.log_dir = log_dir
        cls.log_path = "{}/deploy.log".format(log_dir)
        cls.logger = logging.getLogger("Dao-Deploy")

    def info(self, log_message):
        self.logger.info(log_message)

    def waring(self, log_message):
        self.logger.warning(log_message)

    def error(self, log_message):
        self.logger.error(log_message)
