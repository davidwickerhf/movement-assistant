from datetime import datetime
from fff_automation import db


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.String(8), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    platform = db.Column(db.String(20), nullable=False)
    color = db.Column(db.Integer, nullable=False)
    restriction = db.Column(db.String(20), nullable=False)
    is_subgroup = db.Column(db.Boolean, nullable=False)
    parent_group = db.Column(db.Integer, unique=True, nullable=False)
    purpose = db.Column(db.String(300), nullable=True)
    onboarding = db.Column(db.String(300), nullable=True)
    date_activated = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)
    calls = db.relationship('Call', backref='group', lazy=True)

    def __repr__(self):
        return f"Group('{self.title}', '{self.category}', '{self.region}', '{self.platform}', '{self.restriction}', '{self.is_subgroup}')"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    groups = db.relationship('Group', backref='activator', lazy=True)


class Call(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    card_id = db.Column(db.String(8), unique=True, nullable=False)
    title = db.Column(db.String(30), nullable=False)
