import io
import json
import logging
from pathlib import Path
from uuid import uuid4

from coalsense_common import AppError, configure_logging, get_logger


def test_scrub(capsys):
    marker = str(uuid4())
    configure_logging("DEBUG", content_keys=["private"])
    log = get_logger("scrub")
    assert isinstance(log, logging.Logger)
    data = {
        key: marker
        for key in (
            "text",
            "body",
            "dictation",
            "profile",
            "filename",
            "recipient",
            "prompt",
            "completion",
            "email_body",
            "userText",
            "PRIVATE",
            "audio",
            "video",
            "landmarks",
        )
    }
    log.info(
        "auth.code_sent",
        extra={"nested": [data], "unknown": marker * 3, "id": "request-1", "short": "x" * 64},
    )
    output = capsys.readouterr().err
    assert marker not in output
    record = json.loads(output)
    assert record["extra"]["nested"] == [{}]
    assert record["extra"]["unknown"] == "[omitido]"
    assert record["extra"]["short"] == "x" * 64
    assert record["extra"]["id"] == "request-1"
    assert data["text"] == marker


def test_exceptions_args_and_record(capsys):
    marker = str(uuid4())
    configure_logging("INFO")
    log = get_logger("exceptions")
    log.info("event.failed %s", marker)
    try:
        raise ValueError(marker)
    except ValueError:
        log.exception("event.failed", stack_info=True)
    record = log.makeRecord(
        log.name,
        logging.ERROR,
        __file__,
        1,
        "event.failed",
        (),
        None,
        extra={"error": AppError("E_TEST", marker, False, [marker])},
    )
    record.exc_text = marker
    log.handle(record)
    output = capsys.readouterr().err
    assert marker not in output
    records = [json.loads(line) for line in output.splitlines()]
    assert records[0]["message"] == "[omitido]"
    assert records[1]["exception"]["type"] == "ValueError"
    assert records[1]["exception"]["id"]
    assert records[2]["extra"]["error"]["code"] == "E_TEST"


def test_cycles_objects_levels_and_reconfiguration(capsys):
    class Unsafe:
        def __str__(self):
            raise AssertionError("must not stringify")

    cycle = []
    cycle.append(cycle)
    configure_logging("WARNING")
    log = get_logger("repeat")
    log.info("event.hidden")
    assert capsys.readouterr().err == ""
    configure_logging("INFO")
    log.info("event.ok", extra={"cycle": cycle, "object": Unsafe(), "n": float("nan")})
    record = json.loads(capsys.readouterr().err)
    assert record["extra"]["cycle"] == ["[omitido]"]
    assert record["extra"]["object"] == "[omitido]"


def _events(output):
    return [json.loads(line) for line in output.splitlines()]


def test_child_logger_propagation_is_scrubbed(capsys):
    marker = str(uuid4())
    configure_logging("INFO")
    get_logger("auth")
    child = logging.getLogger("coalsense.auth.sub")
    child.info(f"dictated {marker} %s", marker, extra={"note": marker * 3, "text": marker})
    child.info("event.args %(a)s", {"a": marker}, extra={"nested": {"deep": [{"body": marker}]}})
    output = capsys.readouterr().err
    assert marker not in output
    first, second = _events(output)
    assert first["message"] == "[omitido]"
    assert first["extra"] == {"note": "[omitido]"}
    assert second["extra"]["nested"] == {"deep": [{}]}


def test_second_handler_and_root_propagation_are_scrubbed(capsys):
    from coalsense_common.logging import _JsonFormatter

    marker = str(uuid4())
    configure_logging("INFO")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(_JsonFormatter())  # no scrub filter: the formatter must scrub
    root, other = logging.getLogger(), logging.getLogger("coalsense.unowned")
    root.addHandler(handler)
    try:
        other.warning(f"raw {marker}", extra={"text": marker, "note": marker * 3})
        get_logger("auth").info(f"raw {marker}", extra={"body": marker})
    finally:
        root.removeHandler(handler)
    # Owned loggers do not propagate to root; the unowned record reaches it scrubbed.
    assert marker not in stream.getvalue() + capsys.readouterr().err
    (record,) = _events(stream.getvalue())
    assert record["message"] == "[omitido]"
    assert record["extra"] == {"note": "[omitido]"}


def test_chained_exceptions_never_leak(capsys):
    marker = str(uuid4())
    configure_logging("INFO")
    log = get_logger("chained")
    try:
        try:
            raise ValueError(marker)
        except ValueError as cause:
            raise RuntimeError(f"wrapped {marker}") from cause
    except RuntimeError:
        log.exception("event.failed")
    try:
        try:
            raise KeyError(marker)
        except KeyError:
            raise OSError(marker)  # noqa: B904 - implicit __context__ is the case under test
    except OSError as error:
        log.error("event.failed", exc_info=error, extra={"error": error})
    output = capsys.readouterr().err
    assert marker not in output
    first, second = _events(output)
    assert first["exception"]["type"] == "RuntimeError"
    assert second["extra"]["error"]["type"] == "OSError"


def test_stack_info_is_dropped_entirely(capsys):
    marker = str(uuid4())
    configure_logging("INFO")
    log = get_logger("stack")

    def emit():
        log.info("event.stack", stack_info=True)

    # The marker lives in the frame's function name, so a leaked stack would contain it.
    emit.__code__ = emit.__code__.replace(co_name="f_" + marker.replace("-", "_"))
    emit()
    output = capsys.readouterr().err
    assert marker.replace("-", "_") not in output
    assert "Stack" not in output and "Traceback" not in output
    assert set(json.loads(output)) == {"timestamp", "level", "logger", "message", "extra"}


def test_arguments_extra_and_unusual_values(capsys):
    class Leaky:
        def __repr__(self):
            return marker

    marker = str(uuid4())
    configure_logging("INFO")
    log = get_logger("values")
    log.info("event.%s.%s", marker, marker)
    log.info(
        "event.extra",
        extra={
            "a": {"b": [{"c": {"d": marker * 3, "Prompt": marker}}], "e": (marker * 3,)},
            "set": {marker},
            "bytes": marker.encode(),
            "obj": Leaky(),
            "k": {1: marker, marker * 3: "x"},
        },
    )
    output = capsys.readouterr().err
    assert marker not in output
    _, second = _events(output)
    assert second["extra"]["a"] == {"b": [{"c": {"d": "[omitido]"}}], "e": ["[omitido]"]}
    assert second["extra"]["set"] == second["extra"]["obj"] == "[omitido]"
    assert second["extra"]["k"] == {}


def test_file_names_are_content(capsys):
    marker = str(uuid4())
    configure_logging("INFO")
    keys = ["file_name", "fileName", "file-name", "FILE_PATH", "filePath", "path", "attach_path"]
    get_logger("files").info("event.file", extra={**dict.fromkeys(keys, marker), "file_id": "f-1"})
    output = capsys.readouterr().err
    assert marker not in output
    assert json.loads(output)["extra"] == {"file_id": "f-1"}


def test_standard_attributes_survive_for_other_formatters():
    configure_logging("INFO")
    log = get_logger("standard")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(log.handlers[0].filters[0])
    handler.setFormatter(logging.Formatter("%(filename)s|%(pathname)s|%(funcName)s|%(message)s"))
    log.addHandler(handler)
    log.info("event.standard")
    # Source-code file is metadata (kept on the record); user file names are scrubbed above.
    name = test_standard_attributes_survive_for_other_formatters.__name__
    assert stream.getvalue() == f"{Path(__file__).name}|{__file__}|{name}|event.standard\n"


def test_configure_without_keys_keeps_custom_keys(capsys):
    marker = str(uuid4())
    configure_logging("INFO", content_keys=["Secret_Note", ""])
    configure_logging("INFO")  # must not forget earlier custom keys
    get_logger("keys").info("event.keys", extra={"secretnote": marker, "my_secret_note": marker})
    output = capsys.readouterr().err
    assert marker not in output
    assert json.loads(output)["extra"] == {}
