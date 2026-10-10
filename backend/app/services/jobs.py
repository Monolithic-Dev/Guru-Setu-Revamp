"""Background work hooks. JOB-01 (certificate processing) is scheduled per upload by `services/certificates.py`;
JOB-02 (stale-processing sweep) runs here, at API startup."""
import logging

from app.services import certificates

log = logging.getLogger("gurusetu.jobs")


def startup() -> None:
    """Called once by `main.py` after the schema is applied. A failed sweep must not stop the API from starting."""
    try:
        swept = certificates.sweep_stale()
        if swept:
            log.warning("swept %d stale processing certificate(s) to failed", swept)
    except Exception:
        log.exception("stale-processing sweep failed")
