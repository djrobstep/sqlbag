from datetime import datetime, timedelta, tzinfo

import pendulum
from dateutil.relativedelta import relativedelta
from psycopg2.extensions import AsIs, new_type, register_adapter, register_type

ZERO = timedelta(0)
HOUR = timedelta(hours=1)

PENDULUM_DATETIME_TYPE = type(pendulum.now("UTC"))


# A UTC class.
class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


utc = UTC()


def vanilla(pendulum_dt):
    x = pendulum_dt.in_timezone("UTC")

    return datetime(
        x.year, x.month, x.day, x.hour, x.minute, x.second, x.microsecond, tzinfo=utc
    )


def naive(pendulum_dt):
    x = pendulum_dt
    return x.naive()


def utcnow():
    return pendulum.now("UTC")


def localnow():
    return pendulum.now()


def parse_time_of_day(x):
    return pendulum.parse(x).time()


def combine_date_and_time(date, time, timezone="UTC"):
    naive = datetime.combine(date, time)
    return pendulum.instance(naive, tz=timezone)


OID_TIMESTAMP = 1114
OID_TIMESTAMPTZ = 1184
OID_DATE = 1082
OID_TIME = 1083
OID_INTERVAL = 1186


def tokens_iter(s):
    tokens = s.split()

    while tokens:
        if ":" in tokens[0]:
            x, tokens = tokens[0], tokens[1:]
            t = pendulum.parse(x, strict=False).time()

            yield {
                "hours": x.startswith("-") and -t.hour or t.hour,
                "minutes": t.minute,
                "seconds": t.second,
                "microseconds": t.microsecond,
            }
        else:
            x, tokens = tokens[:2], tokens[2:]
            x[1] = x[1].replace("mons", "months")
            yield {x[1]: int(x[0])}


def parse_interval_values(s):
    values = {}
    [values.update(_) for _ in tokens_iter(s)]

    for k in list(values):
        if not k.endswith("s"):
            values[k + "s"] = values.pop(k)
    return values


def format_relativedelta(rd):
    RELATIVEDELTA_FIELDS = [
        "years",
        "months",
        "days",
        "hours",
        "minutes",
        "seconds",
        "microseconds",
    ]

    fields = [(k, getattr(rd, k)) for k in RELATIVEDELTA_FIELDS if getattr(rd, k)]

    s = " ".join("{} {}".format(v, k) for k, v in fields)

    return s


class sqlbagrelativedelta(relativedelta):
    def __str__(self):
        return format_relativedelta(self)


def cast_timestamp(value, cur):
    if value is None:
        return None
    return pendulum.parse(value).naive()


def cast_timestamptz(value, cur):
    if value is None:
        return None
    return pendulum.parse(value).in_timezone("UTC")


def cast_time(value, cur):
    if value is None:
        return None
    return pendulum.parse(value).time()


def cast_date(value, cur):
    if value is None:
        return None
    return pendulum.parse(value).date()


def cast_interval(value, cur):
    if value is None:
        return None
    values = parse_interval_values(value)
    return sqlbagrelativedelta(**values)


def adapt_datetime(dt):
    if not isinstance(dt, PENDULUM_DATETIME_TYPE):
        dt = pendulum.instance(dt)
    in_utc = dt.in_timezone("UTC")
    return AsIs("'{}'".format(in_utc))


def adapt_relativedelta(rd):
    return AsIs("'{}'".format(format_relativedelta(rd)))


def register_cast(oid, typename, method):
    new_t = new_type((oid,), typename, method)
    register_type(new_t)


def use_pendulum_for_time_types():
    register_cast(OID_TIMESTAMP, "TIMESTAMP", cast_timestamp)
    register_cast(OID_TIMESTAMPTZ, "TIMESTAMPTZ", cast_timestamptz)
    register_cast(OID_DATE, "DATE", cast_date)
    register_cast(OID_TIME, "TIME", cast_time)
    register_cast(OID_INTERVAL, "INTERVAL", cast_interval)

    register_adapter(datetime, adapt_datetime)
    register_adapter(relativedelta, adapt_relativedelta)


utc = UTC()
