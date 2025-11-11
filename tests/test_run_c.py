from pathlib import Path

import correction_helper as checker
import pytest


def test_writes_on_stderr(tmp_path):
    main = tmp_path / "main.c"
    main.write_text(
        r"""
#include <unistd.h>

int main(void) {
    write(2, "Hello\n", 6);
    return 0;
}
""",
        encoding="UTF-8",
    )

    checker.run(
        "gcc",
        *checker.CFLAGS,
        str(main),
        "-o",
        str(tmp_path / "main"),
        encoding="UTF-8",
    )
    with pytest.raises(SystemExit):
        checker.run_c(str(tmp_path / "main"))
