from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, abort
import io, re
from . import db
from .utils import login_required
from .model import Tailor, Order, Payment, Measurements

tailor = Blueprint("tailor", __name__)


@tailor.route("/tailor/profile", methods=['GET', 'POST'])
@login_required(role="Tailor")
def home():
    # tailor_id = session.get('tailor_id')
    tailor_id = 5
    tailor = Tailor.query.filter_by(id=tailor_id).first()

    if request.method == 'POST':
        current_password = request.form.get('current-pass')
        new_password = request.form.get('new-pass')

        # Regular expression to validate password
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$'

        if current_password and new_password:
            if current_password != tailor.password:
                flash('Current password is incorrect.')
            elif not re.match(password_regex, new_password):
                flash("Please set strong password.")
            else:
                tailor.password = new_password
                db.session.commit()
                flash('Password changed successfully!!')

        # Update other fields
        phone_no = request.form.get('phone_no')
        city = request.form.get('city')
        address = request.form.get('address')
        clothing_type = request.form.get('clothing_type')
        price = request.form.get('price')

        if phone_no and city and address and clothing_type and price:
            tailor.phone_no = phone_no
            tailor.city = city
            tailor.address = address
            tailor.clothing_type = clothing_type
            tailor.price = price
            db.session.commit()
            flash('Profile updated successfully!!')
        else:
            flash('All fields are required.')

        return redirect(url_for('tailor.home'))

    return render_template("tailor_profile.html",
                           tittle="Profile",
                           tailor=tailor)


@tailor.route('/image/<int:order_id>/<string:image_type>')
def get_image(order_id, image_type):
    # Validate order_id
    if order_id <= 0:
        abort(404)

    order = Order.query.get_or_404(order_id)

    # Validate image_type
    if image_type not in ['s_speci_image', 'sent_clo_image']:
        abort(404)

    # Retrieve the image data based on image_type
    if image_type == 's_speci_image':
        image_data = order.s_speci_image
    else:
        image_data = order.sent_clo_image

    # Check if image_data is not None or empty
    if not image_data:
        abort(404)

    # Determine the MIME type based on the image data
    mime_type = 'image/jpeg'  # Default MIME type
    if image_data.startswith(b'\xff\xd8'):
        mime_type = 'image/jpeg'
    elif image_data.startswith(b'\x89PNG\r\n\x1a\n'):
        mime_type = 'image/png'
    elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):
        mime_type = 'image/gif'

    # Serve the image
    return send_file(io.BytesIO(image_data), mimetype=mime_type)


@tailor.route("/tailor/NewOrders",  methods=['GET', 'POST'])
def n_order():
    # tailor_id = session.get('tailor_id')
    tailor_id = 5

    # Fetch orders for the current tailor_id from the database
    orders = Order.query.filter_by(tail_id=tailor_id).all()

    # Create a list to hold orders with their corresponding measurements
    orders_with_measurements = []

    for order in orders:
        # Fetch the latest measurements for the current order's cus_id from the Measurements table
        latest_measurements = Measurements.query.filter_by(user_id=order.cus_id).order_by(
            Measurements.timestamp.desc()).first()

        # Add the latest measurements data to the order object
        order_data = {
            'order': order,
            'measurements': latest_measurements
        }

        # Add the order with measurements to the list
        orders_with_measurements.append(order_data)

    return render_template("tailor_new_order.html",
                           tittle="Orders",
                           orders=orders_with_measurements)


@tailor.route("/tailor/updateOrderProgress",  methods=['GET', 'POST'])
def progress():
    order_id = request.form.get('order-id')

    if order_id:
        # Check if the order ID exists
        order = Order.query.filter_by(id=order_id).first()
        if order:
            # If order exists, update the order status based on form data
            order.sti_in_pro = request.form.get('sti_pro') == 'on'
            order.sti_done = request.form.get('sti_done') == 'on'
            order.payment = request.form.get('payment')
            order.clo_del_to_cor = request.form.get('clo_del_to_cor') == 'on'

            # Check if any checkbox is checked
            if order.sti_in_pro or order.sti_done or order.payment or order.clo_del_to_cor:
                # Commit changes to the database
                db.session.commit()

                flash("Order status updated successfully !")
        else:
            # If order doesn't exist, show error message
            flash("Order ID not Found, Please Enter valid ID.")

    # Pass the order_id to the template regardless of whether it exists or not
    return render_template("tailor_update_progress.html",
                           tittle="Update Progress",
                           order_id=order_id)


@tailor.route("/tailor/payment_status",  methods=['GET', 'POST'])
def payment_status():
    # tailor_id = session.get('tailor_id')
    tailor_id = 5

    orders = Order.query.filter_by(tail_id=tailor_id).all()
    payments = Payment.query.filter_by(tailor_id=tailor_id).all()

    if not payments:
        message = "No payment initiated for any order"
    else:
        message = None

    return render_template("tailor_payment.html",
                           tittle="Tailor Payment Status",
                           orders=orders,
                           payments=payments,
                           message=message)


