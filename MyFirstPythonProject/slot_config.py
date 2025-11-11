"""
Slot configuration module for Click Board slots.

Maps slot numbers to their corresponding BeagleBone GPIO pins.
"""

# Slot to pin mapping
# Format: slot_number: {"pin_name": "pin_number", "type": "GPIO_INPUT|GPIO_OUTPUT|PWM"}
SLOT_CONFIG = {
    1: {
        "input": "P9_15",
        "input_type": "GPIO_INPUT"
    },
    2: {
        "input": "P9_41",
        "input_type": "GPIO_INPUT",
        "output": "P9_23",
        "output_type": "GPIO_OUTPUT"
    },
    3: {
        "pwm": "P8_19",
        "pwm_type": "PWM"
    },
    4: {
        "input": "P8_10",
        "input_type": "GPIO_INPUT"
    }
}


def get_slot_pin(slot: int, pin_type: str = "input") -> str:
    """
    Get pin number for a given slot and pin type.
    
    Args:
        slot: Slot number (1-4)
        pin_type: Type of pin ("input", "output", "pwm")
    
    Returns:
        Pin string (e.g., "P9_15")
    
    Raises:
        ValueError: If slot or pin_type is invalid
    """
    if slot not in SLOT_CONFIG:
        raise ValueError(f"Invalid slot number: {slot}. Valid slots are: {list(SLOT_CONFIG.keys())}")
    
    slot_config = SLOT_CONFIG[slot]
    
    if pin_type == "pwm":
        if "pwm" not in slot_config:
            raise ValueError(f"Slot {slot} does not have a PWM pin")
        return slot_config["pwm"]
    elif pin_type == "input":
        if "input" not in slot_config:
            raise ValueError(f"Slot {slot} does not have an input pin")
        return slot_config["input"]
    elif pin_type == "output":
        if "output" not in slot_config:
            raise ValueError(f"Slot {slot} does not have an output pin")
        return slot_config["output"]
    else:
        raise ValueError(f"Invalid pin_type: {pin_type}. Valid types are: input, output, pwm")


def get_slot_config(slot: int) -> dict:
    """
    Get full configuration for a slot.
    
    Args:
        slot: Slot number (1-4)
    
    Returns:
        Dictionary with slot configuration
    
    Raises:
        ValueError: If slot is invalid
    """
    if slot not in SLOT_CONFIG:
        raise ValueError(f"Invalid slot number: {slot}. Valid slots are: {list(SLOT_CONFIG.keys())}")
    
    return SLOT_CONFIG[slot].copy()

