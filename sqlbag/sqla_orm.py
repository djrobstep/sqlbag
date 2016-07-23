from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import re

from collections import OrderedDict

from sqlalchemy import inspect

import sqlalchemy.exc
import sqlalchemy.orm
import sqlalchemy.engine.url

import sqlalchemy.orm.session

from sqlalchemy.ext.declarative import declared_attr

from sqlalchemy.schema import MetaData
import six


def metadata_from_session(s):
    """
    Args:
        s: an SQLAlchemy :class:`Session`
    Returns:
        The metadata.

    Get the metadata associated with the schema.
    """
    meta = MetaData()
    meta.reflect(bind=s.bind)
    return meta


@six.python_2_unicode_compatible
class Base(object):
    """
    A modified ORM Base implementation that gives you a nicer __repr__ (useful when printing/logging/debugging), along with some additional properties.
    """

    @declared_attr
    def __tablename__(cls):
        """Convert CamelCase class name to underscores_between_words
        table name."""
        name = cls.__name__
        return (name[0].lower() + re.sub(
            r'([A-Z])', lambda m: "_" + m.group(0).lower(), name[1:]))

    def __repr__(self):
        items = row2dict(self).items()
        return "{0}({1})".format(
            self.__class__.__name__,
            ', '.join(['{0}={1!r}'.format(*_) for _ in items]))

    @property
    def _sqlachanges(self):
        """
        Return the changes you've made to this object so far this session.
        """
        return sqlachanges(self)

    @property
    def _ordereddict(self):
        """
        Return this object's properties as an OrderedDict.
        """
        return row2dict(self)

    def __str__(self):
        return repr(self)


def sqlachanges(sa_object):
    """
    Returns the changes made to this object so far this session, in {'propertyname': [listofvalues] } format.
    """
    attrs = inspect(sa_object).attrs
    return {
        a.key: list(reversed(a.history.sum()))
        for a in attrs if len(a.history.sum()) > 1
    }


def row2dict(sa_object):
    """
    Converts a mapped object into an OrderedDict.
    """
    return OrderedDict((pname, getattr(sa_object, pname))
                       for pname in get_properties(sa_object))


def get_properties(instance):
    """
    Gets the mapped properties of this mapped object.
    """

    def _props():
        mapper = sqlalchemy.orm.object_mapper(instance)
        for prop in mapper.iterate_properties:
            yield prop.key

    return list(_props())
