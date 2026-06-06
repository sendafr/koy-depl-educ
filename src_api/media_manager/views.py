from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils.text import slugify
from .models import MediaUpload, MediaFile, MediaCategory, MediaTag, MediaDownload
from .serializers import (
    MediaUploadSerializer,
    MediaFileSerializer,
    MediaFileCreateUpdateSerializer,
    MediaCategorySerializer,
    MediaTagSerializer,
    MediaDownloadSerializer
)
#Create a Public Media View in Django
        
from django.http import FileResponse, HttpResponse
from django.views.decorators.http import condition
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
import mimetypes
import re

MEDIA_TYPE_ALIASES = {
    'videos': 'video',
    'video': 'video',
    'images': 'image',
    'image': 'image',
    'docs': 'document',
    'doc': 'document',
    'document': 'document',
    'documentary': 'documentary',
    'maps': 'map',
    'map': 'map',
    'studycases': 'studycase',
    'studycase': 'studycase',
    'study_case': 'studycase',
}


def normalize_media_type(value):
    if not value:
        return value
    return MEDIA_TYPE_ALIASES.get(value.strip().lower(), value.strip().lower())


@csrf_exempt  # Allow unauthenticated access
def serve_media_file(request, file_path):
    """
    Serve media files publicly without authentication.
    Supports range requests for video seeking.
    """
    # Security: Prevent directory traversal attacks
    file_path = file_path.lstrip('/')
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    
    # Ensure the file is within MEDIA_ROOT
    if not os.path.abspath(full_path).startswith(os.path.abspath(settings.MEDIA_ROOT)):
        return HttpResponse('Access Denied', status=403)
    
    # Check if file exists
    if not os.path.exists(full_path):
        return HttpResponse('File Not Found', status=404)
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(full_path)
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    file_size = os.path.getsize(full_path)
    
    # Handle Range requests (for video seeking)
    range_header = request.META.get('HTTP_RANGE', '')
    
    if range_header:
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            
            # Validate range
            if start >= file_size or end >= file_size:
                return HttpResponse('Range Not Satisfiable', status=416)
            
            with open(full_path, 'rb') as f:
                f.seek(start)
                response = HttpResponse(f.read(end - start + 1), content_type=mime_type, status=206)
            
            response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response['Content-Length'] = str(end - start + 1)
        else:
            response = FileResponse(open(full_path, 'rb'), content_type=mime_type)
            response['Content-Length'] = str(file_size)
    else:
        response = FileResponse(open(full_path, 'rb'), content_type=mime_type)
        response['Content-Length'] = str(file_size)
    
    # Add required headers for video streaming
    response['Accept-Ranges'] = 'bytes'
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Range'
    response['Access-Control-Expose-Headers'] = 'Content-Range, Content-Length, Accept-Ranges'
    response['Cache-Control'] = 'public, max-age=86400'
    
    return response

 

# ─── MediaUpload CRUD ──────────────────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def media_upload_list_create(request):
    if request.method == 'GET':
        media_uploads = MediaUpload.objects.all()
        serializer = MediaUploadSerializer(media_uploads, many=True, context={'request': request})
        return Response({
            'message': 'Media uploads retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        permission_classes = [IsAuthenticated]
        serializer = MediaUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Media uploaded successfully.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def media_upload_detail(request, pk):
    try:
        media_upload = MediaUpload.objects.get(pk=pk)
    except MediaUpload.DoesNotExist:
        return Response(
            {'error': 'Media upload not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = MediaUploadSerializer(media_upload, context={'request': request})
        return Response({
            'message': 'Media upload retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        if media_upload.user != request.user:
            return Response(
                {'error': 'You do not have permission to edit this media.'},
                status=status.HTTP_403_FORBIDDEN
            )
        partial = request.method == 'PATCH'
        serializer = MediaUploadSerializer(
            media_upload,
            data=request.data,
            partial=partial,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Media upload updated successfully.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if media_upload.user != request.user:
            return Response(
                {'error': 'You do not have permission to delete this media.'},
                status=status.HTTP_403_FORBIDDEN
            )
        media_upload.delete()
        return Response(
            {'message': 'Media upload deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


# ─── MediaFile CRUD ───────────────────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def media_file_list_create(request):
    if request.method == 'GET':
        media_type = request.query_params.get('media_type')
        status_filter = request.query_params.get('status')
        is_featured = request.query_params.get('is_featured')

        media_files = MediaFile.objects.all()

        if media_type:
            normalized_media_type = normalize_media_type(media_type)
            media_files = media_files.filter(media_type=normalized_media_type)
        if status_filter:
            media_files = media_files.filter(status=status_filter)
        if is_featured:
            media_files = media_files.filter(is_featured=is_featured.lower() == 'true')

        serializer = MediaFileSerializer(media_files, many=True, context={'request': request})
        return Response({
            'message': 'Media files retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        permission_classes = [IsAuthenticated]
        serializer = MediaFileCreateUpdateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            media_file = serializer.save()
            # Generate slug if not provided
            if not media_file.slug:
                media_file.slug = slugify(media_file.title)
                media_file.save()
            return Response({
                'message': 'Media file created successfully.',
                'data': MediaFileSerializer(media_file, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def media_file_detail(request, pk):
    try:
        media_file = MediaFile.objects.get(pk=pk)
    except MediaFile.DoesNotExist:
        return Response(
            {'error': 'Media file not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = MediaFileSerializer(media_file, context={'request': request})
        return Response({
            'message': 'Media file retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        if media_file.user != request.user:
            return Response(
                {'error': 'You do not have permission to edit this media.'},
                status=status.HTTP_403_FORBIDDEN
            )
        partial = request.method == 'PATCH'
        serializer = MediaFileCreateUpdateSerializer(
            media_file,
            data=request.data,
            partial=partial,
            context={'request': request}
        )
        if serializer.is_valid():
            media_file = serializer.save()
            return Response({
                'message': 'Media file updated successfully.',
                'data': MediaFileSerializer(media_file, context={'request': request}).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if media_file.user != request.user:
            return Response(
                {'error': 'You do not have permission to delete this media.'},
                status=status.HTTP_403_FORBIDDEN
            )
        media_file.delete()
        return Response(
            {'message': 'Media file deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


# ─── MediaCategory CRUD ───────────────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def media_category_list_create(request):
    if request.method == 'GET':
        categories = MediaCategory.objects.all()
        serializer = MediaCategorySerializer(categories, many=True)
        return Response({
            'message': 'Categories retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        permission_classes = [IsAuthenticated]
        serializer = MediaCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Category created successfully.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def media_category_detail(request, pk):
    try:
        category = MediaCategory.objects.get(pk=pk)
    except MediaCategory.DoesNotExist:
        return Response(
            {'error': 'Category not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = MediaCategorySerializer(category)
        return Response({
            'message': 'Category retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = MediaCategorySerializer(category, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Category updated successfully.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        category.delete()
        return Response(
            {'message': 'Category deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


# ─── MediaTag CRUD ────────────────────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def media_tag_list_create(request):
    if request.method == 'GET':
        tags = MediaTag.objects.all()
        serializer = MediaTagSerializer(tags, many=True)
        return Response({
            'message': 'Tags retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        permission_classes = [IsAuthenticated]
        serializer = MediaTagSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Tag created successfully.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def media_tag_detail(request, pk):
    try:
        tag = MediaTag.objects.get(pk=pk)
    except MediaTag.DoesNotExist:
        return Response(
            {'error': 'Tag not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = MediaTagSerializer(tag)
        return Response({
            'message': 'Tag retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = MediaTagSerializer(tag, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Tag updated successfully.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        tag.delete()
        return Response(
            {'message': 'Tag deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


# ─── MediaDownload CRUD ───────────────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def media_download_list_create(request):
    if request.method == 'GET':
        downloads = MediaDownload.objects.filter(user=request.user)
        serializer = MediaDownloadSerializer(downloads, many=True)
        return Response({
            'message': 'Downloads retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = MediaDownloadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Download recorded successfully.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def media_download_detail(request, pk):
    try:
        download = MediaDownload.objects.get(pk=pk)
    except MediaDownload.DoesNotExist:
        return Response(
            {'error': 'Download record not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if download.user != request.user:
        return Response(
            {'error': 'You do not have permission to access this download.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'GET':
        serializer = MediaDownloadSerializer(download)
        return Response({
            'message': 'Download retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        download.delete()
        return Response(
            {'message': 'Download record deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )