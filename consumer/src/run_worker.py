from config.settings import AppConfig
from worker.base import Consumer
from models.enums import WorkerType
from models.misc import get_console_handler, date_time_now_utc
import logging
import time


def main(cfg: AppConfig):

    start = time.perf_counter()
    # BookingWorker
    booking_worker = Consumer(
        cfg, WorkerType.BOOKING, cfg.queue_names[1], cfg.queue_names[1]
    )

    # SearchWorker
    search_worker = Consumer(
        cfg, WorkerType.SEARCH, cfg.queue_names[0], cfg.queue_names[0]
    )

    # GenericWorker
    generic_worker = Consumer(
        cfg, WorkerType.GENERIC, cfg.queue_names[3], cfg.queue_names[3]
    )

    # Start processes
    booking_worker.start()
    search_worker.start()
    generic_worker.start()

    end = time.perf_counter()

    cfg.logger.info(
        f"""Started processes:{booking_worker.pid},{search_worker.pid},
        {generic_worker.pid}
        in {end - start:.4f} seconds. {date_time_now_utc()}"""
    )
    # Wait for 3 to finish
    booking_worker.join()
    search_worker.join()
    generic_worker.join()


if __name__ == "__main__":
    cfg = AppConfig()
    # Set up logging
    logging.basicConfig(
        level=cfg.log_level,
        handlers=[
            get_console_handler(),
        ],
    )
    main(cfg)
