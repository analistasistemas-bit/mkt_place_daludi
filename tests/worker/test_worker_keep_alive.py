import importlib
import sys
import types
import unittest
from unittest.mock import patch


def load_worker_module():
    sys.modules.pop("apps.worker.worker", None)
    rq_stub = types.SimpleNamespace(Worker=object, Queue=object, Connection=object)
    with patch.dict(sys.modules, {"rq": rq_stub}):
        return importlib.import_module("apps.worker.worker")


worker = load_worker_module()


class StartKeepAliveThreadTests(unittest.TestCase):
    def test_start_keep_alive_thread_uses_daemon_background_thread(self):
        with patch.object(worker.threading, "Thread") as thread_cls:
            thread = thread_cls.return_value

            worker.start_keep_alive_thread()

            thread_cls.assert_called_once_with(
                target=worker.keep_alive_loop,
                kwargs={
                    "interval_seconds": worker.KEEP_ALIVE_INTERVAL_SECONDS,
                    "url": worker.KEEP_ALIVE_URL,
                    "timeout_seconds": worker.KEEP_ALIVE_TIMEOUT_SECONDS,
                },
                daemon=True,
                name="render-worker-keep-alive",
            )
            thread.start.assert_called_once_with()


class KeepAliveLoopTests(unittest.TestCase):
    def test_keep_alive_loop_pings_url_before_first_sleep(self):
        slept = []
        pinged = []

        def fake_sleep(seconds):
            slept.append(seconds)
            raise StopIteration

        def fake_ping(*, url, timeout_seconds):
            pinged.append((url, timeout_seconds))
            if len(pinged) == 1:
                return

        with self.assertRaises(StopIteration):
            worker.keep_alive_loop(
                interval_seconds=240,
                url="https://mktplace-worker.onrender.com/",
                timeout_seconds=9,
                sleep_fn=fake_sleep,
                ping_fn=fake_ping,
            )

        self.assertEqual(
            pinged,
            [
                ("https://mktplace-worker.onrender.com/", 9),
            ],
        )
        self.assertEqual(slept, [240])

    def test_keep_alive_loop_ignores_ping_failures_and_keeps_running(self):
        slept = []
        pinged = []

        def fake_sleep(seconds):
            slept.append(seconds)
            if len(slept) == 2:
                raise StopIteration

        def fake_ping(*, url, timeout_seconds):
            pinged.append((url, timeout_seconds))
            raise RuntimeError("network issue")

        with self.assertRaises(StopIteration):
            worker.keep_alive_loop(
                interval_seconds=120,
                url="https://mktplace-worker.onrender.com/",
                timeout_seconds=5,
                sleep_fn=fake_sleep,
                ping_fn=fake_ping,
            )

        self.assertEqual(slept, [120, 120])
        self.assertEqual(
            pinged,
            [
                ("https://mktplace-worker.onrender.com/", 5),
                ("https://mktplace-worker.onrender.com/", 5),
            ],
        )


if __name__ == "__main__":
    unittest.main()
