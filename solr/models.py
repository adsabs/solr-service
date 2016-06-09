# -*- coding: utf-8 -*-
"""
    solr.models
    ~~~~~~~~~~~~~~~~~~~~~

    Models for the users (users) of AdsWS
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy() # must be run in the context of a flask application

class Limits(db.Model):
    __bind_key__ = 'solr_service'
    __tablename__ = 'limits'
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255))
    field = db.Column(db.String(255))
    filter = db.Column(db.Text)
    
    def toJSON(self):
        """Returns value formatted as python dict."""
        return {
            'uid': self.uid,
            'field': self.field,
            'filter': self.filter or None
        }