from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from myprofile.models import StaffMember, Associate
from phdstuds.models import PhdThesis
from associates.models import Attendance, Card
from curricula.models import Course, StudyProgram, Department
from .serializers import StaffSerializer, StaffFullSerializer, AssociateSeralizer, CourseSerializer, CourseTitleSerializer, PhDThesisSerializer, ProjectSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from datetime import datetime
from .api_orderings import sort_by_title
from projects.models import Project
# Create your views here.


class StaffMemberApiView(APIView):

    permission_classes = []
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        department_pk = request.GET.get('department_pk')
        if department_pk:
            department = get_object_or_404(Department, pk = department_pk)
            staff_members = sort_by_title( StaffMember.objects.filter(internal_department = department) )
            serializer = StaffSerializer(staff_members, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


        program_pk = request.GET.get('program_pk')
        if program_pk:
            program = get_object_or_404(StudyProgram, pk = program_pk)
            staff_members = sort_by_title( StaffMember.objects.filter(
                course__program = program
            ).distinct() )
            serializer = StaffSerializer(staff_members, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        
class StaffMemberFullApiView(APIView):

    permission_classes = []
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        pk = request.GET.get('pk')
        staff = get_object_or_404(StaffMember, pk=pk)
        serializer = StaffFullSerializer(staff)
        return Response(serializer.data, status=status.HTTP_200_OK)

class StaffMemberFullListApiView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):

        department_pk = request.GET.get('department_pk')
        if department_pk:
            department = get_object_or_404(Department, pk = department_pk)
            staff_members = sort_by_title( StaffMember.objects.filter(internal_department = department) )
            serializer = StaffFullSerializer(staff_members, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


        program_pk = request.GET.get('program_pk')
        if program_pk:
            program = get_object_or_404(StudyProgram, pk = program_pk)
            staff_members = sort_by_title( StaffMember.objects.filter(
                course__program = program
            ).distinct() )
            serializer = StaffFullSerializer(staff_members, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        

class AssociateApiView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        card_no = request.GET.get('card_no')
        associate = Associate.objects.filter(card_no = card_no)
        serializer = AssociateSeralizer(associate, many = True)
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)

class CourseApiView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        id = request.GET.get('id')
        course = Course.objects.filter(pk = id)
        serializer = CourseSerializer(course, many=True)
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)

class CourseListApiView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        
        program_id = request.GET.get('id')
        if not program_id:
            return Response({"error" : "must provide program id."},
                            status = status.HTTP_400_BAD_REQUEST)
        try:
            program_id = int(program_id)
        except ValueError:
            return Response({"error" : "must provide integer id."},
                            status = status.HTTP_400_BAD_REQUEST)
        program = get_object_or_404(StudyProgram, id = program_id)
        courses = Course.objects.filter(program=program).order_by('semester')
        serializer = CourseTitleSerializer(courses, many=True)

        return Response(serializer.data)

class CourseFullListApiView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def get(self, request):
        
        program_id = request.GET.get('id')
        if not program_id:
            return Response({"error" : "must provide program id."},
                            status = status.HTTP_400_BAD_REQUEST)
        try:
            program_id = int(program_id)
        except ValueError:
            return Response({"error" : "must provide integer id."},
                            status = status.HTTP_400_BAD_REQUEST)
        program = get_object_or_404(StudyProgram, id = program_id)
        courses = Course.objects.filter(program=program).order_by('semester')
        serializer = CourseSerializer(courses, many=True)

        return Response(serializer.data)


class PhDThesesFullListApiView(APIView):
    permission_classes = [permissions.IsAdminUser]
    # permission_classes = []
    # authentication_classes = []
    
    def get(self, request):
        
        program_id = request.GET.get('id')
        if not program_id:
            return Response({"error" : "must provide program id."},
                            status = status.HTTP_400_BAD_REQUEST)
        try:
            program_id = int(program_id)
        except ValueError:
            return Response({"error" : "must provide integer id."},
                            status = status.HTTP_400_BAD_REQUEST)

        program = get_object_or_404(StudyProgram, id = program_id)
        theses = PhdThesis.objects.filter(candidate__program=program).order_by('-inscription_date')
        serializer = PhDThesisSerializer(theses, many=True)

        return Response(serializer.data)
        

class AttendanceApiView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        card_no = request.data.get('card_no')
        now = datetime.now()
        now_date = now.date()
    
        associates = Associate.objects.filter(card_no = card_no)
        
        if associates.count() > 0:
            associate = associates[0]
            existing_attendances = Attendance.objects.filter(date_time__contains = now_date, associate = associate)
            
            if existing_attendances.count() % 2 == 1:
                check_type = Attendance.CHECK_OUT
            else:
                check_type = Attendance.CHECK_IN
            
            attendance = Attendance(
                card_no = card_no,
                date_time = now,
                check_type = check_type,
                associate = associate
            )
            attendance.save()

            serializer = AssociateSeralizer(associates, many = True)
            data = serializer.data
            data[0]['count'] = existing_attendances.count()
            data[0]['check_type'] = check_type
                    

            return Response(data, status=status.HTTP_200_OK)
        
        else:
            serializer = AssociateSeralizer([], many = True)
            card = Card(card_no = card_no)
            card.save()
            return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    # permission_classes = []
    # authentication_classes = []
    
    def get(self, request):
    
        department_id = request.GET.get('id')

        if not department_id:
            return Response({"error" : "must provide department id."},
                            status = status.HTTP_400_BAD_REQUEST)
        try:
            department_id = int(department_id)
        except ValueError:
            return Response({"error" : "must provide integer id."},
                            status = status.HTTP_400_BAD_REQUEST)

        department = get_object_or_404(Department, id = department_id)
        projects = Project.objects.filter(coordinator__internal_department = department)
        serializer = ProjectSerializer(projects, many=True)

        return Response(serializer.data)
