import argparse

from .models import Cluster, MicroServices, TaskStone
from .errors import ArgsError, DeployTaskError
from .config import DESC, USAGE


class Deploy(object):
    def __init__(self):
        self.parser = self.init_parser()
        self._before_deploy = []
        self._after_deploy = []
        self._deploy_task = None
        self._check_deploy = None
        self._rollback = None

        self._get_test_cluster = lambda: Cluster("test_cluster")
        self._get_test_micro_services = lambda: []

        self.__finish_before_task = False
        self.__finish_after_task = False
        self.__finish_deploy_task = False
        self.__finish_check_task = False
        self.__need_rollback = False
        self.__finish_rollback = False

    @staticmethod
    def init_parser():
        parser = argparse.ArgumentParser(description=DESC, usage=USAGE,
                                         formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('deploy', help="执行部署任务或执行部署逻辑测试", choices=["deploy", "test"])
        parser.add_argument('--cluster-url', dest="api_url", help="集群 API URL", default="")
        parser.add_argument('--cluster-username', dest="api_username", help="集群 API 用户名", default="")
        parser.add_argument('--cluster-password', dest="api_password", help="集群 API 密码", default="")
        parser.add_argument('--cluster-type', dest="runtime_type", help="集群类型", choices=["salt_stack"], default="")
        parser.add_argument('--cluster-env', dest="cluster_env", help="集群环境标签", default="")

        parser.add_argument('--package-info', dest="packages", help="制品信息", default="")
        return parser

    def before_deploy(self, func):
        self._before_deploy.append(func)
        return func

    def after_deploy(self, func):
        self._after_deploy.append(func)
        return func

    def deploy_task(self, func):
        if not callable(func):
            raise DeployTaskError("deploy_task: func {} 参数不可用".format(func))
        self._deploy_task = func
        return func

    def check_deploy(self, func):
        if not callable(func):
            raise DeployTaskError("check_deploy func {} 参数不可用".format(func))
        self._check_deploy = func
        return func

    def test_cluster(self, func):
        if not callable(func):
            raise DeployTaskError("test_cluster func {} 参数不可用".format(func))
        self._get_test_cluster = func
        return func

    def test_micro_services(self, func):
        if not callable(func):
            raise DeployTaskError("test_micro_services func {} 参数不可用".format(func))
        self._get_test_micro_services = func
        return func

    def rollback(self, func):
        if not callable(func):
            raise DeployTaskError("rollback func {} 参数不可用".format(func))
        self._rollback = func
        return func

    def _run_before_deploy_task(self, task_stone):
        if not self._before_deploy:
            return
        result = {}
        for func in self._before_deploy:
            result[str(func.__name__)] = func(task_stone)
        task_stone.set_result("before_deploy", result)
        self.__finish_before_task = True

    def _run_after_deploy_task(self, task_stone):
        if not self._after_deploy:
            return
        result = {}
        for func in self._after_deploy:
            result[str(func.__name__)] = func(task_stone)
        task_stone.set_result("after_deploy", result)
        self.__finish_after_task = True

    def _run_deploy_task(self, task_stone):
        if not self._deploy_task:
            raise DeployTaskError("不能找到部署任务！")
        result = self._deploy_task(task_stone)
        task_stone.set_result("deploy", result)
        self.__finish_deploy_task = True

    def _run_rollback_task(self, task_stone):
        if not self._rollback:
            return
        result = self._rollback(task_stone)
        task_stone.set_result("rollback", result)
        self.__finish_rollback = True

    def _run_check_deploy(self, task_stone):
        if not self._check_deploy:
            raise DeployTaskError("不能找到部署后检查任务！")
        result = self._check_deploy(task_stone)
        if result is True:
            self.__finish_check_task = True
            return True
        if result is False:
            self.__finish_check_task = True
            self.__need_rollback = True
            return False
        raise DeployTaskError("部署检查任务必须返回 bool 类型的值")

    @staticmethod
    def get_cluster(cluster_args):
        cluster_type = cluster_args.runtime_type.strip()
        if not cluster_type:
            raise ArgsError("找不到集群类型: --cluster-type")

        cluster = Cluster(cluster_type)
        cluster_url = cluster_args.api_url.strip()
        if not cluster_url:
            raise ArgsError("找不到集群 API URL: --cluster-url")

        cluster_username = cluster_args.api_username.strip()
        if not cluster_username:
            raise ArgsError("找不到集群验证用户名: --cluster-username")

        cluster_password = cluster_args.api_password.strip()
        if not cluster_password:
            raise ArgsError("找不到集群验证密码: --cluster-password")
        cluster.set_connect(cluster_url, cluster_username, cluster_password)

        env_label = cluster_args.cluster_env.strip()
        if not env_label:
            raise ArgsError("找不到集群环境: --cluster-env")
        cluster.set_env_label(env_label)
        return cluster

    @staticmethod
    def get_micro_services(micro_services):
        result = []
        for m in micro_services:
            ms = MicroServices(m['ms_id'], m['package_type'])
            ms.set_package_info(m['package_name'], m['release_name'])
            ms.set_release_path(m['release_path'], m['token'])
            result.append(ms)
        return result

    def test_deploy(self):
        return

    def run(self):
        args = self.parser.parse_args()
        deploy = args.deploy.strip()
        cluster = None
        micro_services = []
        if deploy == "test":
            cluster = self._get_test_cluster()
            micro_services = self._get_test_micro_services()
        if deploy == "deploy":
            cluster = self.get_cluster(args)
            micro_services = self.get_micro_services(args.packages.strip())
        if cluster is None or not isinstance(cluster, Cluster):
            raise ArgsError("集群配置错误")
        task_stone = TaskStone(cluster, micro_services)
        self._run_before_deploy_task(task_stone)
        self._run_deploy_task(task_stone)
        if not self._run_check_deploy(task_stone):
            self._run_rollback_task(task_stone)
        else:
            self._run_after_deploy_task(task_stone)
