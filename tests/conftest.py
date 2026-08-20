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

CB_TEST_TRACE=2 additionally logs one line per boto invocation. Level 1
answers whether time is going into polling or into throttled retries; when
the answer is neither - as it was for test_create_and_list_image, where 1184
of 1400 seconds passed in a single stretch with no polls and no retries at
all - level 2 is what names the call that blocked, since the gap between two
consecutive request lines is that request.

Deliberately opt-in: at a 1s poll interval a 30 minute wait is ~1800 lines
for a single waiting resource, and level 2 is roughly 20x that again.
"""
import logging
import os

TRACE_FILE_PREFIX = 'cb-trace-'


def _trace_level():
    """
    0 off; 1 waits and retries; 2 also every provider request.

    Level 1 answers "is the time going into polling, or into throttled
    retries" - it is cheap enough to leave on. Level 2 additionally logs each
    boto invocation, so the gap between two consecutive lines names the call
    that blocked; that is what level 1 cannot show, at perhaps 20x the volume.
    """
    raw = (os.environ.get('CB_TEST_TRACE') or '').lower()
    if raw in ('2', 'requests', 'all'):
        return 2
    return 1 if raw in ('1', 'true', 'yes') else 0


def _trace_path():
    # Each xdist worker needs its own file; they run in one directory and
    # would otherwise interleave mid-line.
    worker = os.environ.get('PYTEST_XDIST_WORKER', 'main')
    return '{0}{1}.log'.format(TRACE_FILE_PREFIX, worker)


class _TraceFilter(logging.Filter):
    """
    Keep the test markers, the poll lines and genuine retries; at level 2
    keep the provider request lines too, and drop everything else.

    cloudbridge at DEBUG is far too chatty to keep wholesale - roughly 20x
    the volume - and most of it says nothing about where the time went.
    """

    def __init__(self, level):
        super(_TraceFilter, self).__init__()
        self.level = level

    def filter(self, record):
        message = record.getMessage()
        if record.name.startswith('botocore'):
            # botocore logs a line per request whether or not it retried;
            # only an actual backoff says anything about throttling. The two
            # retry implementations word the negative case differently.
            return not (message.startswith('Not retrying')
                        or message.startswith('No retry needed'))
        if record.name.startswith('cloudbridge.providers'):
            return self.level >= 2
        return message.startswith('=== ') or 'Waiting another' in message


def pytest_configure(config):
    level = _trace_level()
    if not level:
        return

    handler = logging.FileHandler(_trace_path(), mode='w')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(name)s %(message)s'))
    handler.addFilter(_TraceFilter(level))

    # wait_for logs one line per poll at DEBUG, naming the object and the
    # state it is waiting on. Scope the level to that module rather than the
    # cloudbridge tree: raising the whole tree to DEBUG would have every
    # provider request build a log record that the filter then discards, and
    # those records still propagate to pytest's own capture handler, which
    # holds them for the duration of the test.
    loggers = ['cloudbridge.base.resources',
               # Quiet unless a request is actually retried, which is how
               # throttling shows up client-side. Enabling botocore wholesale
               # would log every request and response.
               'botocore.retries', 'botocore.retryhandler']
    if level >= 2:
        # One line per boto invocation, so a stretch with no wait_for polling
        # can still be attributed to the call that blocked.
        loggers.append('cloudbridge.providers')

    for name in loggers:
        target = logging.getLogger(name)
        target.addHandler(handler)
        target.setLevel(logging.DEBUG)


def pytest_runtest_logstart(nodeid, location):
    # Stamps the trace with test boundaries, so a span of polls can be
    # attributed to the test that caused it.
    if _trace_level():
        logging.getLogger('cloudbridge.base.resources').debug(
            '=== START %s', nodeid)


def pytest_runtest_logfinish(nodeid, location):
    if _trace_level():
        logging.getLogger('cloudbridge.base.resources').debug(
            '=== END %s', nodeid)
