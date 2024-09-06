from datetime import datetime

from flask import session

from .extns import db


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def save_to_database(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_database(self):
        db.session.delete(self)
        db.session.commit()

    def add_to_session(self):
        session['user_id'] = self.id

    def __repr__(self):
        return f"<user: {self.id}>"


class Tailor(db.Model):
    __tablename__ = "tailor"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone_no = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(255), nullable=True)
    clothing_type = db.Column(db.Text, nullable=True)
    price = db.Column(db.Text, nullable=True)

    def save_to_database(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_database(self):
        db.session.delete(self)
        db.session.commit()

    def add_to_session(self):
        session['tailor_id'] = self.id

    def __repr__(self):
        return f"<tailor: {self.id}>"


class Courier(db.Model):
    __tablename__ = "courier"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def save_to_database(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_database(self):
        db.session.delete(self)
        db.session.commit()

    def add_to_session(self):
        session['courier_id'] = self.id

    def __repr__(self):
        return f"<courier: {self.id}>"


class Order(db.Model):
    __tablename__ = "order"
    id = db.Column(db.Integer, primary_key=True)
    cus_name = db.Column(db.String(255), nullable=False)
    cus_phone_no = db.Column(db.String(255), nullable=False)
    cus_address = db.Column(db.Text, nullable=False)
    tail_id = db.Column(db.Integer, nullable=False)
    tail_address = db.Column(db.Text, nullable=False)
    tail_phoneNo = db.Column(db.Text, nullable=False)
    s_specification = db.Column(db.Text, nullable=False)
    s_speci_image = db.Column(db.BLOB, nullable=True)
    sent_clo_image = db.Column(db.BLOB, nullable=False)
    cus_id = db.Column(db.Integer, nullable=False)
    tracking_id = db.Column(db.String(4), nullable=False)
    clo_rec_from_cus = db.Column(db.Boolean, default=False)
    clo_del_to_tail = db.Column(db.Boolean, default=False)
    sti_in_pro = db.Column(db.Boolean, default=False)
    sti_done = db.Column(db.Boolean, default=False)
    payment = db.Column(db.Numeric(10, 2))
    clo_del_to_cor = db.Column(db.Boolean, default=False)
    clo_del_to_cus = db.Column(db.Boolean, default=False)

    def save_to_database(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_database(self):
        db.session.delete(self)
        db.session.commit()

    def add_to_session(self):
        session['order_id'] = self.id

    def __repr__(self):
        return f"<order: {self.id}>"


class Measurements(db.Model):
    __tablename__ = "measurements"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    shoulder = db.Column(db.Float, nullable=True)
    sleeves = db.Column(db.Float, nullable=True)
    armhole = db.Column(db.Float, nullable=True)
    hip_to_ankle = db.Column(db.Float, nullable=True)
    back_l = db.Column(db.Float, nullable=True)
    waist = db.Column(db.Float, nullable=True)
    chest = db.Column(db.Float, nullable=True)
    knees = db.Column(db.Float, nullable=True)
    front_l = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def save_to_database(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_database(self):
        db.session.delete(self)
        db.session.commit()

    def add_to_session(self):
        session['measurements_id'] = self.id

    def __repr__(self):
        return f"<measurements: {self.id}>"


class Payment(db.Model):
    __tablename__ = "payment"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    track_id = db.Column(db.String(255), nullable=False)
    tailor_id = db.Column(db.Integer, nullable=False)
    amount_usd = db.Column(db.Float, nullable=True)
    amount_pkr = db.Column(db.Float, nullable=True)
    payment_link = db.Column(db.String(500), nullable=False)
    stripe_payment_intent = db.Column(db.String(255), nullable=True)
    currency = db.Column(db.String(10), nullable=False, default='pkr')
    status = db.Column(db.String(255), nullable=False, default='pending')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def save_to_database(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_database(self):
        db.session.delete(self)
        db.session.commit()

    def add_to_session(self):
        session['payment_id'] = self.id

    def __repr__(self):
        return f"<payment: {self.id}>"