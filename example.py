from dao_deploy import Deploy

d = Deploy()


@d.before_deploy
def do_something_before_deploy_0(task_stone):
    task_stone.logger.info("do something before deploy: task 0")


@d.before_deploy
def do_something_before_deploy_1(task_stone):
    task_stone.logger.info("do something before deploy: task 1")


@d.after_deploy
def do_something_after_deploy_0(task_stone):
    task_stone.logger.info("do something after deploy: task 0")


@d.after_deploy
def do_something_after_deploy_1(task_stone):
    task_stone.logger.info("do something after deploy: task 1")


@d.deploy_task
def do_deploy(task_stone):
    task_stone.logger.info("do deploy...")
    task_stone.logger.info("finish.")


@d.check_deploy
def check_deploy_is_success(task_stone):
    task_stone.logger.info("check instance...")
    task_stone.logger.info("deploy success!")
    return True


@d.rollback
def rollback_when_failed(task_stone):
    task_stone.logger.info("rollback...")


if __name__ == "__main__":
    d.run()
