from __future__ import absolute_import, division, print_function, unicode_literals

from collections import OrderedDict

import six
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from sqlbag import Base as SqlxBase
from sqlbag import S, metadata_from_session, temporary_database

Base = declarative_base(cls=SqlxBase)


class Something(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String)


def test_orm_stuff():
    with temporary_database() as url:
        with S(url) as s:
            Base.metadata.create_all(s.bind.engine)

        with S(url) as s:
            x = Something(name="kanye")
            s.add(x)
            s.commit()
            things = s.query(Something).all()
            x1 = things[0]

            prefix = "u" if six.PY2 else ""
            repr_str = "Something(id=1, name={}'kanye')".format(prefix)
            assert repr(x1) == str(x1) == repr_str

            assert metadata_from_session(s).schema == Base.metadata.schema
            assert x1._sqlachanges == {}
            assert x1._ordereddict == OrderedDict([("id", 1), ("name", "kanye")])
            x1.name = "kanye west"
            assert x1._sqlachanges == {"name": ["kanye", "kanye west"]}
            s.commit()
            assert x1._sqlachanges == {}
