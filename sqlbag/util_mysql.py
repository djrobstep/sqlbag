MYSQL_KILLQUERY_FORMAT = """
    select
        *,
        ID as process_id,
        connection_id() as cid
    from
        information_schema.processlist
    where
        ID != connection_id()
"""
