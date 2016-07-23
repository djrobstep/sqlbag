PSQL_KILLQUERY_FORMAT = """
    select
        pg_terminate_backend(psa.pid)
    from
        pg_stat_activity psa
    where
        psa.pid != pg_backend_pid()
"""

PSQL_KILLQUERY_FORMAT_HARD = """
    select
        pg_terminate_backend(psa.pid)
    from
        pg_stat_activity psa
    where datname = :databasename
"""

# this is needed because pg_stat_activity doesn't
# show activity of dropped users properly
STAT_ACTIVITY_INCLUDING_DROPPED_USERS = """
    with psa as (
        SELECT
            *,
            (select datname from pg_database d where d.oid = s.datid)
                as datname
        FROM pg_stat_get_activity(NULL::integer) s

    )
    select * from psa;
"""

PSQL_KILLQUERY_FORMAT_INCLUDING_DROPPED = """
    with psa as (
        SELECT
            *,
            (select datname from pg_database d where d.oid = s.datid)
                as datname
        FROM pg_stat_get_activity(NULL::integer) s
    )
    select
        pg_terminate_backend(psa.pid)
    from
        psa
    where psa.pid != pg_backend_pid()
"""
