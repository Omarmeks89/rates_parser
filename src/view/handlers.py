import typing
import sys

from .core_presets import handlers as h
from .core_presets import Cache
from .messages import ShowModelPreview
from services.preview_builders import PreviewFactory, PreviewSettingsFactory


def draw_preview(preview: typing.Generator) -> None:
    for line in preview:
        print(line, file=sys.stdout)


class ShowPreviewCmdHandler(h.Handler):

    def __init__(
            self,
            uow: typing.Any,
            cache: Cache
            ):
        self._uow = uow
        self._cache = cache

    def fetch_events(self) -> typing.List[typing.Any]:
        return self._uow.events

    def handle(
            self,
            cmd: ShowModelPreview
            ) -> None:
        with self._uow:

            preview_fact = None
            prev_set_factory = None
            sheet = None
            pr_settings = None

            model = self._cache.get(cmd.fname)
            if model:
                sheet = model.get_sheet_struct
                preview_fact = PreviewFactory()
                prev_set_factory = PreviewSettingsFactory()
            try:
                if prev_set_factory.sheet_is_valid(sheet):
                    prev_set_factory.calculate_preview_settings(sheet)
                    pr_settings = prev_set_factory.preview_settings

                if preview_fact.pair_is_valid(sheet, pr_settings):
                    preview_fact.create_preview(sheet, pr_settings)
                    draw_preview(preview_fact.preview)

            except Exception as e:
                msg = f'Command preview creation failed: {e}.'
                raise Exception(msg)
