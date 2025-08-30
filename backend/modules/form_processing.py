"""
Form Data Processing Utilities Module - API Version
==================================================

Processes form data from API requests for document generation.
Handles text placeholders, image uploads, and data formatting.
"""


def format_address(line1, line2, line3):
    """
    Format address with first two lines combined by comma, third line on new line.
    Example: "Building Name, Street Address\nCity, State, PIN"
    """
    # Combine first two lines with comma if both exist
    first_part = []
    if line1 and line1.strip():
        first_part.append(line1.strip())
    if line2 and line2.strip():
        first_part.append(line2.strip())
    
    # Create the address parts
    address_parts = []
    if first_part:
        address_parts.append(', '.join(first_part))
    if line3 and line3.strip():
        address_parts.append(line3.strip())
    
    return '\n'.join(address_parts)


def format_address_oneline(line1, line2, line3):
    """
    Format address as a single line with all parts separated by commas.
    Example: "Building Name, Street Address, City, State, PIN"
    """
    address_parts = []
    if line1 and line1.strip():
        address_parts.append(line1.strip())
    if line2 and line2.strip():
        address_parts.append(line2.strip())
    if line3 and line3.strip():
        address_parts.append(line3.strip())
    
    return ', '.join(address_parts)


def format_date(date_string):
    """
    Convert date from YYYY-MM-DD format to DD-MM-YYYY format.
    Example: "2023-05-29" becomes "29-05-2023"
    """
    if not date_string:
        return ''
    
    try:
        # Split the date and rearrange
        parts = date_string.split('-')
        if len(parts) == 3:
            year, month, day = parts
            return f"{day}-{month}-{year}"
        else:
            return date_string  # Return as-is if format is unexpected
    except:
        return date_string  # Return as-is if there's any error


def combine_person_list(prefixes, names, designations):
    """Combine person data into formatted strings with proper grammar."""
    people = []
    for p, n, d in zip(prefixes, names, designations):
        if n and n.strip():
            entry = f"{p} {n.strip()}" if p else n.strip()
            if d and d.strip():
                entry += f" ({d.strip()})"
            people.append(entry)
    
    # Format with proper grammar: use "and" before the last item
    if len(people) == 0:
        return ''
    elif len(people) == 1:
        return people[0]
    elif len(people) == 2:
        return f"{people[0]} and {people[1]}"
    else:
        return f"{', '.join(people[:-1])} and {people[-1]}"


def process_form_data_api(request):
    """Process all form data from API request and return structured data."""
    
    # Helper function to get list data from form
    def get_form_list(key):
        """Get list data from form, handling both single values and lists."""
        values = request.form.getlist(key)
        if not values:
            # Try without [] suffix
            single_value = request.form.get(key.rstrip('[]'))
            if single_value:
                values = [single_value]
        return values or []
    
    # Dynamic Person Lists - try direct fields first, then arrays
    def get_person_data(base_name):
        """Get person data, trying direct field first, then arrays."""
        # Try direct field first (e.g., 'rrecl_people')
        direct_value = request.form.get(base_name, '').strip()
        if direct_value:
            return direct_value
        
        # Fall back to array format
        if base_name == 'rrecl_people':
            return combine_person_list(
                get_form_list('sda_prefix[]'),
                get_form_list('sda_name[]'),
                get_form_list('sda_designation[]')
            )
        elif base_name == 'guest_trainers':
            return combine_person_list(
                get_form_list('guest_prefix[]'),
                get_form_list('guest_name[]'),
                get_form_list('guest_designation[]')
            )
        elif base_name == 'chief_guests':
            return combine_person_list(
                get_form_list('chief_prefix[]'),
                get_form_list('chief_name[]'),
                get_form_list('chief_designation[]')
            )
        elif base_name == 'guidance_person':
            return combine_person_list(
                get_form_list('guidance_prefix[]'),
                get_form_list('guidance_name[]'),
                get_form_list('guidance_designation[]')
            )
        return ''
    
    # Get person data using flexible approach
    Sda_people = get_person_data('rrecl_people')
    guest_trainers = get_person_data('guest_trainers')
    chief_guests = get_person_data('chief_guests')
    guidance_person = get_person_data('guidance_person')

    # Text replacements
    text_replacements = {
        '{{EVENT_DATE}}': format_date(request.form.get('event_date', '')),
        '{{Submitted_to}}': request.form.get('submitted_to', ''),
        '{{Submitted_by}}': request.form.get('submitted_by', ''),
        '{{ADDRESS}}': format_address(
            request.form.get('address_line1', ''),
            request.form.get('address_line2', ''),
            request.form.get('address_line3', '')
        ),
        '{{ADDRESS_ONELINE}}': format_address_oneline(
            request.form.get('address_line1', ''),
            request.form.get('address_line2', ''),
            request.form.get('address_line3', '')
        ),
        '{{RRECL_PEOPLE}}': Sda_people,
        '{{WORKSHOP_TYPE}}': request.form.get('workshop_type', ''),
        '{{GUEST_TRAINERS}}': guest_trainers,
        '{{ORGANIZER}}': request.form.get('organizer', ''),
        '{{VENUE}}': request.form.get('venue', ''),
        '{{DATETIME}}': format_date(request.form.get('date', '')),
        '{{CELL_NAME}}': request.form.get('cell_name', ''),
        '{{CHIEF_GUESTS}}': chief_guests,
        '{{GUIDANCE_PERSON}}': guidance_person,
        
        # Additional fields for different training types
        '{{START_DATE}}': format_date(request.form.get('start_date', '')),
        '{{END_DATE}}': format_date(request.form.get('end_date', '')),
        '{{DURATION}}': request.form.get('duration', ''),
        '{{PARTICIPANT_COUNT}}': request.form.get('participant_count', ''),
        '{{TRAINING_TYPE}}': request.form.get('training_type', ''),
        '{{CONTACT_PERSON}}': request.form.get('contact_person', ''),
        '{{PHONE}}': request.form.get('phone', ''),
        '{{EMAIL}}': request.form.get('email', ''),
    }
    
    return text_replacements


def process_gallery_images_api(request):
    """Process gallery images and captions from API request."""
    from .document_utils import save_uploaded_file_to_temp
    
    gallery_images = []
    gallery_captions = []
    
    # Process up to 10 gallery images
    for i in range(1, 11):
        image_file = request.files.get(f'gallery_image_{i}')
        if image_file:
            image_path = save_uploaded_file_to_temp(image_file)
            if image_path:
                gallery_images.append(image_path)
                gallery_captions.append(request.form.get(f'gallery_caption_{i}', ''))
    
    return gallery_images, gallery_captions
