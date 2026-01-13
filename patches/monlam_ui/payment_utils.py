"""
Payment Calculation Utilities for Monlam Analytics

Calculates payment for annotators and reviewers based on project-specific rules.
"""

import re
from typing import Dict, Optional


def count_tibetan_syllables(text: str) -> int:
    """
    Count Tibetan syllables in a text.
    
    Tibetan syllables are typically separated by:
    - Tsheg (་) - Tibetan syllable separator
    - Spaces
    - Line breaks
    
    Args:
        text: Text string (can contain Tibetan characters)
    
    Returns:
        Number of syllables counted
    """
    if not text or not isinstance(text, str):
        return 0
    
    # Remove extra whitespace
    text = text.strip()
    if not text:
        return 0
    
    # Split by tsheg (་) - the primary Tibetan syllable separator
    # Also split by spaces and line breaks
    # Tibetan Unicode range: U+0F00 to U+0FFF
    # Tsheg: U+0F0B (་)
    
    # Split by tsheg first
    parts = re.split(r'[་\s\n\r]+', text)
    
    # Filter out empty strings
    syllables = [p for p in parts if p.strip()]
    
    # If no tsheg found, try splitting by spaces
    if len(syllables) == 1 and text:
        # Check if text contains Tibetan characters
        has_tibetan = bool(re.search(r'[\u0F00-\u0FFF]', text))
        if has_tibetan:
            # For Tibetan text without tsheg, count each character group
            # This is a fallback - ideally text should have tsheg
            syllables = re.findall(r'[\u0F00-\u0FFF]+', text)
        else:
            # For non-Tibetan text, count words
            syllables = text.split()
    
    return len(syllables)


def get_project_payment_config(project_name: str) -> Optional[Dict]:
    """
    Get payment configuration for a project.
    
    Returns:
        Dict with payment rates, or None if project not configured
    """
    # Project-specific payment rules
    payment_configs = {
        # AM_AB_A and KH_AB_A: Rs. 5 × Total Audio Minutes + Rs. 2 per audio segment
        'AM_AB_A': {
            'audio_minute_rate': 5.0,
            'segment_rate': 2.0,
            'syllable_rate': None,  # Not used for this project
        },
        'KH_AB_A': {
            'audio_minute_rate': 5.0,
            'segment_rate': 2.0,
            'syllable_rate': None,
        },
        
        # KH_MV_A, KH_MV_B, AM_MV_B, AM_MV_A: Rs. 5 × Total Audio Minutes + Rs. 0.35 per reviewed syllable
        'KH_MV_A': {
            'audio_minute_rate': 5.0,
            'segment_rate': None,
            'syllable_rate': 0.35,
        },
        'KH_MV_B': {
            'audio_minute_rate': 5.0,
            'segment_rate': None,
            'syllable_rate': 0.35,
        },
        'AM_MV_B': {
            'audio_minute_rate': 5.0,
            'segment_rate': None,
            'syllable_rate': 0.35,
        },
        'AM_MV_A': {
            'audio_minute_rate': 5.0,
            'segment_rate': None,
            'syllable_rate': 0.35,
        },
        
        # STT_TEACHING_A: Rs. 5 × Total Audio Minutes + Rs. 0.3 per reviewed syllable
        'STT_TEACHING_A': {
            'audio_minute_rate': 5.0,
            'segment_rate': None,
            'syllable_rate': 0.3,
        },
    }
    
    # Check exact match first
    if project_name in payment_configs:
        return payment_configs[project_name]
    
    # Check if project name contains any of the keys (for partial matches)
    for key, config in payment_configs.items():
        if key in project_name:
            return config
    
    return None


def calculate_payment(
    project_name: str,
    total_audio_minutes: float,
    approved_segments: int = 0,
    reviewed_syllables: int = 0,
    is_reviewer: bool = False
) -> Dict:
    """
    Calculate payment for an annotator or reviewer.
    
    Args:
        project_name: Name of the project
        total_audio_minutes: Total audio duration in minutes
        approved_segments: Number of approved audio segments (for annotators)
        reviewed_syllables: Number of reviewed syllables (for reviewers)
        is_reviewer: Whether this is a reviewer (affects which rates apply)
    
    Returns:
        Dict with:
        - total_rupees: Total payment in Rupees
        - audio_payment: Payment from audio minutes
        - segment_payment: Payment from segments (if applicable)
        - syllable_payment: Payment from syllables (if applicable)
        - breakdown: Human-readable breakdown
    """
    config = get_project_payment_config(project_name)
    
    if not config:
        return {
            'total_rupees': 0.0,
            'audio_payment': 0.0,
            'segment_payment': 0.0,
            'syllable_payment': 0.0,
            'breakdown': 'Project not configured for payment calculation',
            'configured': False
        }
    
    # Calculate audio payment (applies to both annotators and reviewers)
    audio_payment = total_audio_minutes * config['audio_minute_rate']
    
    # Calculate segment payment (for AM_AB_A, KH_AB_A - applies to both annotators and reviewers)
    segment_payment = 0.0
    if config['segment_rate'] is not None and approved_segments > 0:
        segment_payment = approved_segments * config['segment_rate']
    
    # Calculate syllable payment (for MV projects and STT_TEACHING_A - applies to both annotators and reviewers)
    syllable_payment = 0.0
    if config['syllable_rate'] is not None and reviewed_syllables > 0:
        syllable_payment = reviewed_syllables * config['syllable_rate']
    
    total_rupees = audio_payment + segment_payment + syllable_payment
    
    # Create breakdown
    breakdown_parts = []
    if audio_payment > 0:
        breakdown_parts.append(f"Audio: {total_audio_minutes:.2f} min × Rs. {config['audio_minute_rate']} = Rs. {audio_payment:.2f}")
    if segment_payment > 0:
        breakdown_parts.append(f"Segments: {approved_segments} × Rs. {config['segment_rate']} = Rs. {segment_payment:.2f}")
    if syllable_payment > 0:
        breakdown_parts.append(f"Syllables: {reviewed_syllables} × Rs. {config['syllable_rate']} = Rs. {syllable_payment:.2f}")
    
    breakdown = " + ".join(breakdown_parts) if breakdown_parts else "No payment applicable"
    
    return {
        'total_rupees': round(total_rupees, 2),
        'audio_payment': round(audio_payment, 2),
        'segment_payment': round(segment_payment, 2),
        'syllable_payment': round(syllable_payment, 2),
        'breakdown': breakdown,
        'configured': True
    }

