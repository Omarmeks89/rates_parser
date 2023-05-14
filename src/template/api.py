from .core_presets import command_filters as cf
from .core_presets import api_router
from .core_presets import CmdKey
from .core_presets import receiver
from .messages import LoadExcelFile
from .messages import LoadTxtFile
from .messages import SaveExcelFile


MEMORY_SAFE_LOAD_MODE: bool = False
WRITE_ONLY: bool = False


@api_router.route(CmdKey.LOADFILE)
def load_excel_file(
        cmd: cf.TerminalCommand
        ) -> None:
    filename = ''.join(cmd.args)
    _cmd = LoadExcelFile(
            name=cmd.cmd,
            path=cmd.path,
            flag=cmd.flag,
            mode=MEMORY_SAFE_LOAD_MODE,
            fname=filename,
            suffix=cmd.suffix
            )
    receiver.receive(_cmd)


@api_router.route(CmdKey.LOADFILE)
def load_txt_file(
        cmd: cf.TerminalCommand
        ) -> None:
    filename = ''.join(cmd.args)
    load_txt = LoadTxtFile(
            name=cmd.cmd,
            path=cmd.path,
            flag=cmd.flag,
            mode='r',
            fname=filename,
            suffix=cmd.suffix
            )
    receiver.receive(load_txt)


@api_router.route(CmdKey.SAVEFILE)
def save_excel_file(
        cmd: cf.TerminalCommand,
        ) -> None:
    cached_fname = ''.join(cmd.args)
    save_xl_file = SaveExcelFile(
            name=cmd.cmd,
            path=cmd.path,
            flag=cmd.flag,
            mode=WRITE_ONLY,
            fname=cached_fname,
            suffix=cmd.suffix,
            )
    receiver.receive(save_xl_file)
