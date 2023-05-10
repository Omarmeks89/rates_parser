from config import system_logger as logger
from config import cmd_filters as cf
from config import Postprocessor
from config import on_startup
from config import on_shutdown
from config import api_router
from config import ValidationError


def main() -> None:
    """Application main_loop() func."""

    _running = False
    try:
        on_startup()
        _running = True
    except Exception as err:  # BootstrapError(msg)
        logger.critical(err)

    while _running:
        raw_cmd = cf.read_terminal_cmd()
        if raw_cmd:
            template = cf.PreProcessor.make_cmd_template(raw_cmd)
            try:
                term_command = Postprocessor.make_command_from(template)
                cf.check_command_subscribed(
                        term_command,
                        api_router.controllers
                        )
                api_router.dispatch(term_command.cmd, term_command)
            except cf.SystemValidationError as err:
                logger.critical(err)
            except cf.PostprocessorError as err:
                logger.critical(err)
            except ValidationError as err:
                logger.critical(err)
    else:
        on_shutdown()


if __name__ == "__main__":
    main()
