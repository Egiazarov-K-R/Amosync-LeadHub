"""
Pydantic schemas for Lead validation and restructuring.

This module defines the data structures used to validate incoming leads
from external systems (like Haier API or the randomuser.me mock) and ensure
they are clean and safe to be written to PostgreSQL and AmoCRM.

Classes:
    LeadCreate: Schema for validating raw lead data and generating default values.
"""

import random
from pydantic import BaseModel, Field, field_validator


class LeadCreate(BaseModel):
    """
    Schema to validate and prepare raw lead data for processing.
    
    Automatically cleans the client's phone number and assigns a random
    budget (price) between 35,000 and 60,000 rubles if not provided.

    Business Logic for Price Generation:
    1. The external manufacturer (Haier) only provides raw contact details. They do not know 
       the dealer's local pricing, regional installation costs, or final negotiation margin.
    2. Creating deals in AmoCRM with a 0 RUB budget ruins sales pipeline forecasting, 
       analytical dashboards, and manager performance reports.
    3. Generating a realistic estimated budget (35,000 - 60,000 RUB, reflecting the typical cost 
       of a Haier AC unit with standard installation) populates the CRM with immediate, 
       actionable pipeline value from the moment of capture.
    """
    external_lead_id: str
    client_name: str
    client_phone: str
    price: int = Field(default_factory=lambda: random.randint(35000, 60000))

    @field_validator("client_phone")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        """
        Cleans the input phone number string by keeping only digits and '+'.
        
        Args:
            v (str): Raw phone number from the API.
            
        Returns:
            str: Cleaned phone number string.
            
        Raises:
            ValueError: If the cleaned phone number contains no digits.
        """
        # randomuser.me sends phone numbers like "(999)-111-2233".
        # This validator will only accept "9991112233" (or "+7..." if it's a plus sign)
        cleaned = "".join(c for c in v if c.isdigit() or c == "+")
        if not cleaned:
            raise ValueError("Phone number must contain digits.")
        return cleaned
