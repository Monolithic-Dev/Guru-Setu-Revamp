"""Background work hooks. JOB-01 (certificate processing) is filled in with the certificates API in Phase 2;
JOB-02 (stale-processing sweep) runs at API startup."""


def startup() -> None:
    """Called once by `main.py`. JOB-02 is added in T2.P2.1; nothing to sweep before the certificates exist."""
