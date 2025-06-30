from pydantic import ValidationError
from job_spec_models import JobSpec


def validate_job_spec(job_spec_dict):
    """
    Validate job specification dictionary and return JobSpec object

    Args:
        job_spec_dict: Raw job specification dictionary

    Returns:
        JobSpec: Validated JobSpec object

    Raises:
        ValueError: If validation fails with formatted error messages
    """
    try:
        return JobSpec(**job_spec_dict)
    except ValidationError as e:
        formatted_errors = format_validation_errors(e)
        raise ValueError(f"Invalid job specification:{formatted_errors}")


def format_validation_errors(e: ValidationError) -> str:
    """Format Pydantic validation errors into user-friendly messages"""
    error_messages = []
    for error in e.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        error_msg = error["msg"]
        # input_val = error.get("input", "N/A")
        error_messages.append(f"Field '{field_path}': {error_msg}")

    return "\n  - " + "\n  - ".join(error_messages)
