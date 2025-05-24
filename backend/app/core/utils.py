pythonimport re
from typing import Optional

def validate_mobile(mobile: str) -> bool:
    """
    Validate Iranian mobile number.
    Valid formats: 09XXXXXXXXX, +989XXXXXXXXX, 989XXXXXXXXX
    """
    # Remove any spaces, hyphens, etc.
    mobile = re.sub(r'\s+|-|\(|\)', '', mobile)
    
    # Handle different formats
    if mobile.startswith('+98'):
        mobile = '0' + mobile[3:]
    elif mobile.startswith('98') and len(mobile) >= 10:
        mobile = '0' + mobile[2:]
    
    # Check if it matches the pattern
    pattern = r'^09\d{9}$'
    return bool(re.match(pattern, mobile))


def format_mobile(mobile: str) -> Optional[str]:
    """
    Format mobile number to a standard format (09XXXXXXXXX).
    Returns None if the mobile is invalid.
    """
    # Remove any spaces, hyphens, etc.
    mobile = re.sub(r'\s+|-|\(|\)', '', mobile)
    
    # Handle different formats
    if mobile.startswith('+98'):
        mobile = '0' + mobile[3:]
    elif mobile.startswith('98') and len(mobile) >= 10:
        mobile = '0' + mobile[2:]
    
    # Check if it matches the pattern
    pattern = r'^09\d{9}$'
    if re.match(pattern, mobile):
        return mobile
    
    return None