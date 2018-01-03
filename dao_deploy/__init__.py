import argparse

USAGE = """
执行部署任务：

    python3 deploy.py deploy

测试部署逻辑：

    python3 deploy.py test

"""
DESC = """

DaoCloud Services 2.0 部署脚本


                         ,                              
                     `:;;;                              
                   ,;;;;;;                              
                `;;;;;;;;;   `                          
              .;;;;;;;;;;;   ;;        `;:,,            
            .;;;;;;;;;;;;;   ;;;:                       
           ;;;;;;;;;;;;;;;   ;;;;;                      
         ,;;;;;;;;;;;;;;;;   ;;;;;;,                    
        ;;;;;;;;;;;;;;;;;;   ;;;;;;;;                   
       ;;;;;;;;;;;;;;;;;;;   ;;;;;;;;;                  
      ;;;;;;;;;;;;;;;;;;;;   ;;;;;;;;;;                 
     ;;;;;;;;;;;;;;;;;;;;;   ;;;;;;;;;;;                
     ;;;;;;;;;;;;;;;;;;;;;   ;;;;;;;;;;;;               
    ``````````````````````   `````````````              
                      ``..,::;;;;;;;;;;;:,,..`          
   ``````....``````         ```....``                   
               ```````                                  
     
      START SAILING, FOREVER AND ALWAYS

"""


class ArgsError(Exception):
    pass


class DeployTaskError(Exception):
    pass


class StoneKeyError(Exception):
    pass


class Cluster(object):
    """
    Cluster Info.
    """

    def __init__(self, cluster_type):
        self.cluster_type = cluster_type

        self.cluster_url = None
        self.cluster_username = None
        self.cluster_password = None

        self.cluster_env = None

    def set_connect(self, cluster_url, cluster_username, cluster_password):
        self.cluster_url = cluster_url
        self.cluster_username = cluster_username
        self.cluster_password = cluster_password

    def set_env_label(self, env_label):
        self.cluster_env = env_label


class TaskStone(object):
    def __init__(self, cluster, micro_services):
        self._stone = {
            'micro_services': micro_services,
            'cluster': cluster,
            'config': {},
            'result': {}
        }

    def set_config(self, key, value):
        self._stone['config'][key] = value

    def set_result(self, key, value):
        self._stone['result'][key] = value

    def set_value(self, key, value):
        if key in ['cluster', 'micro_services', 'config', 'result']:
            raise StoneKeyError("不能使用 {} 作为 key。".format(key))
        self._stone[key] = value

    def get_value(self, key, default=None):
        return self._stone.get(key, default=default)


class MicroServices(object):
    """
    MicroServices Info.
    """

    def __init__(self, ms_id, package_type):
        self.ms_id = ms_id
        self.package_type = package_type
        self.package_name = None
        self.release_name = None

        self.release_path = None
        self.token = None

    def set_package_info(self, package_name, release_name):
        self.package_name = package_name
        self.release_name = release_name

    def set_release_path(self, release_path, token):
        self.release_path = release_path
        self.token = token


class Deploy(object):
    def __init__(self):
        self.parser = self.init_parser()
        self._before_deploy = []
        self._after_deploy = []
        self._deploy_task = None
        self._check_deploy = None
        self._rollback = None

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
            return
        if result is False:
            self.__finish_check_task = True
            self.__need_rollback = True
            return
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
        if deploy == "test":
            self.test_deploy()
            return
        cluster = self.get_cluster(args)
        micro_services = self.get_micro_services(args.packages.strip())
        task_stone = TaskStone(cluster, micro_services)
        self._run_before_deploy_task(task_stone)
        self._run_deploy_task(task_stone)
        if not self._run_check_deploy(task_stone):
            self._run_rollback_task(task_stone)
        else:
            self._run_after_deploy_task(task_stone)


d = Deploy()


@d.deploy_task
def deploy_task(task_stone):
    print("deploy...")
    print("finish.")


@d.check_deploy
def check_deploy(task_stone):
    print("checking instance...")
    print("deploy success!")
    return True


if __name__ == "__main__":
    d.run()
