from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from . import db
from .utils import login_required
from .model import Order, Tailor

courier = Blueprint("courier", __name__)


@courier.route("/courier/NewOrders", methods=['GET', 'POST'])
@login_required(role="Courier")
def home():
    # Query all orders from the Order model
    orders = Order.query.all()

    # Create a dictionary to store orders along with tailor data
    orders_with_tailors = []

    # Loop through each order
    for order in orders:
        # Query the Tailor table to find the tailor associated with the tail_id
        tailor = Tailor.query.filter_by(id=order.tail_id).first()

        # If tailor exists, add order and tailor data to the dictionary
        if tailor:
            orders_with_tailors.append({
                'order': order,
                'tailor': tailor
            })
    return render_template("courier_new_order.html",
                           tittle="Orders",
                           orders_with_tailors=orders_with_tailors)


@courier.route("/courier/updateOrderProgress", methods=['GET', 'POST'])
def u_progress():
    order_id = None
    if request.method == 'POST':
        order_id = request.form.get('order-id')

        if order_id:
            # Check if the order ID exists
            order = Order.query.filter_by(id=order_id).first()
            if order:
                # If order exists, update the order status based on form data
                order.clo_rec_from_cus = request.form.get('clo_rec_from_cus') == 'on'
                order.clo_del_to_tail = request.form.get('clo_del_to_tail') == 'on'
                order.clo_del_to_cus = request.form.get('clo_del_to_cus') == 'on'

                # Check if any checkbox is checked
                if order.clo_rec_from_cus or order.clo_del_to_tail or order.clo_del_to_cus:
                    # Commit changes to the database
                    db.session.commit()

                    flash("Order status updated successfully !")
            else:
                # If order doesn't exist, show error message
                flash("Order ID not found, please enter a valid ID.")
        else:
            flash("Order ID is required to update the order progress.")

    # Pass the order_id to the template regardless of whether it exists or not
    return render_template("courier_update_progress.html",
                           title="Update Orders Progress",
                           order_id=order_id)
