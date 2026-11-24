"""Puerto de Alto entre el bus y el controlador local; no depende de red ni modelos."""

from collections.abc import Callable

from ..actuator.halt import HaltController, HaltFailure, HaltReport


class StopGuard:
    def __init__(
        self,
        controller: HaltController,
        notify: Callable[[HaltReport], None] | None = None,
    ) -> None:
        self.controller = controller
        self.notify = notify
        self.last_report: HaltReport | None = None
        self.notification_failures = 0

    def _notify(self) -> None:
        if self.notify and self.last_report:
            try:
                self.notify(self.last_report)
            except Exception:
                self.notification_failures += 1

    def halt(self) -> None:
        try:
            self.last_report = self.controller.halt()
        except HaltFailure as error:
            self.last_report = error.report
            self._notify()
            raise HaltFailure(error.report) from None
        self._notify()
