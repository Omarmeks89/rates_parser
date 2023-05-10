from .core_presets import command_filters as cf
from .core_presets import CmdKey
from .core_presets import receiver
from .messages import ShowModelPreview
from .core_presets import api_router


@api_router.route(CmdKey.SHOWPREV.value)
def display_preview(
        cmd: cf.TerminalCommand
        ) -> None:
    filename = ''.join(cmd.args)
    _cmd = ShowModelPreview(
            name=cmd.cmd,
            fname=filename
            )
    receiver.receive(_cmd)
