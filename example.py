from dao_deploy import Deploy

d = Deploy()


@d.before_deploy
def do_something_before_deploy_0(task_stone):
    print("do something before deploy: task 0")


@d.before_deploy
def do_something_before_deploy_1(task_stone):
    print("do something before deploy: task 1")


@d.after_deploy
def do_something_after_deploy_0(task_stone):
    print("do something after deploy: task 0")


@d.after_deploy
def do_something_after_deploy_1(task_stone):
    print("do something after deploy: task 1")


@d.deploy_task
def do_deploy(task_stone):
    print("do deploy...")
    print("finish...")


@d.check_deploy
def check_deploy_is_success(task_stone):
    print("check instance...")
    print("deploy success!")
    return True


@d.rollback
def rollback_when_failed(task_stone):
    print("rollback...")


if __name__ == "__main__":
    d.run()
