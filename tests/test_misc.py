from __future__ import unicode_literals

from sqlbag import quoted_identifier


def test_misc():
    assert quoted_identifier('hi') == '"hi"'
    assert quoted_identifier('he"llo') == '"he""llo"'
