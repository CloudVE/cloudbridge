"""
Opt-in tracing for the cloud integration suites.

The AWS suite's wall time is dominated by one or two tests, and end-to-end
timings have proved too noisy to attribute - test_create_and_list_image alone
has measured 26.2, 60.6 and 33.8 minutes across three runs of the same 123
tests. Answering *where* that time goes needs the individual waits timed
rather than the test as a whole.

Set CB_TEST_TRACE=1 to capture, per xdist worker:

* every ``wait_for`` poll, which brackets each wait - the span from a wait's
  first poll to its last is the wait itself, and the gap between consecutive
  polls shows whether the state call is slow (the interval is 1s for real
  providers, so a larger gap is the API, not the sleep);
* botocore retries, which is how throttling appears client-side. Those
  loggers stay silent unless a request is actually retried, so anything they
  emit is signal.

Records go to cb-trace-<worker>.log rather than stderr because pytest
captures stderr at file-descriptor level, and captured output is discarded
for passing tests - which these are. tox prints the files once the run
finishes.

Deliberately opt-in: at a 1s poll interval a 30 minute wait is ~1800 lines
for a single waiting resource.
"""
import logging
import os

TRACE_FILE_PREFIX = 'cb-trace-'


def _tracing_requested():
    return (os.environ.get('CB_TEST_TRACE') or '').lower() in (
        '1', 'true', 'yes')


def _trace_path():
    # Each xdist worker needs its own file; they run in one directory and
    # would otherwise interleave mid-line.
    worker = os.environ.get('PYTEST_XDIST_WORKER', 'main')
    return '{0}{1}.log'.format(TRACE_FILE_PREFIX, worker)


class _WaitAndRetryOnly(logging.Filter):
    """
    Keep the poll lines, the test markers and the retries; drop the rest.

    cloudbridge at DEBUG is far too chatty to keep wholesale - most of the
    volume is per-request logging from the provider helpers, which says
    nothing about where a wait went.
    """

    def filter(self, record):
        message = record.getMessage()
        if record.name.startswith('botocore'):
            # botocore logs a line per request either way; only the ones
            # where it actually backed off say anything about throttling.
            return not message.startswith('Not retrying')
        return message.startswith('=== ') or 'Waiting another' in message


def pytest_configure(config):
    if not _tracing_requested():
        return

    handler = logging.FileHandler(_trace_path(), mode='w')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(name)s %(message)s'))
    handler.addFilter(_WaitAndRetryOnly())

    # wait_for logs one line per poll at DEBUG, naming the object and the
    # state it is waiting on. Scope the level to that module rather than the
    # cloudbridge tree: raising the whole tree to DEBUG would have every
    # provider request build a log record that the filter then discards, and
    # those records still propagate to pytest's own capture handler, which
    # holds them for the duration of the test.
    waits = logging.getLogger('cloudbridge.base.resources')
    waits.addHandler(handler)
    waits.setLevel(logging.DEBUG)

    # Quiet unless a request is actually retried, which is how throttling
    # shows up client-side. Enabling botocore wholesale would log every
    # request and response.
    for name in ('botocore.retries', 'botocore.retryhandler'):
        target = logging.getLogger(name)
        target.addHandler(handler)
        target.setLevel(logging.DEBUG)


def pytest_runtest_logstart(nodeid, location):
    # Stamps the trace with test boundaries, so a span of polls can be
    # attributed to the test that caused it.
    if _tracing_requested():
        logging.getLogger('cloudbridge.base.resources').debug(
            '=== START %s', nodeid)


def pytest_runtest_logfinish(nodeid, location):
    if _tracing_requested():
        logging.getLogger('cloudbridge.base.resources').debug(
            '=== END %s', nodeid)
