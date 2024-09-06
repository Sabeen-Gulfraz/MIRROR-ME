from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash, send_file
import random, string, requests, logging
import cv2
import torch
import mediapipe as mp
import numpy as np
import time, re
import tempfile
import stripe
from scipy.stats import skew

from . import db
from .utils import login_required
from .model import Tailor, User, Order, Measurements, Payment

user = Blueprint("user", __name__)
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stripe.api_key = 'sk_test_51PPMtfJNX7WUNuNsVXzTBGAsoPml13dqiYkXJr3csGuLNNENs5beu4e8BP0pFUv7trhXSkOGUluEN4c6CGGJdWXF00ekwCKGAm'
exchange_rate_api_key = 'bf2a9b4916877d9716a315ee'
endpoint_secret = 'whsec_GKuZ5hRt9kM6IgXjBkMLJixnGNn1ZYnM'


@user.route("/user/profile", methods=['GET', 'POST'])
@login_required(role="Customer")
def home():
    # user_id = session.get('user_id')
    user_id = 4

    user = User.query.filter_by(id=user_id).first()

    if request.method == 'POST':
        current_password = request.form.get('current-pass')
        new_password = request.form.get('new-pass')
        print(current_password)
        print(new_password)

        # Regular expression to validate password
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$'

        if current_password != user.password:
            flash('Current password is incorrect.')
        elif not re.match(password_regex, new_password):
            flash("Please set strong password.")
        else:
            user.password = new_password
            db.session.commit()
            flash('Password changed successfully!!')

            return redirect(url_for('user.home'))

    return render_template("user_profile.html"
                           ,tittle="Profile"
                           , user=user)


@user.route("/user/search", methods=['GET', 'POST'])
def search():
    data = request.args.get("search", None, type=str)
    # search query
    tailors = Tailor.query.filter(Tailor.city.like(f'%{data}%')).all()

    if not tailors:
        flash(f"Sorry 😞, No result found.....")
    return render_template("user_search.html"
                           ,tittle=f"{data.capitalize()} Tailors"
                           ,tailors=tailors)


def generate_tracking_id():
    # Generate a 4-digit tracking ID
    return ''.join(random.choices(string.digits, k=4))


@user.route("/user/placeOrder", methods=['GET', 'POST'])
def for_payment():
    return render_template("user_place_order.html"
                           , tittle="Payment")


@user.route("/user/placeOrder/<tailor_id>", methods=['GET', 'POST'])
def order(tailor_id):
    if request.method == 'POST':
        # Access user ID from the session
        # cus_id = session.get('user_id')
        cus_id = 4

        # Check if the user has saved body measurements
        user_measurement = Measurements.query.filter_by(user_id=cus_id).first()
        if not user_measurement:
            flash('You have to save your body measurements first.')
            return redirect(request.url)  # Redirect back to the order page

        # Retrieve form data
        cus_name = request.form['u-name']
        cus_phone_no = request.form['u-phone_no']
        cus_address = request.form['u-address']
        # Fetch the tailor's details from the database using the tailor_id
        tailor = Tailor.query.filter_by(id=tailor_id).first()
        tail_id = tailor_id
        tail_address = tailor.address
        tail_phoneNo = tailor.phone_no
        s_specification = request.form['s-specification']

        # Read the contents of the uploaded files
        s_speci_image = request.files['specification_image'].read()
        sent_clo_image = request.files['sent_clothes_image'].read()

        if not all([cus_name, cus_phone_no, cus_address, tail_id, tail_address, tail_phoneNo, s_specification, sent_clo_image,
                    cus_id]):
            flash('Please fill out all fields.')
        else:
            try:
                # Generate a unique order tracking ID
                order_tracking_id = generate_tracking_id()
                # Create a new Order object with the form data and file contents
                new_order = Order(cus_name=cus_name, cus_phone_no=cus_phone_no, cus_address=cus_address,
                                  tail_id=tail_id, tail_address=tail_address, tail_phoneNo=tail_phoneNo, s_specification=s_specification,
                                  s_speci_image=s_speci_image, sent_clo_image=sent_clo_image,
                                  cus_id=cus_id, tracking_id=order_tracking_id)

                # Save the new order to the database
                new_order.save_to_database()
                flash('Your order has been placed successfully!')
            except Exception as e:
                flash(f'An error occurred while submitting your order: {str(e)}')

    return render_template("user_place_order.html"
                           , tittle="Place Order"
                           , tailor_id=tailor_id)


@user.route("/user/orderHistory" , methods=['GET' , 'POST'])
def order_history():
    # Get the user_id from the session
    # user_id = session.get('user_id')
    user_id = 4

    if user_id:
        # Query the database to get all orders for the logged-in user
        user_orders = Order.query.filter_by(cus_id=user_id).all()
        return render_template("user_order_history.html", tittle="Orders History", orders=user_orders)

    return render_template("user_order_history.html"
                           , tittle="Orders History")


@user.route("/user/measurements", methods=['GET', 'POST'])
def measure_page():
    # user_id = session.get('user_id')  # Fetching user_id from session
    user_id = 4
    # Fetching user's latest measurements by user_id
    measurements = Measurements.query.filter_by(user_id=user_id).order_by(Measurements.timestamp.desc()).first()
    return render_template("user_measure.html"
                           , tittle="Take Measurements"
                           , measurements=measurements)


@user.route("/user/take_measurements", methods=['GET', 'POST'])
def measure():
    # Initialize the body landmarks detection module
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose = mp_pose.Pose(static_image_mode=False)

    # Load MiDaS model
    midas = torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')
    midas.to('cpu')
    midas.eval()

    # Define transformations for MiDaS
    transforms = torch.hub.load('intel-isl/MiDaS', 'transforms')
    transform = transforms.small_transform

    # Constants for depth processing
    alpha = 0.5
    previous_depth = 0.0
    depth_scale = 1.0
    soft_threshold_param = 0.5

    # Known approximated measurement ratios for the respective joints
    measurement_ratios = {
        'Shoulder Width': 0.2,
        'Hip to Ankle': 0.25,
        'Chest/Bust': 0.28,
        'Waist': 0.45,
        'Sleeve Length': 0.28,
        'Armhole Depth': 0.2,
        'Back Length': 0.4,
        'Front Length': 0.4,  # Assuming front length equals back length
        'Knees': 0.1
    }
    # Ground truth measurements in inches (example values)
    ground_truth_measurements = {
        'Shoulder Width': 18.0,
        'Sleeve Length': 25.0,
        'Armhole Depth': 10.0,
        'Hip to Ankle': 40.0,
        'Back Length': 20.0,
        'Waist': 30.0,
        'Chest/Bust': 36.0,
        'Knees': 15.0,
        'Front Length': 20.0
    }

    # Function to apply exponential moving average filter
    def apply_ema_filter(current_depth):
        global previous_depth
        filtered_depth = alpha * current_depth + (1 - alpha) * previous_depth
        previous_depth = filtered_depth  # Update the previous depth value
        return filtered_depth

    # Function to convert depth to distance in inches
    def depth_to_distance(depth_value, depth_scale):
        return round(39.3701 / (depth_value * depth_scale),
                     2)  # Convert meters to inches and round to 2 decimal places

    # Function to calculate Euclidean distance between two 2D points
    def calculate_distance(point1, point2):
        return np.linalg.norm(np.array(point1) - np.array(point2))

    def visualize_measurements(img, measurements):
        x_offset = 30
        y_offset = 30
        for i, (name, value) in enumerate(measurements.items()):
            text = f'{name}: {value:.2f}"'
            cv2.putText(img, text, (x_offset, y_offset + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Initialize video capture
    cap = cv2.VideoCapture(1)

    # Initialize variables
    stable_detection_start_time = None
    all_keypoints_detected = False
    captured_img = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to RGB
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect the body landmarks in the frame
        results = pose.process(img)

        if results.pose_landmarks:
            # Extract Landmark Coordinates
            landmarks = results.pose_landmarks.landmark

            # Draw all landmarks
            mp_drawing.draw_landmarks(img, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Check if all required keypoints are detected
            required_keypoints = [mp_pose.PoseLandmark.NOSE, mp_pose.PoseLandmark.LEFT_ANKLE,
                                  mp_pose.PoseLandmark.RIGHT_ANKLE]
            if all(landmarks[keypoint].visibility > 0.5 for keypoint in required_keypoints):
                all_keypoints_detected = True
                if stable_detection_start_time is None:
                    stable_detection_start_time = time.time()
                else:
                    if time.time() - stable_detection_start_time > 5:
                        # Take a picture after 5 seconds of stable detection
                        captured_img = frame.copy()
                        break
            else:
                stable_detection_start_time = None

        # Display frame
        cv2.imshow('Video', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release video capture and close windows
    cap.release()
    cv2.destroyAllWindows()

    if all_keypoints_detected and captured_img is not None:
        # Process the captured image for measurements
        img_rgb = cv2.cvtColor(captured_img, cv2.COLOR_BGR2RGB)
        results = pose.process(img_rgb)
        landmarks = results.pose_landmarks.landmark

        # Measurement keypoints
        measurement_pairs = {
            'Shoulder Width': (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.RIGHT_SHOULDER),
            'Hip to Ankle': (mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.LEFT_ANKLE),
            'Sleeve Length': (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_WRIST),
            'Armhole Depth': (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_ELBOW),
            'Waist': (mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.RIGHT_HIP),
            'Chest/Bust': (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.RIGHT_SHOULDER),
            'Knees': (mp_pose.PoseLandmark.LEFT_KNEE, mp_pose.PoseLandmark.RIGHT_KNEE),
            'Back Length': (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_HIP),
            'Front Length': (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_HIP)
        }

        # Calculate and scale measurements
        measurements = {}
        for name, (start, end) in measurement_pairs.items():
            start_point = (
                int(landmarks[start].x * captured_img.shape[1]), int(landmarks[start].y * captured_img.shape[0]))
            end_point = (
                int(landmarks[end].x * captured_img.shape[1]), int(landmarks[end].y * captured_img.shape[0]))
            measurement_value = calculate_distance(start_point, end_point)
            if name in ['Waist', 'Chest/Bust']:
                approx_value = measurement_ratios.get(name, measurement_value)
                scaled_value = measurement_value * approx_value * 2  # Double the value for circumference
            else:
                approx_value = measurement_ratios.get(name, measurement_value)
                scaled_value = measurement_value * approx_value
            measurements[name] = scaled_value

        # Ensure the measurements are reasonable by applying a minimum threshold
        for name in measurements.keys():
            measurements[name] = max(measurements[name], soft_threshold_param)

        # Apply skew adjustment to the measurements
        measurement_values = list(measurements.values())
        skew_value = skew(measurement_values)
        for name in measurements.keys():
            measurements[name] += skew_value

        # Set front length equal to back length
        measurements['Front Length'] = measurements['Back Length']

        # Calculate accuracy
        errors = []
        for name, ground_truth in ground_truth_measurements.items():
            measured_value = measurements.get(name, 0)
            error = abs(measured_value - ground_truth) / ground_truth * 100
            errors.append(error)

        # Average error can be used for further processing if needed
        average_error = np.mean(errors)
        accuracy = 100 - average_error
        print(f"Accuracy: {accuracy:.2f}%")

        # Save measurements to the database
        measurements_entry = Measurements(
            # user_id=session.get('user_id'),
            user_id=4,
            shoulder=measurements.get('Shoulder Width'),
            sleeves=measurements.get('Sleeve Length'),
            armhole=measurements.get('Armhole Depth'),
            hip_to_ankle=measurements.get('Hip to Ankle'),
            back_l=measurements.get('Back Length'),
            waist=measurements.get('Waist'),
            chest=measurements.get('Chest/Bust'),
            knees=measurements.get('Knees'),
            front_l=measurements.get('Front Length')
        )

        db.session.add(measurements_entry)
        db.session.commit()

        # Save measurements to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as temp_file:
            for name, value in measurements.items():
                temp_file.write(f'{name}: {value:.2f}"\n')
            temp_file_path = temp_file.name

        flash(f"Your measurements file is downloaded successfully.")

        # Return the file for download
        return send_file(temp_file_path, as_attachment=True)

    else:
        flash("Failed to detect all keypoints stably for 5 seconds.")

    return redirect(url_for('user.measure_page'))


@user.route("/user/trackOrder", methods=['GET', 'POST'])
def track_order():
    if request.method == 'POST':
        # Get the tracking ID entered by the user
        tracking_id = request.form.get('tracking-id')

        # Check if the tracking ID exists in the database
        order = Order.query.filter_by(tracking_id=tracking_id).first()
        if order:
            # If order exists, render the template with order details
            return render_template("user_track_order.html",
                                   tittle="Track order",
                                   order=order,
                                   tracking_id=tracking_id)
        else:
            # If order doesn't exist, display an error message
            flash("Tracking ID not found, Please enter valid ID", "error")
    return render_template("user_track_order.html"
                           , tittle="Track order")


def convert_pkr_to_usd(amount_pkr):
    url = f"https://v6.exchangerate-api.com/v6/{exchange_rate_api_key}/pair/PKR/USD"
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200 or data['result'] != 'success':
        raise Exception('Error fetching exchange rates')

    exchange_rate = data['conversion_rate']
    return round(amount_pkr * exchange_rate, 2)


@user.route('/user/create-payment-link', methods=['POST'])
def create_payment_link():
    amount_pkr = float(request.form['amount'])
    # user_id = session.get('user_id')
    user_id = 4

    tailor_id = request.form['tail-id']
    order_tracking_id = request.form['track-id']

    try:
        amount_usd = convert_pkr_to_usd(amount_pkr)
        amount_usd_cents = int(amount_usd * 100)  # Stripe expects the amount in the smallest currency unit

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Custom Payment',
                        },
                        'unit_amount': amount_usd_cents,
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url='https://example.com/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://example.com/cancel',
        )
        print(user_id)
        payment_intent_id = checkout_session.payment_intent

        new_payment = Payment(
            user_id=user_id,
            track_id=order_tracking_id,
            tailor_id=tailor_id,
            amount_usd=amount_usd,
            amount_pkr=amount_pkr,
            payment_link=checkout_session.url,
            stripe_payment_intent=payment_intent_id,   # Save session ID
            currency='usd',
            status='pending'
        )
        new_payment.save_to_database()

        # return jsonify({'url': checkout_session.url})
        flash("Scroll down to Payment form !!")
        return render_template("user_place_order.html"
                               , tittle="Place Order"
                               , pay_url=checkout_session.url)

    except Exception as e:
        return jsonify(error=str(e)), 403


@user.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        logger.info(f'Received event: {event["type"]}')
    except ValueError as e:
        logger.error(f'Invalid payload: {e}')
        return jsonify(success=False, error='Invalid payload'), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f'Invalid signature: {e}')
        return jsonify(success=False, error='Invalid signature'), 400

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        logger.info(f'Checkout session completed: {session}')

        # Find the payment by payment_intent
        payment = Payment.query.filter_by(stripe_payment_intent=session['payment_intent']).first()
        if payment:
            payment.status = 'complete'
            payment.save_to_database()
            logger.info(f'Payment updated: {payment}')
        else:
            logger.error(f'Payment not found for payment_intent: {session["payment_intent"]}')
            return jsonify(success=False, error='Payment not found'), 404

    return jsonify(success=True)

