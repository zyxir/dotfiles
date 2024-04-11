"""Utility for Rime configuration."""


from installer.job import Job
from installer.opt import Options
from installer.path import to_path


def win_rime_setup(opt: Options) -> None:
    """Do extra setup for Rime on Windows, handling errors."""
    msg = "Configuring the Cangjie6 schema"

    def action() -> None:
        win_configure_cangjie6(opt)

    Job(msg, action).run()


def win_configure_cangjie6(opt: Options) -> None:
    """Write the additional configuration file for the Cangjie6 schema."""
    if opt.dry:
        return

    path = to_path("%appdata%/rime/cangjie6.custom.yaml")
    content = """
patch:
  "switches/@2/reset": 1
    """
    with open(path, "w") as fp:
        fp.write(content)
