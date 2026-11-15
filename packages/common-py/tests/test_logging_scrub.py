import json
import logging
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
