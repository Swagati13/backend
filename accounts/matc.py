from django.http import JsonResponse
from .models import Person
from .serializers import PersonSerialiers 
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

def calculate_match_score(record, missing_person):
    match_score = 0

    if record.name and missing_person.name and record.name.lower() == missing_person.name.lower():
        match_score += 1
    if record.age and missing_person.age and record.age == missing_person.age:
        match_score += 1
    if record.blood_group and missing_person.blood_group and record.blood_group == missing_person.blood_group:
        match_score += 1
    if record.complexion and missing_person.complexion and record.complexion.lower() == missing_person.complexion.lower():
        match_score += 1
    if record.hair_color and missing_person.hair_color and record.hair_color.lower() == missing_person.hair_color.lower():
        match_score += 1
    if record.eye_color and missing_person.eye_color and record.eye_color.lower() == missing_person.eye_color.lower():
        match_score += 1

    total_fields = len(Person._meta.fields)
    match_percent = (match_score / (total_fields - 2)) * 100

    return match_percent


@api_view(['GET'])
def match_with_unidentified_person(request, missing_person_id):
    try:
        missing_person = Person.objects.get(id=missing_person_id, person_type='missing')
    except Person.DoesNotExist:
        return Response({'error': 'Missing person not found.'}, status=status.HTTP_404_NOT_FOUND)

    unidentified_people = Person.objects.filter(person_type='unidentified_person')
    matched_records = []

    for record in unidentified_people:
        if calculate_match_score(record, missing_person) >= 80:
            matched_records.append(record)

    serialized_missing = PersonSerialiers(missing_person).data
    serialized_matches = PersonSerialiers(matched_records, many=True).data

    return Response({
        'missing_person': serialized_missing,
        'matched_unidentified_people': serialized_matches,
        'match_count': len(matched_records)
    })


@api_view(['GET'])
def match_with_unidentified_body(request, missing_person_id):
    try:
        missing_person = Person.objects.get(id=missing_person_id, person_type='missing')
    except Person.DoesNotExist:
        return Response({'error': 'Missing person not found.'}, status=status.HTTP_404_NOT_FOUND)

    unidentified_bodies = Person.objects.filter(person_type='unidentified_body')
    matched_records = []

    for record in unidentified_bodies:
        if calculate_match_score(record, missing_person) >= 80:
            matched_records.append(record)

    serialized_missing = PersonSerialiers(missing_person).data
    serialized_matches = PersonSerialiers(matched_records, many=True).data

    return Response({
        'missing_person': serialized_missing,
        'matched_unidentified_bodies': serialized_matches,
        'match_count': len(matched_records)
    })