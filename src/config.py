import typing
import types

from core import core_utils as cu
from core import command_filters as cmd_filters
from core import registrator
from core import api_router
from core import channels
from core import Cache
from core import messages as cm
from core import terminal_commands as tc
from core.settings import settings as cs
from template import handlers as th
from template import messages as tm
from template import tmp_models
from view import handlers as vh
from view import messages as vm
import services.services as srv
import services.drivers as drv


_LOG_FMT: str = '%(name)s %(asctime)s %(funcName)s %(lineno)s %(message)s'
_LOG_NAME: str = 'TestSystemLogger'
_LOG_LEVEL: str = 'DEBUG'


class SystemConfigurationError(Exception):
    pass


class LogSettings(typing.NamedTuple):
    name: str = _LOG_NAME
    fmt: str = _LOG_FMT
    log_level: str = _LOG_LEVEL


log_settings = LogSettings()
logger = cu.BaseLogger(log_settings)
system_logger = logger.get_logger
api_router.set_logger(system_logger)

FILTERS: types.MappingProxyType = types.MappingProxyType(
        {
            cmd_filters.PATH_FILTER_KEY: cmd_filters.FetchSuffixFilter,
            cmd_filters.ARGS_FILTER_KEY: cmd_filters.ArgsToListFilter
        }
    )


# Terminal command postpocessing settings.
Postprocessor = cmd_filters.PostProcessor()
cmd_filters.set_postprocessor_filters(
        Postprocessor,
        FILTERS
        )


excel_compiler = drv.ExcelCompiler()
txt_compiler = drv.TxtCompiler()


basedriver = drv.ExcelDriver(
        system_logger,
        excel_compiler
        )
txt_driver = drv.TxtDriver(
        system_logger,
        txt_compiler
        )
xl_save_drv = drv.ExcelSaveDriver(system_logger)


# data parsing patterns configuration
# load_config == OrderdDict

load_config = cs.make_config(path=cs._make_dotenv_path())
readers = tc.get_readers_repo()
writers = tc.get_writers_repo()
flags = tc.flags()

# readers subscribing
readers.add('.xlsx', (basedriver, srv.ExcelFileReader()))
readers.add('.txt', (txt_driver, srv.TxtFileReader()))

# writers subscribing
writers.add(".xlsx", (xl_save_drv, srv.ExcelFileWriter()))


flags.add(
        tc.CommandFlag.MULTY,
        cs.build_patterns_map(
            cs.MULTY_HEADERS_KEY,
            load_config
            )
        )
flags.add(
        tc.CommandFlag.RAIL,
        cs.build_patterns_map(
            cs.RAIL_HEADERS_KEY,
            load_config
            )
        )
baseloader = drv.LoadConfigurator(readers, flags)
basedumper = drv.DumpConfigurator(writers)
# dummy - dumper
sheet_model = tmp_models.SheetTemplate()
repository = srv.BaseFileIOAdapter(baseloader, basedumper, sheet_model)
uow = srv.FileOperator(repository, system_logger)


# channels subscribe on event types
registrator.register_channel(cm.Command, channels.Channel())


# cmd hadlers setup
load_excel_hnd = th.LoadExcelFileCmdHandler(uow, Cache)
show_model_prev_hnd = vh.ShowPreviewCmdHandler(uow, Cache)
load_txt_hnd = th.LoadTxtFileCmdHandler(uow, Cache)
save_xl_file = th.SaveExcelFileCmdHandler(uow, Cache)


# cmd handlers subscribe on channels
registrator.register_handler(tm.LoadExcelFile, [load_excel_hnd, ])
registrator.register_handler(vm.ShowModelPreview, [show_model_prev_hnd, ])
registrator.register_handler(tm.LoadTxtFile, [load_txt_hnd, ])
registrator.register_handler(tm.SaveExcelFile, [save_xl_file, ])


def on_startup() -> None:
    try:
        from core import registrator
    except ImportError as e:
        raise SystemConfigurationError(e)

    if registrator.can_setup():
        try:
            registrator.setup_eventsystem()
        except Exception as e:
            msg = f'Application bootstrap failed with err: {e}.'
            raise SystemConfigurationError(msg)


def on_shutdown() -> None:
    ...


ValidationError = tc.ValidationError


__all__ = [
        'uow',
        'system_logger',
        'Postprocessor',
        'cmd_filters',
        'on_startup',
        'on_shutdown',
        'api_router',
        'registrator',
        'ValidationError'
        ]
