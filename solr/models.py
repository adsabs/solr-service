# -*- coding: utf-8 -*-
"""
    solr.models
    ~~~~~~~~~~~~~~~~~~~~~

    Models for the users (users) of AdsWS
"""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Limits(Base):
    __tablename__ = 'limits'
    id = Column(Integer, primary_key=True)
    uid = Column(String(255))
    field = Column(String(255))
    filter = Column(Text)

    def toJSON(self):
        """Returns value formatted as python dict."""
        return {
            'uid': self.uid,
            'field': self.field,
            'filter': self.filter or None
        }
