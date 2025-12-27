import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
from ....infrastructure.persistence.database import database
from ....infrastructure.persistence.employee_repository_impl import EmployeeRepository
from ....infrastructure.persistence.check_in_repository_impl import CheckInRepository
from ....infrastructure.persistence.group_repository_impl import GroupRepository
from ....infrastructure.persistence.employee_group_repository_impl import EmployeeGroupRepository
from ....infrastructure.persistence.telegram_user_repository_impl import TelegramUserRepository
from ....application.use_cases.record_check_in import RecordCheckInUseCase
from ....application.use_cases.get_employee import GetEmployeeUseCase
from ....application.use_cases.register_group import RegisterGroupUseCase
from ....application.use_cases.add_employee_to_group import AddEmployeeToGroupUseCase
from ....application.dto.check_in_dto import CheckInRequest
from ....domain.value_objects.check_in_type import CheckInType
from ....infrastructure.telegram.notification_service import get_notification_service

checkin_bp = Blueprint('checkin', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_repositories():
    """Get repository instances with a new session"""
    session = database.get_session()
    return (
        EmployeeRepository(session),
        CheckInRepository(session),
        GroupRepository(session),
        EmployeeGroupRepository(session),
        TelegramUserRepository(session),
        session
    )

@checkin_bp.route('/checkin', methods=['POST'])
def checkin():
    """
    Check-in endpoint for mini app
    ---
    tags:
      - Check-ins
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: telegram_user_id
        type: string
        required: true
        description: Telegram user ID
        example: "123456789"
      - in: formData
        name: group_chat_id
        type: string
        required: true
        description: Telegram group chat ID
        example: "-100123456789"
      - in: formData
        name: latitude
        type: number
        format: float
        required: true
        description: Location latitude
        example: 11.5564
      - in: formData
        name: longitude
        type: number
        format: float
        required: true
        description: Location longitude
        example: 104.9282
      - in: formData
        name: group_name
        type: string
        required: false
        description: Group name (optional)
        example: "Office Team"
      - in: formData
        name: type
        type: string
        required: false
        enum: ["checkin", "checkout"]
        default: "checkin"
        description: Type of check-in record (checkin or checkout)
        example: "checkin"
      - in: formData
        name: photo
        type: file
        required: false
        description: Check-in photo (optional, max 16MB)
    responses:
      200:
        description: Check-in successful
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Check-in recorded successfully"
            data:
              type: object
              properties:
                employee_name:
                  type: string
                  example: "John Doe"
                group_name:
                  type: string
                  example: "Office Team"
                timestamp:
                  type: string
                  example: "2024-01-01 10:30:00"
                location:
                  type: string
                  example: "11.5564, 104.9282"
                type:
                  type: string
                  enum: ["checkin", "checkout"]
                  example: "checkin"
                  description: "Type of check-in record (automatically set to 'checkin' for this endpoint)"
                photo_url:
                  type: string
                  example: "/uploads/photos/123456789_20240101_103000_photo.jpg"
      400:
        description: Bad request - missing required fields or validation error
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Missing required fields"
      404:
        description: Employee not registered
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Employee not registered. Please register first."
      500:
        description: Internal server error
    """
    try:
        # Get form data
        telegram_user_id = request.form.get('telegram_user_id')
        group_chat_id = request.form.get('group_chat_id')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        type_str = request.form.get('type', 'checkin')  # Default to 'checkin' if not provided

        # Validate required fields
        if not all([telegram_user_id, group_chat_id, latitude, longitude]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: telegram_user_id, group_chat_id, latitude, longitude'
            }), 400

        # Convert to appropriate types
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            # Convert type string to enum
            check_in_type = CheckInType.CHECKOUT if type_str.lower() == 'checkout' else CheckInType.CHECKIN
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid latitude or longitude format'
            }), 400

        # Get repositories
        employee_repo, check_in_repo, group_repo, employee_group_repo, telegram_user_repo, session = get_repositories()

        try:
            # Get or create employee
            get_employee_use_case = GetEmployeeUseCase(employee_repo)
            employee = get_employee_use_case.execute_by_telegram_id(str(telegram_user_id))

            if not employee:
                return jsonify({
                    'success': False,
                    'error': 'Employee not registered. Please register first.'
                }), 404

            # Get or create group
            register_group_use_case = RegisterGroupUseCase(group_repo, telegram_user_repo)
            group_name = request.form.get('group_name', f'Group {group_chat_id}')
            group = register_group_use_case.execute(
                chat_id=str(group_chat_id),
                name=group_name
            )

            # Create employee-group association if it doesn't exist
            # This automatically links the employee to this group on first check-in
            add_employee_to_group_use_case = AddEmployeeToGroupUseCase(
                employee_group_repo,
                employee_repo,
                group_repo
            )
            add_employee_to_group_use_case.execute(
                employee_id=employee.id,
                group_id=group.id
            )

            # Handle photo upload
            photo_url = None
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Create unique filename with timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_filename = f"{telegram_user_id}_{timestamp}_{filename}"

                    # Ensure upload directory exists
                    upload_folder = 'uploads/photos'
                    os.makedirs(upload_folder, exist_ok=True)

                    # Save file
                    file_path = os.path.join(upload_folder, unique_filename)
                    file.save(file_path)
                    photo_url = f"/uploads/photos/{unique_filename}"

            # Create check-in request
            check_in_request = CheckInRequest(
                employee_id=employee.id,
                group_id=group.id,
                latitude=latitude,
                longitude=longitude,
                type=check_in_type,
                photo_url=photo_url
            )

            # Execute check-in
            record_check_in_use_case = RecordCheckInUseCase(
                check_in_repo,
                employee_repo,
                group_repo
            )
            response = record_check_in_use_case.execute(check_in_request)

            # Send notification to group
            try:
                notification_service = get_notification_service()
                if check_in_type == CheckInType.CHECKOUT:
                    notification_service.send_checkout_notification(
                        group_chat_id=group_chat_id,
                        employee_name=employee.name,
                        timestamp=response.timestamp,
                        location=response.location,
                        latitude=latitude,
                        longitude=longitude,
                        photo_url=photo_url
                    )
                else:
                    notification_service.send_checkin_notification(
                        group_chat_id=group_chat_id,
                        employee_name=employee.name,
                        timestamp=response.timestamp,
                        location=response.location,
                        latitude=latitude,
                        longitude=longitude,
                        photo_url=photo_url
                    )
            except Exception as e:
                # Log error but don't fail the check-in
                print(f"Failed to send notification: {e}")

            return jsonify({
                'success': True,
                'message': response.message,
                'data': {
                    'employee_name': employee.name,
                    'group_name': group.name,
                    'timestamp': response.timestamp,
                    'location': response.location,
                    'type': response.type,
                    'photo_url': photo_url
                }
            }), 200

        finally:
            session.close()

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@checkin_bp.route('/checkout', methods=['POST'])
def checkout():
    """
    Check-out endpoint for mini app
    ---
    tags:
      - Check-outs
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: telegram_user_id
        type: string
        required: true
        description: Telegram user ID
        example: "123456789"
      - in: formData
        name: group_chat_id
        type: string
        required: true
        description: Telegram group chat ID
        example: "-100123456789"
      - in: formData
        name: latitude
        type: number
        format: float
        required: true
        description: Location latitude
        example: 11.5564
      - in: formData
        name: longitude
        type: number
        format: float
        required: true
        description: Location longitude
        example: 104.9282
      - in: formData
        name: group_name
        type: string
        required: false
        description: Group name (optional)
        example: "Office Team"
      - in: formData
        name: type
        type: string
        required: false
        enum: ["checkin", "checkout"]
        default: "checkin"
        description: Type of check-in record (checkin or checkout)
        example: "checkout"
      - in: formData
        name: photo
        type: file
        required: false
        description: Check-out photo (optional, max 16MB)
    responses:
      200:
        description: Check-out successful
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Check-out recorded successfully"
            data:
              type: object
              properties:
                employee_name:
                  type: string
                  example: "John Doe"
                group_name:
                  type: string
                  example: "Office Team"
                timestamp:
                  type: string
                  example: "2024-01-01 10:30:00"
                location:
                  type: string
                  example: "11.5564, 104.9282"
                type:
                  type: string
                  enum: ["checkin", "checkout"]
                  example: "checkout"
                  description: "Type of check-in record (automatically set to 'checkout' for this endpoint)"
                photo_url:
                  type: string
                  example: "/uploads/photos/123456789_20240101_103000_photo.jpg"
      400:
        description: Bad request - missing required fields or validation error
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Missing required fields"
      404:
        description: Employee not registered
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Employee not registered. Please register first."
      500:
        description: Internal server error
    """
    try:
        # Get form data
        telegram_user_id = request.form.get('telegram_user_id')
        group_chat_id = request.form.get('group_chat_id')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        type_str = request.form.get('type', 'checkin')  # Default to 'checkin' if not provided

        # Validate required fields
        if not all([telegram_user_id, group_chat_id, latitude, longitude]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: telegram_user_id, group_chat_id, latitude, longitude'
            }), 400

        # Convert to appropriate types
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            # Convert type string to enum
            check_in_type = CheckInType.CHECKOUT if type_str.lower() == 'checkout' else CheckInType.CHECKIN
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid latitude or longitude format'
            }), 400

        # Get repositories
        employee_repo, check_in_repo, group_repo, employee_group_repo, telegram_user_repo, session = get_repositories()

        try:
            # Get or create employee
            get_employee_use_case = GetEmployeeUseCase(employee_repo)
            employee = get_employee_use_case.execute_by_telegram_id(str(telegram_user_id))

            if not employee:
                return jsonify({
                    'success': False,
                    'error': 'Employee not registered. Please register first.'
                }), 404

            # Get or create group
            register_group_use_case = RegisterGroupUseCase(group_repo, telegram_user_repo)
            group_name = request.form.get('group_name', f'Group {group_chat_id}')
            group = register_group_use_case.execute(
                chat_id=str(group_chat_id),
                name=group_name
            )

            # Create employee-group association if it doesn't exist
            # This automatically links the employee to this group on first check-out
            add_employee_to_group_use_case = AddEmployeeToGroupUseCase(
                employee_group_repo,
                employee_repo,
                group_repo
            )
            add_employee_to_group_use_case.execute(
                employee_id=employee.id,
                group_id=group.id
            )

            # Handle photo upload
            photo_url = None
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Create unique filename with timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_filename = f"{telegram_user_id}_{timestamp}_{filename}"

                    # Ensure upload directory exists
                    upload_folder = 'uploads/photos'
                    os.makedirs(upload_folder, exist_ok=True)

                    # Save file
                    file_path = os.path.join(upload_folder, unique_filename)
                    file.save(file_path)
                    photo_url = f"/uploads/photos/{unique_filename}"

            # Create check-out request
            check_in_request = CheckInRequest(
                employee_id=employee.id,
                group_id=group.id,
                latitude=latitude,
                longitude=longitude,
                type=check_in_type,
                photo_url=photo_url
            )

            # Execute check-in (same use case, different messaging)
            record_check_in_use_case = RecordCheckInUseCase(
                check_in_repo,
                employee_repo,
                group_repo
            )
            response = record_check_in_use_case.execute(check_in_request)

            # Send notification to group
            try:
                notification_service = get_notification_service()
                if check_in_type == CheckInType.CHECKOUT:
                    notification_service.send_checkout_notification(
                        group_chat_id=group_chat_id,
                        employee_name=employee.name,
                        timestamp=response.timestamp,
                        location=response.location,
                        latitude=latitude,
                        longitude=longitude,
                        photo_url=photo_url
                    )
                else:
                    notification_service.send_checkin_notification(
                        group_chat_id=group_chat_id,
                        employee_name=employee.name,
                        timestamp=response.timestamp,
                        location=response.location,
                        latitude=latitude,
                        longitude=longitude,
                        photo_url=photo_url
                    )
            except Exception as e:
                # Log error but don't fail the request
                print(f"Failed to send notification: {e}")

            return jsonify({
                'success': True,
                'message': 'Check-out recorded successfully',
                'data': {
                    'employee_name': employee.name,
                    'group_name': group.name,
                    'timestamp': response.timestamp,
                    'location': response.location,
                    'type': response.type,
                    'photo_url': photo_url
                }
            }), 200

        finally:
            session.close()

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@checkin_bp.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    ---
    tags:
      - Health
    responses:
      200:
        description: API is healthy and running
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "API is running"
    """
    return jsonify({
        'success': True,
        'message': 'API is running'
    }), 200
