import six
from .deploy import Deploy
from .errors import DeployTaskError

if six.PY2:
    print("Python 2.7 will not be maintained past 2020.")
    raise DeployTaskError("部署脚本不支持 Python2, 请使用 Python3")
