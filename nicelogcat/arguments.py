from colorama import Fore, Back
from colorama.ansi import AnsiCodes
from collections import Counter
from dataclasses import Field, dataclass, field
from enum import Enum
from pynput import keyboard
from jsonargparse import (
    ArgumentParser,
    ActionParser,
    ActionConfigFile,
    SUPPRESS
)
from typing import List, TypeVar

from nicelogcat.utils import r_merge_dicts

ArgType = TypeVar("ArgType")


class FilterType(Enum):
    all = "all"
    any = "any"


##############################################################
# Argument Dataclasses
##############################################################
@dataclass
class AlignArgs:
    header_len_counter: Counter = Counter()
    header_freq_counter: Counter = Counter()
    header_occurence_check_limit = 5000
    header_most_freq_line = ""
    header_max_len_with_padding = -1
    off: bool = True


@dataclass
class ColorArgs:
    header: AnsiCodes = Back.YELLOW + Fore.BLACK
    log_warn: AnsiCodes = Fore.YELLOW
    log_error: AnsiCodes = Fore.RED
    log_info: AnsiCodes = Fore.GREEN
    time: AnsiCodes = Fore.YELLOW
    current_time: AnsiCodes = Fore.RED
    prefix: AnsiCodes = Fore.GREEN
    title: AnsiCodes = Fore.MAGENTA
    highlight: AnsiCodes = Back.RED + Fore.BLACK,
    highlight_off: AnsiCodes = Fore.BLACK + Back.YELLOW
    highlight_off_filter: AnsiCodes = Fore.GREEN + Back.BLACK,
    value: AnsiCodes = Fore.WHITE
    key: AnsiCodes = Fore.CYAN
    stacktrace_msg: AnsiCodes = Fore.GREEN,
    path: AnsiCodes = Fore.LIGHTMAGENTA_EX
    timing: AnsiCodes = Back.RED + Fore.BLACK
    change_detected: AnsiCodes = Back.RED + Fore.BLACK


@dataclass
class HighlightArgs:
    phrases: List[str] = field(default_factory=list)
    prefixes: List[str] = field(default_factory=list)
    off: bool = False


@dataclass
class FilterArgs:
    include: List[str] = field(default_factory=list)
    include_type: FilterType = FilterType.all
    exclude: List[str] = field(default_factory=list)
    exclude_type: FilterType = FilterType.any
    prefixes: List[str] = field(default_factory=list)
    exclude_prefixes: List[str] = field(default_factory=list)
    log_levels: List[str] = field(default_factory=list)
    off: bool = False


@dataclass
class LayoutArgs:
    linespace: int = 0
    divider: bool = False
    flat: bool = False
    no_flat: bool = False
    per_line: int = 4
    header_spacer: str = "\n"


@dataclass
class LineArgs:
    title: str = "all"
    raw: bool = False
    no_date: bool = False
    no_secs: bool = False
    show_title: bool = False
    align_head: bool = False
    no_align_head: bool = False
    align_simple: bool = False
    random_color: bool = False
    random_color_background: bool = False
    random_color_message: bool = False
    no_random_color: bool = False
    left_of_key: str = "["
    right_of_key: str = "]"
    off: bool = False


@dataclass
class MetricArgs:
    common_msgs: dict = field(default_factory=dict)
    common_msgs_to_raw: dict = field(default_factory=dict)
    common_msgs_timeframe_secs: int = 120
    off: bool = True


@dataclass
class RecordArgs:
    dir: str = ""
    keys: List[str] = field(default_factory=list)
    key_diff: dict = field(default_factory=dict)
    off: bool = True
    key: str = keyboard.Key.f12
    init_recording_state: bool = True
    filename: str = ""
    is_recording: bool = False


@dataclass
class StacktraceArgs:
    num_stack_traces: int = 10
    prev_lines_before_stacktrace: int = 4
    off: bool = True
    stacktrace_map: dict = field(default_factory=dict)
    stacktrace_colors: dict = field(default_factory=dict)


##############################################################
# Main argument export
##############################################################
def arg_options(no_help: bool = False, **kwargs: dict) -> dict:
    _args = {}
    if "no_help" in kwargs:
        no_help = kwargs.pop()
    _args |= kwargs
    if no_help:
        _args["help"] = SUPPRESS
    return _args


@dataclass
class NiceLogCatArgs:

    @staticmethod
    def cfg_parser(with_cfg: bool = False,
                   no_help: bool = False) -> ArgumentParser:
        parser = ArgumentParser()
        parser.add_dataclass_arguments(
            AlignArgs,
            **(arg_options(nested_key="align",
                           default=AlignArgs(),
                           no_help=no_help)))
        parser.add_dataclass_arguments(
            FilterArgs,
            **(arg_options(nested_key="filter",
                           default=FilterArgs(),
                           no_help=no_help)))
        parser.add_dataclass_arguments(
            HighlightArgs,
            **(arg_options(nested_key="highlight",
                           default=HighlightArgs(),
                           no_help=no_help)))
        parser.add_dataclass_arguments(
            LayoutArgs,
            **(arg_options(nested_key="layout",
                           default=LayoutArgs(),
                           no_help=no_help)))
        parser.add_dataclass_arguments(
            LineArgs,
            **(arg_options(nested_key="line", default=LineArgs(),
                           no_help=no_help)))
        parser.add_dataclass_arguments(
            RecordArgs,
            **(arg_options(nested_key="record",
                           default=RecordArgs(),
                           no_help=no_help)))
        parser.add_dataclass_arguments(
            StacktraceArgs,
            **(arg_options(nested_key="stacktrace",
                           default=StacktraceArgs(),
                           no_help=no_help)))
        if with_cfg:
            parser.add_argument('--load', action=ActionConfigFile)
        return parser


@dataclass
class Args:
    align: AlignArgs
    color: ColorArgs
    filter: FilterArgs
    highlight: HighlightArgs
    layout: LayoutArgs
    line: LineArgs
    metric: MetricArgs
    record: RecordArgs
    stacktrace: StacktraceArgs


def get_arguments():
    cliparser: ArgumentParser = NiceLogCatArgs.cfg_parser()
    configparser: ArgumentParser = NiceLogCatArgs.cfg_parser(with_cfg=True,
                                                             no_help=True)
    action_configparser = ActionParser(configparser)
    cliparser.add_argument("--config",
                           action=action_configparser,
                           help=SUPPRESS)
    joined_parser = cliparser.parse_args()

    cli_args: dict = joined_parser.as_dict()
    config_args: dict = cli_args.pop("config")

    if "load" in config_args:
        config_args.pop("load")
    if "__path__" in config_args:
        config_args.pop("__path__")

    main_args: dict = r_merge_dicts(config_args, cli_args)
    args_field_dict = Args.__dataclass_fields__
    for arg_type, value in main_args.items():
        arg_field = args_field_dict[arg_type]
        cls_type: Field = arg_field.type
        main_args[arg_type] = cls_type(**value)

    missing_args = {
        arg_type: args_field
        for arg_type, args_field in args_field_dict.items()
        if arg_type not in main_args
    }

    for arg_type, arg_field in missing_args.items():
        arg_field: Field
        cls_type = arg_field.type
        main_args[arg_type] = cls_type()
    main_args = Args(**main_args)
    return main_args