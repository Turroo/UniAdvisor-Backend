from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from math import radians, cos, sin, asin, sqrt

from database.database import get_db
from models.faculty import Faculty
from models.course import Course
from models.teacher import Teacher
from auth.auth import get_current_user
from models.user import User

router = APIRouter()

# ============================================
# UTILITY FUNCTION: Haversine Distance
# ============================================

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    Returns distance in meters.
    """
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    r = 6371000  # Radius of earth in meters
    return c * r

def calculate_walking_time(distance_meters: float) -> int:
    """
    Calculate walking time in minutes.
    Assumes average walking speed of 5 km/h (83.33 m/min)
    """
    walking_speed_m_per_min = 83.33
    return int(distance_meters / walking_speed_m_per_min) + 1

# ============================================
# ENDPOINT 1: Get All Faculties with Locations
# ============================================

@router.get("/faculties/map")
def get_faculties_for_map(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all faculties with location data for displaying on campus map.
    """
    faculties = db.query(Faculty).filter(
        Faculty.latitude.isnot(None),
        Faculty.longitude.isnot(None)
    ).all()
    
    return [
        {
            "id": f.id,
            "name": f.name,
            "latitude": f.latitude,
            "longitude": f.longitude,
            "building_name": f.building_name
        }
        for f in faculties
    ]

# ============================================
# ENDPOINT 2: Get Faculty Location Details
# ============================================

@router.get("/faculties/{faculty_id}/location")
def get_faculty_location(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed location information for a specific faculty.
    """
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    
    if not faculty.latitude or not faculty.longitude:
        raise HTTPException(status_code=404, detail="Faculty location not available")
    
    return {
        "id": faculty.id,
        "name": faculty.name,
        "latitude": faculty.latitude,
        "longitude": faculty.longitude,
        "address": faculty.address,
        "building_name": faculty.building_name
    }

# ============================================
# ENDPOINT 3: Get All Courses with Locations
# ============================================

@router.get("/courses/map")
def get_courses_for_map(
    faculty_id: Optional[int] = Query(None, description="Filter by faculty ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all courses with location data for displaying on campus map.
    """
    query = db.query(Course).filter(
        Course.latitude.isnot(None),
        Course.longitude.isnot(None)
    )
    
    if faculty_id:
        query = query.filter(Course.faculty_id == faculty_id)
    
    courses = query.all()
    
    return [
        {
            "id": c.id,
            "name": c.name,
            "faculty_id": c.faculty_id,
            "room_number": c.room_number,
            "building_name": c.building_name,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "floor": c.floor
        }
        for c in courses
    ]

# ============================================
# ENDPOINT 4: Get Course Location Details
# ============================================

@router.get("/courses/{course_id}/location")
def get_course_location(
    course_id: int,
    user_latitude: Optional[float] = Query(None),
    user_longitude: Optional[float] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed location information for a specific course.
    If user location is provided, also returns distance and walking time.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if not course.latitude or not course.longitude:
        raise HTTPException(status_code=404, detail="Course location not available")
    
    # Get teacher name
    teacher_name = None
    if course.teacher_id:
        teacher = db.query(Teacher).filter(Teacher.id == course.teacher_id).first()
        if teacher:
            teacher_name = teacher.name
    
    response = {
        "id": course.id,
        "name": course.name,
        "room_number": course.room_number,
        "building_name": course.building_name,
        "latitude": course.latitude,
        "longitude": course.longitude,
        "floor": course.floor,
        "teacher_name": teacher_name
    }
    
    # Calculate distance if user location is provided
    if user_latitude and user_longitude:
        distance_meters = calculate_distance(
            user_latitude, user_longitude,
            course.latitude, course.longitude
        )
        walking_time_minutes = calculate_walking_time(distance_meters)
        
        response["distance_meters"] = round(distance_meters, 1)
        response["walking_time_minutes"] = walking_time_minutes
    
    return response

# ============================================
# ENDPOINT 5: Get Nearby Courses
# ============================================

@router.get("/courses/nearby")
def get_nearby_courses(
    latitude: float = Query(..., description="User's current latitude"),
    longitude: float = Query(..., description="User's current longitude"),
    radius_meters: float = Query(1000, description="Search radius in meters"),
    faculty_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all courses within a specified radius of the user's location.
    """
    query = db.query(Course).filter(
        Course.latitude.isnot(None),
        Course.longitude.isnot(None)
    )
    
    if faculty_id:
        query = query.filter(Course.faculty_id == faculty_id)
    
    courses = query.all()
    
    courses_with_distance = []
    for course in courses:
        distance = calculate_distance(
            latitude, longitude,
            course.latitude, course.longitude
        )
        
        if distance <= radius_meters:
            walking_time = calculate_walking_time(distance)
            
            teacher_name = None
            if course.teacher_id:
                teacher = db.query(Teacher).filter(Teacher.id == course.teacher_id).first()
                if teacher:
                    teacher_name = teacher.name
            
            courses_with_distance.append({
                "id": course.id,
                "name": course.name,
                "faculty_id": course.faculty_id,
                "room_number": course.room_number,
                "building_name": course.building_name,
                "latitude": course.latitude,
                "longitude": course.longitude,
                "floor": course.floor,
                "teacher_name": teacher_name,
                "distance_meters": round(distance, 1),
                "walking_time_minutes": walking_time
            })
    
    courses_with_distance.sort(key=lambda x: x["distance_meters"])
    
    return {
        "user_location": {"latitude": latitude, "longitude": longitude},
        "radius_meters": radius_meters,
        "total_courses_found": len(courses_with_distance),
        "courses": courses_with_distance
    }

# ============================================
# ENDPOINT 6: Get Navigation Info
# ============================================

@router.get("/navigate/{course_id}")
def get_navigation_info(
    course_id: int,
    user_latitude: float = Query(...),
    user_longitude: float = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get navigation information for a specific course.
    Returns Google Maps URL and walking directions info.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if not course.latitude or not course.longitude:
        raise HTTPException(status_code=404, detail="Course location not available")
    
    distance = calculate_distance(
        user_latitude, user_longitude,
        course.latitude, course.longitude
    )
    walking_time = calculate_walking_time(distance)
    
    google_maps_url = (
        f"https://www.google.com/maps/dir/?api=1"
        f"&origin={user_latitude},{user_longitude}"
        f"&destination={course.latitude},{course.longitude}"
        f"&travelmode=walking"
    )
    
    waze_url = f"https://waze.com/ul?ll={course.latitude},{course.longitude}&navigate=yes"
    
    return {
        "course_id": course.id,
        "course_name": course.name,
        "destination": {
            "room_number": course.room_number,
            "building_name": course.building_name,
            "latitude": course.latitude,
            "longitude": course.longitude,
            "floor": course.floor
        },
        "distance_meters": round(distance, 1),
        "walking_time_minutes": walking_time,
        "google_maps_url": google_maps_url,
        "waze_url": waze_url
    }