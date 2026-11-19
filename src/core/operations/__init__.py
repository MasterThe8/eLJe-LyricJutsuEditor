"""Operasi Jutsu — murni Python (tanpa import GUI).

Setiap fungsi publik menerima teks script editor dan mengembalikan teks baru, atau melempar ``JutsuError``.
"""
from core.operations.add_lyric import (  # noqa: F401
    ADD_FAKE_NEXT,
    ADD_HIDE_NEXT,
    ADD_NO_SLIDEUP,
    build_add_jutsu_text,
)
from core.operations.batch_jutsu import (  # noqa: F401
    MIN_TICK_GAP,
    BatchMode,
    BatchTarget,
    EventCollisionError,
    RowValueError,
    RowValues,
    TableColumn,
    TargetSpec,
    TickTooCloseError,
    apply_batch_jutsu,
    carry_over_values,
    check_row_values,
    check_tick_spacing,
    default_row_values,
    extract_targets,
    parse_target_input,
    table_columns,
)
from core.operations.color_builders import (  # noqa: F401
    NEXT_PHRASE_ADD,
    NEXT_PHRASE_HIDE,
    NEXT_PHRASE_SHOW,
)
from core.operations.convert_phrase import apply_kan2rom  # noqa: F401
from core.operations.errors import JutsuError  # noqa: F401
from core.operations.jutsu_edit import apply_jutsu_edit  # noqa: F401
from core.operations.jutsu_scan import JutsuBlock, find_jutsu_blocks  # noqa: F401
from core.operations.lyric_color_method1 import apply_lyric_color_method1  # noqa: F401
from core.operations.lyric_color_method2 import apply_lyric_color_method2  # noqa: F401
from core.operations.text_patch import TextPatch, make_patch  # noqa: F401
