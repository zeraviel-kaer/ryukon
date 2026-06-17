from __future__ import annotations

import asyncio
from typing import Callable, Awaitable


class Timer:
    """Повторяет callback каждые interval секунд.

    timer = ryukon.Timer(interval=1.0, callback=my_func)
    timer.start()
    timer.stop()
    """

    def __init__(
        self,
        *,
        interval:  float,
        callback:  Callable[..., Awaitable],
        autostart: bool = False,
    ) -> None:
        self._interval = interval
        self._callback = callback
        self._running  = False
        self._task:    asyncio.Task | None = None

        if autostart:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self._auto_start())
            except RuntimeError:
                pass

    async def _auto_start(self) -> None:
        await asyncio.sleep(0)
        self.start()

    def start(self) -> None:
        """Запускает таймер."""
        if self._running:
            return
        self._running = True
        self._task    = asyncio.get_event_loop().create_task(self._run())

    def stop(self) -> None:
        """Останавливает таймер."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None

    def restart(self) -> None:
        """Перезапускает таймер."""
        self.stop()
        self.start()

    @property
    def running(self) -> bool:
        return self._running

    async def _run(self) -> None:
        try:
            while self._running:
                await asyncio.sleep(self._interval)
                if self._running:
                    await self._callback()
        except asyncio.CancelledError:
            pass  # нормальная остановка