from flask import Blueprint, request, jsonify
from ....infrastructure.persistence.database import database
from ....infrastructure.persistence.employee_repository_impl import EmployeeRepository
from ....infrastructure.persistence.salary_advance_repository_impl import SalaryAdvanceRepository
from ....infrastructure.persistence.allowance_repository_impl import AllowanceRepository
from ....application.use_cases.register_employee import RegisterEmployeeUseCase
from ....application.use_cases.get_employee_status import GetEmployeeStatusUseCase
from ....application.use_cases.record_allowance import RecordAllowanceUseCase
from ....application.use_cases.record_salary_advance import RecordSalaryAdvanceUseCase
from ....application.dto.employee_dto import RegisterEmployeeRequest
from ....application.dto.allowance_dto import RecordAllowanceRequest
from ....application.dto.salary_advance_dto import SalaryAdvanceRequest

employee_bp = Blueprint('employee', __name__)

def get_repositories():
    """Get repository instances with a new session"""
    session = database.get_session()
    return (
        EmployeeRepository(session),
        SalaryAdvanceRepository(session),
        AllowanceRepository(session),
        session
    )

@employee_bp.route('/employees/register', methods=['POST'])
def register_employee():
    """
    Register a new employee
    ---
    tags:
      - Employees
    parameters:
      - in: body
        name: body
        required: true
        description: Employee registration data
        schema:
          type: object
          required:
            - telegram_id
            - name
          properties:
            telegram_id:
              type: string
              example: "123456789"
              description: Telegram user ID
            name:
              type: string
              example: "John Doe"
              description: Employee full name
            phone:
              type: string
              example: "1234567890"
              description: Employee phone number
            role:
              type: string
              example: "Developer"
              description: Employee role/position
            date_start_work:
              type: string
              example: "2024-01-01"
              description: Date employee started work (ISO format or YYYY-MM-DD)
            probation_months:
              type: integer
              example: 3
              description: Number of probation months
            base_salary:
              type: number
              format: float
              example: 1000.0
              description: Base salary amount
            bonus:
              type: number
              format: float
              example: 100.0
              description: Bonus amount
    responses:
      201:
        description: Employee registered successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Employee registered successfully"
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                telegram_id:
                  type: string
                  example: "123456789"
                name:
                  type: string
                  example: "John Doe"
                phone:
                  type: string
                  example: "1234567890"
                role:
                  type: string
                  example: "Developer"
                date_start_work:
                  type: string
                  example: "2024-01-01T00:00:00"
                probation_months:
                  type: integer
                  example: 3
                base_salary:
                  type: number
                  example: 1000.0
                bonus:
                  type: number
                  example: 100.0
                created_at:
                  type: string
                  example: "2024-01-01T10:30:00"
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
              example: "Missing required fields: telegram_id, name"
      500:
        description: Internal server error
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('telegram_id') or not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: telegram_id, name'
            }), 400

        # Create request DTO
        register_request = RegisterEmployeeRequest(
            telegram_id=str(data['telegram_id']),
            name=data['name'],
            phone=data.get('phone'),
            role=data.get('role'),
            date_start_work=data.get('date_start_work'),
            probation_months=data.get('probation_months'),
            base_salary=data.get('base_salary'),
            bonus=data.get('bonus')
        )

        # Get repositories
        employee_repo, _, _, session = get_repositories()

        try:
            # Execute use case
            use_case = RegisterEmployeeUseCase(employee_repo)
            response = use_case.execute(register_request)

            return jsonify({
                'success': True,
                'message': 'Employee registered successfully',
                'data': {
                    'id': response.id,
                    'telegram_id': response.telegram_id,
                    'name': response.name,
                    'phone': response.phone,
                    'role': response.role,
                    'date_start_work': response.date_start_work,
                    'probation_months': response.probation_months,
                    'base_salary': response.base_salary,
                    'bonus': response.bonus,
                    'created_at': response.created_at
                }
            }), 201

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

@employee_bp.route('/employees/<employee_id>/status', methods=['GET'])
def get_employee_status(employee_id):
    """
    Get employee status including salary, borrows, and allowances
    ---
    tags:
      - Staff Operations
    parameters:
      - in: path
        name: employee_id
        type: integer
        required: true
        description: Employee ID
        example: 1
    responses:
      200:
        description: Employee status retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                employee:
                  type: object
                  properties:
                    id:
                      type: integer
                    telegram_id:
                      type: string
                    name:
                      type: string
                    phone:
                      type: string
                    role:
                      type: string
                    date_start_work:
                      type: string
                    probation_months:
                      type: integer
                    base_salary:
                      type: number
                    bonus:
                      type: number
                    created_at:
                      type: string
                salary_advances:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                      amount:
                        type: string
                      note:
                        type: string
                      created_by:
                        type: string
                      timestamp:
                        type: string
                allowances:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                      amount:
                        type: number
                      allowance_type:
                        type: string
                      note:
                        type: string
                      created_by:
                        type: string
                      timestamp:
                        type: string
                summary:
                  type: object
                  properties:
                    total_salary_advances:
                      type: number
                    total_allowances:
                      type: number
                    total_compensation:
                      type: number
      404:
        description: Employee not found
      500:
        description: Internal server error
    """
    try:
        # Get repositories
        employee_repo, salary_advance_repo, allowance_repo, session = get_repositories()

        try:
            # Execute use case
            use_case = GetEmployeeStatusUseCase(
                employee_repo,
                salary_advance_repo,
                allowance_repo
            )
            response = use_case.execute_by_id(int(employee_id))

            return jsonify({
                'success': True,
                'data': {
                    'employee': {
                        'id': response.id,
                        'telegram_id': response.telegram_id,
                        'name': response.name,
                        'phone': response.phone,
                        'role': response.role,
                        'date_start_work': response.date_start_work,
                        'probation_months': response.probation_months,
                        'base_salary': response.base_salary,
                        'bonus': response.bonus,
                        'created_at': response.created_at
                    },
                    'salary_advances': [
                        {
                            'id': adv.id,
                            'amount': adv.amount,
                            'note': adv.note,
                            'created_by': adv.created_by,
                            'timestamp': adv.timestamp
                        }
                        for adv in response.salary_advances
                    ],
                    'allowances': [
                        {
                            'id': allow.id,
                            'amount': allow.amount,
                            'allowance_type': allow.allowance_type,
                            'note': allow.note,
                            'created_by': allow.created_by,
                            'timestamp': allow.timestamp
                        }
                        for allow in response.allowances
                    ],
                    'summary': {
                        'total_salary_advances': response.total_salary_advances,
                        'total_allowances': response.total_allowances,
                        'total_compensation': (response.base_salary or 0) + (response.bonus or 0) + response.total_allowances
                    }
                }
            }), 200

        finally:
            session.close()

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@employee_bp.route('/employees/telegram/<telegram_id>/status', methods=['GET'])
def get_employee_status_by_telegram_id(telegram_id):
    """
    Get employee status by Telegram ID
    ---
    tags:
      - Staff Operations
    parameters:
      - in: path
        name: telegram_id
        type: string
        required: true
        description: Telegram user ID
        example: "123456789"
    responses:
      200:
        description: Employee status retrieved successfully
      404:
        description: Employee not found
      500:
        description: Internal server error
    """
    try:
        # Get repositories
        employee_repo, salary_advance_repo, allowance_repo, session = get_repositories()

        try:
            # Execute use case
            use_case = GetEmployeeStatusUseCase(
                employee_repo,
                salary_advance_repo,
                allowance_repo
            )
            response = use_case.execute_by_telegram_id(str(telegram_id))

            return jsonify({
                'success': True,
                'data': {
                    'employee': {
                        'id': response.id,
                        'telegram_id': response.telegram_id,
                        'name': response.name,
                        'phone': response.phone,
                        'role': response.role,
                        'date_start_work': response.date_start_work,
                        'probation_months': response.probation_months,
                        'base_salary': response.base_salary,
                        'bonus': response.bonus,
                        'created_at': response.created_at
                    },
                    'salary_advances': [
                        {
                            'id': adv.id,
                            'amount': adv.amount,
                            'note': adv.note,
                            'created_by': adv.created_by,
                            'timestamp': adv.timestamp
                        }
                        for adv in response.salary_advances
                    ],
                    'allowances': [
                        {
                            'id': allow.id,
                            'amount': allow.amount,
                            'allowance_type': allow.allowance_type,
                            'note': allow.note,
                            'created_by': allow.created_by,
                            'timestamp': allow.timestamp
                        }
                        for allow in response.allowances
                    ],
                    'summary': {
                        'total_salary_advances': response.total_salary_advances,
                        'total_allowances': response.total_allowances,
                        'total_compensation': (response.base_salary or 0) + (response.bonus or 0) + response.total_allowances
                    }
                }
            }), 200

        finally:
            session.close()

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@employee_bp.route('/employees/<employee_id>/allowances', methods=['POST'])
def record_allowance(employee_id):
    """
    Record an allowance for an employee
    ---
    tags:
      - Staff Operations
    parameters:
      - in: path
        name: employee_id
        type: integer
        required: true
        description: Employee ID
        example: 1
      - in: body
        name: body
        required: true
        description: Allowance data
        schema:
          type: object
          required:
            - amount
            - allowance_type
            - created_by
          properties:
            amount:
              type: number
              format: float
              example: 50.0
              description: Allowance amount
            allowance_type:
              type: string
              example: "transport"
              description: Type of allowance (e.g., transport, meal, housing)
            created_by:
              type: string
              example: "manager_name"
              description: Who created this allowance record
            note:
              type: string
              example: "Monthly transport allowance"
              description: Optional notes
    responses:
      201:
        description: Allowance recorded successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Allowance recorded successfully"
            data:
              type: object
              properties:
                id:
                  type: integer
                employee_id:
                  type: integer
                amount:
                  type: number
                allowance_type:
                  type: string
                note:
                  type: string
                created_by:
                  type: string
                timestamp:
                  type: string
      400:
        description: Bad request - validation error
      500:
        description: Internal server error
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not all([data.get('amount'), data.get('allowance_type'), data.get('created_by')]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: amount, allowance_type, created_by'
            }), 400

        # Create request DTO
        allowance_request = RecordAllowanceRequest(
            employee_id=int(employee_id),
            amount=float(data['amount']),
            allowance_type=data['allowance_type'],
            created_by=data['created_by'],
            note=data.get('note')
        )

        # Get repositories
        employee_repo, _, allowance_repo, session = get_repositories()

        try:
            # Execute use case
            use_case = RecordAllowanceUseCase(allowance_repo, employee_repo)
            response = use_case.execute(allowance_request)

            return jsonify({
                'success': True,
                'message': 'Allowance recorded successfully',
                'data': {
                    'id': response.id,
                    'employee_id': response.employee_id,
                    'amount': response.amount,
                    'allowance_type': response.allowance_type,
                    'note': response.note,
                    'created_by': response.created_by,
                    'timestamp': response.timestamp
                }
            }), 201

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

@employee_bp.route('/employees/<employee_id>/salary-advances', methods=['POST'])
def record_salary_advance(employee_id):
    """
    Record a salary advance (borrow) for an employee
    ---
    tags:
      - Staff Operations
    parameters:
      - in: path
        name: employee_id
        type: integer
        required: true
        description: Employee ID
        example: 1
      - in: body
        name: body
        required: true
        description: Salary advance data
        schema:
          type: object
          required:
            - amount
            - created_by
          properties:
            amount:
              type: number
              format: float
              example: 100.0
              description: Salary advance amount
            created_by:
              type: string
              example: "manager_name"
              description: Who authorized this salary advance
            note:
              type: string
              example: "Emergency advance"
              description: Optional notes
    responses:
      201:
        description: Salary advance recorded successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Salary advance recorded successfully"
            data:
              type: object
              properties:
                employee_name:
                  type: string
                amount:
                  type: string
                timestamp:
                  type: string
      400:
        description: Bad request - validation error
      404:
        description: Employee not found
      500:
        description: Internal server error
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not all([data.get('amount'), data.get('created_by')]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: amount, created_by'
            }), 400

        # Get repositories
        employee_repo, salary_advance_repo, _, session = get_repositories()

        try:
            # Get employee to find their name
            employee = employee_repo.find_by_id(int(employee_id))
            if not employee:
                return jsonify({
                    'success': False,
                    'error': f'Employee with ID {employee_id} not found'
                }), 404

            # Create request DTO (the existing use case uses employee_name)
            salary_advance_request = SalaryAdvanceRequest(
                employee_name=employee.name,
                amount=float(data['amount']),
                created_by=data['created_by'],
                note=data.get('note')
            )

            # Execute use case
            use_case = RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
            response = use_case.execute(salary_advance_request)

            return jsonify({
                'success': True,
                'message': response.message,
                'data': {
                    'employee_name': response.employee_name,
                    'amount': response.amount,
                    'timestamp': response.timestamp
                }
            }), 201

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
