from __future__ import absolute_import, division, print_function, unicode_literals

import io
from datetime import datetime, timedelta, tzinfo

import pendulum
from dateutil.relativedelta import relativedelta
from pytest import raises
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.pool import NullPool

from common import db  # flake8: noqa
from sqlbag import DB_ERROR_TUPLE, S, copy_url, raw_connection
from sqlbag.pg import (
    errorcode_from_error,
    pg_errorname_lookup,
    pg_notices,
    pg_print_notices,
    use_pendulum_for_time_types,
)
from sqlbag.pg.datetimes import (
    UTC,
    ZERO,
    combine_date_and_time,
    localnow,
    naive,
    parse_interval_values,
    parse_time_of_day,
    sqlbagrelativedelta,
    utcnow,
    vanilla,
)

USERNAME = "testonly_sqlbag_user"
PW = "duck"


ZERO = timedelta(0)
HOUR = timedelta(hours=1)


def test_errors_and_messages(db):
    assert pg_errorname_lookup(22005) == "ERROR_IN_ASSIGNMENT"

    with S(db) as s:
        s.execute("drop table if exists x")
        assert pg_notices(s) == ['NOTICE:  table "x" does not exist, skipping\n']
        assert pg_notices(s, wipe=True) == [
            'NOTICE:  table "x" does not exist, skipping\n'
        ]
        assert pg_notices(s) == []

        out = io.StringIO()
        s.execute("drop table if exists x")
        pg_print_notices(s, out=out)

        assert out.getvalue() == 'NOTICE:  table "x" does not exist, skipping'

        out = io.StringIO()
        pg_print_notices(s, out=out)

        assert out.getvalue() == ""

        s.execute("create table x(id text)")

    try:
        with S(db) as s:
            s.execute("create table x(id text)")
    except DB_ERROR_TUPLE as e:
        assert errorcode_from_error(e) == "42P07"


def test_parse_interval():
    TEST_CASES = [
        "1 years 2 mons",
        "3 days 04:05:06",
        "-1 year -2 mons +3 days -04:05:06.2",
    ]

    ANSWERS = [
        dict(years=1, months=2),
        dict(days=3, hours=4, minutes=5, seconds=6, microseconds=0),
        dict(
            years=-1,
            months=-2,
            days=3,
            hours=-4,
            minutes=5,
            seconds=6,
            microseconds=200000,
        ),
    ]

    for case, answer in zip(TEST_CASES, ANSWERS):
        assert parse_interval_values(case) == answer


def test_datetime_primitives():
    dt = datetime.now()

    utc = UTC()
    assert utc.utcoffset(dt) == ZERO
    assert utc.utcoffset(None) == ZERO

    assert utc.tzname(dt) == "UTC"

    assert utc.dst(dt) == ZERO
    assert utc.dst(None) == ZERO

    p = pendulum.instance(dt)
    n = naive(p)
    assert n == dt
    assert type(n) == type(p)  # use pendulum naive type

    p2 = utcnow()

    assert p2.tz == p2.in_timezone("UTC").tz

    p3 = localnow()

    v = vanilla(p3)
    assert pendulum.instance(v) == p3

    tod = parse_time_of_day("2015-01-01 12:34:56")
    assert str(tod) == "12:34:56"

    d = pendulum.Date(2017, 1, 1)
    dt = combine_date_and_time(d, tod)
    assert str(dt) == "2017-01-01T12:34:56+00:00"

    sbrd = sqlbagrelativedelta(days=5, weeks=6, months=7)
    assert str(sbrd) == "7 months 47 days"


def test_pendulum_for_time_types(db):
    t = pendulum.parse("2017-12-31 23:34:45", tz="Australia/Melbourne")
    i = relativedelta(days=1, seconds=200, microseconds=99)

    with S(db) as s:
        c = raw_connection(s)
        cu = c.cursor()

        cu.execute(
            """
            select
                null::timestamp,
                null::timestamptz,
                null::date,
                null::time,
                null::interval
        """
        )

        descriptions = cu.description
        oids = [x[1] for x in descriptions]

        use_pendulum_for_time_types()

        s.execute(
            """
            create temporary table dt(
                ts timestamp,
                tstz timestamptz,
                d date,
                t time,
                i interval)
        """
        )

        s.execute(
            """
            insert into dt(ts, tstz, d, t, i)
            values
            (:ts,
            :tstz,
            :d,
            :t,
            :i)
        """,
            {
                "ts": vanilla(t),
                "tstz": t.in_timezone("Australia/Sydney"),
                "d": t.date(),
                "t": t.time(),
                "i": i,
            },
        )

        out = list(s.execute("""select * from dt"""))[0]

        assert out.ts == naive(t.in_tz("UTC"))
        assert out.tstz == t.in_timezone("UTC")
        assert out.d == t.date()
        assert out.t == t.time()
        assert out.i == i

        result = s.execute(
            """
            select
                null::timestamp,
                null::timestamptz,
                null::date,
                null::time,
                null::interval
        """
        )

        out = list(result)[0]
        assert list(out) == [None, None, None, None, None]
