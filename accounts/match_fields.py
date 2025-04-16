from django.http import JsonResponse
from .models import Person
from .serializers import PersonSerialiers 
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from difflib import SequenceMatcher

def calculate_similarity(a, b):
    """Return a similarity ratio between 0 and 100 for strings."""
    return int(SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio() * 100)

def calculate_match_score(record, missing_person, numeric_tolerance=2):
    field_match_scores = {}
    total_score = 0
    total_fields = 0

    for field in Person._meta.fields:
        field_name = field.name

        if field.auto_created or field.primary_key or field_name == "person_type":
            continue

        record_value = getattr(record, field_name, None)
        missing_value = getattr(missing_person, field_name, None)

        if record_value is None or missing_value is None:
            field_match_scores[field_name] = None
            continue

        total_fields += 1

        if isinstance(record_value, str) and isinstance(missing_value, str):
            match_score = calculate_similarity(record_value, missing_value)

        elif isinstance(record_value, (int, float)) and isinstance(missing_value, (int, float)):
            diff = abs(record_value - missing_value)
            if diff == 0:
                match_score = 100
            elif diff <= numeric_tolerance:
                match_score = int(100 - (diff / numeric_tolerance) * 100)
            else:
                match_score = 0
        else:
            match_score = 100 if record_value == missing_value else 0

        field_match_scores[field_name] = match_score
        total_score += match_score

    overall_percentage = (total_score / total_fields) if total_fields > 0 else 0

    return {
        'field_wise_percentages': field_match_scores,
        'overall_percentage': overall_percentage
    }

def match_with_unidentified_person(request, missing_person_id):
    try:
        missing_person = Person.objects.get(id=missing_person_id, person_type='misssing')
    except Person.DoesNotExist:
        return JsonResponse({'error': 'Missing person not found'}, status=404)

    candidates = Person.objects.filter(
        person_type='unidentified_Person'
    ).exclude(case_status='resolved')

    matches = []
    for candidate in candidates:
        match_result = calculate_match_score(candidate, missing_person)
        matches.append({
            'id': candidate.id,
            'name': candidate.name,
            'match': match_result
        })

    return JsonResponse({'matches': matches})

def match_with_unidentified_body(request, missing_person_id):
    try:
        missing_person = Person.objects.get(id=missing_person_id, person_type='misssing')
    except Person.DoesNotExist:
        return JsonResponse({'error': 'Missing person not found'}, status=404)

    candidates = Person.objects.filter(
        person_type='unidentified_body'
    ).exclude(case_status='resolved')

    matches = []
    for candidate in candidates:
        match_result = calculate_match_score(candidate, missing_person)
        matches.append({
            'id': candidate.id,
            'name': candidate.name,
            'match': match_result
        })

    return JsonResponse({'matches': matches})