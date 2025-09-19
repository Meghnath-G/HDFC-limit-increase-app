"""
Django REST Framework views for Analytics and Reporting.

Provides comprehensive analytics, reporting, and business
intelligence with proper aggregation and visualization support.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import logging
from datetime import timedelta, datetime
import json

from .models import AnalyticsEvent, DashboardMetrics, PerformanceLog
from .serializers import (
    AnalyticsEventSerializer,
    AnalyticsQuerySerializer,
    DashboardMetricsSerializer,
    PerformanceLogSerializer,
    AnalyticsReportSerializer,
    MetricsTrendSerializer,
    UserBehaviorAnalyticsSerializer
)
from .services import AnalyticsService, ReportingService
from apps.customers.models import Customer
from apps.requests.models import LimitRequest
from core.permissions import IsCustomerService, IsAnalyticsViewer
from core.mixins import SecurityMixin, AuditMixin
from core.pagination import StandardResultsSetPagination
from core.utils import get_client_ip

logger = logging.getLogger(__name__)


class AnalyticsEventViewSet(SecurityMixin, AuditMixin, viewsets.ModelViewSet):
    """
    ViewSet for analytics event tracking.
    
    Handles event logging, querying, and basic analytics
    with proper data validation and security controls.
    """
    
    queryset = AnalyticsEvent.objects.select_related('customer')
    serializer_class = AnalyticsEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['event_category', 'event_type', 'event_name']
    search_fields = ['event_name', 'page_path']
    ordering_fields = ['created_at', 'value']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name__in=['customer_service', 'analytics_viewer']).exists():
            # Staff and analytics viewers can see all events
            return self.queryset
        else:
            # Regular users can only see their own events
            try:
                customer = Customer.objects.get(firebase_uid=user.username)
                return self.queryset.filter(customer=customer)
            except Customer.DoesNotExist:
                return AnalyticsEvent.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Create analytics event with automatic customer association."""
        # Get customer from Firebase UID
        try:
            customer = Customer.objects.get(firebase_uid=request.user.username)
        except Customer.DoesNotExist:
            # For analytics events, we allow anonymous tracking
            customer = None
        
        # Add customer to request data if found
        data = request.data.copy()
        if customer:
            data['customer'] = customer.id
        
        # Add request metadata
        data['ip_address'] = get_client_ip(request)
        data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Create event
            event = serializer.save(customer=customer)
            
            # Process event asynchronously for real-time analytics
            AnalyticsService.process_event_async(event)
            
            return Response({
                'status': 'success',
                'message': 'Event tracked successfully',
                'data': {'event_id': event.id}
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Analytics event creation failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Event tracking failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAnalyticsViewer])
    def query(self, request):
        """Execute analytics query with aggregation and filtering."""
        serializer = AnalyticsQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Execute query using analytics service
            query_result = AnalyticsService.execute_query(
                start_date=serializer.validated_data['start_date'],
                end_date=serializer.validated_data['end_date'],
                event_category=serializer.validated_data.get('event_category'),
                event_type=serializer.validated_data.get('event_type'),
                event_name=serializer.validated_data.get('event_name'),
                group_by=serializer.validated_data.get('group_by', ['day']),
                metrics=serializer.validated_data.get('metrics', ['count']),
                include_comparison=serializer.validated_data.get('include_comparison', False),
                comparison_period_days=serializer.validated_data.get('comparison_period_days', 7)
            )
            
            # Log query execution
            self.log_audit_event(
                action='analytics_query_executed',
                resource_type='AnalyticsQuery',
                resource_id=None,
                user=request.user,
                details={
                    'query_parameters': serializer.validated_data,
                    'result_count': len(query_result.get('data', [])),
                    'analyst_user': request.user.username
                }
            )
            
            return Response({
                'status': 'success',
                'data': query_result
            })
            
        except Exception as e:
            logger.error(f"Analytics query failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Analytics query failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardMetricsViewSet(SecurityMixin, AuditMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for dashboard metrics.
    
    Provides real-time business metrics and KPIs
    for executive dashboards and monitoring.
    """
    
    queryset = DashboardMetrics.objects.all()
    serializer_class = DashboardMetricsSerializer
    permission_classes = [permissions.IsAuthenticated, IsAnalyticsViewer]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['metric_date']
    ordering_fields = ['metric_date', 'total_customers', 'total_limit_requests']
    ordering = ['-metric_date']
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current day metrics with real-time data."""
        try:
            # Check cache first
            cache_key = 'dashboard_metrics_current'
            cached_metrics = cache.get(cache_key)
            
            if cached_metrics:
                return Response({
                    'status': 'success',
                    'data': cached_metrics,
                    'cached': True
                })
            
            # Generate current metrics
            current_metrics = AnalyticsService.generate_current_metrics()
            
            # Cache for 5 minutes
            cache.set(cache_key, current_metrics, 300)
            
            return Response({
                'status': 'success',
                'data': current_metrics,
                'cached': False
            })
            
        except Exception as e:
            logger.error(f"Current metrics retrieval failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to retrieve current metrics',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get metrics summary with trends and comparisons."""
        try:
            # Get query parameters
            days = int(request.query_params.get('days', 30))
            include_trends = request.query_params.get('include_trends', 'true').lower() == 'true'
            
            # Generate summary
            summary_data = AnalyticsService.generate_metrics_summary(
                days=days,
                include_trends=include_trends
            )
            
            return Response({
                'status': 'success',
                'data': summary_data
            })
            
        except Exception as e:
            logger.error(f"Metrics summary retrieval failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to retrieve metrics summary',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def kpis(self, request):
        """Get key performance indicators with targets and alerts."""
        try:
            # Generate KPI data
            kpi_data = AnalyticsService.generate_kpi_dashboard()
            
            return Response({
                'status': 'success',
                'data': kpi_data
            })
            
        except Exception as e:
            logger.error(f"KPI data retrieval failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to retrieve KPI data',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PerformanceLogViewSet(SecurityMixin, AuditMixin, viewsets.ModelViewSet):
    """
    ViewSet for performance monitoring.
    
    Handles system performance tracking, monitoring,
    and optimization recommendations.
    """
    
    queryset = PerformanceLog.objects.all()
    serializer_class = PerformanceLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomerService]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['operation_type', 'error_occurred']
    ordering_fields = ['created_at', 'execution_time_seconds', 'memory_usage_mb']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def performance_summary(self, request):
        """Get performance summary with alerts and recommendations."""
        try:
            # Get query parameters
            hours = int(request.query_params.get('hours', 24))
            operation_type = request.query_params.get('operation_type')
            
            # Generate performance summary
            summary = AnalyticsService.generate_performance_summary(
                hours=hours,
                operation_type=operation_type
            )
            
            return Response({
                'status': 'success',
                'data': summary
            })
            
        except Exception as e:
            logger.error(f"Performance summary retrieval failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to retrieve performance summary',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """Get performance alerts and recommendations."""
        try:
            # Generate performance alerts
            alerts = AnalyticsService.generate_performance_alerts()
            
            return Response({
                'status': 'success',
                'data': alerts
            })
            
        except Exception as e:
            logger.error(f"Performance alerts retrieval failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to retrieve performance alerts',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReportingViewSet(SecurityMixin, AuditMixin, viewsets.ViewSet):
    """
    ViewSet for comprehensive reporting.
    
    Provides business intelligence reports, data exports,
    and visualization support for various stakeholders.
    """
    
    permission_classes = [permissions.IsAuthenticated, IsAnalyticsViewer]
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Generate comprehensive business report."""
        serializer = AnalyticsReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Generate report using reporting service
            report_data = ReportingService.generate_report(
                report_type=serializer.validated_data['report_type'],
                start_date=serializer.validated_data['start_date'],
                end_date=serializer.validated_data['end_date'],
                customer_segment=serializer.validated_data.get('customer_segment'),
                card_type=serializer.validated_data.get('card_type'),
                group_by_period=serializer.validated_data.get('group_by_period', 'day'),
                include_comparison=serializer.validated_data.get('include_comparison', False),
                format_type=serializer.validated_data.get('format_type', 'json')
            )
            
            # Log report generation
            self.log_audit_event(
                action='report_generated',
                resource_type='AnalyticsReport',
                resource_id=None,
                user=request.user,
                details={
                    'report_type': serializer.validated_data['report_type'],
                    'date_range': f"{serializer.validated_data['start_date']} to {serializer.validated_data['end_date']}",
                    'format_type': serializer.validated_data.get('format_type', 'json'),
                    'analyst_user': request.user.username
                }
            )
            
            return Response({
                'status': 'success',
                'message': 'Report generated successfully',
                'data': report_data
            })
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Report generation failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def metrics_trend(self, request):
        """Analyze metrics trends with forecasting."""
        serializer = MetricsTrendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Analyze trends using analytics service
            trend_analysis = AnalyticsService.analyze_metric_trend(
                metric_name=serializer.validated_data['metric_name'],
                time_period=serializer.validated_data['time_period'],
                include_forecast=serializer.validated_data.get('include_forecast', False),
                detect_anomalies=serializer.validated_data.get('detect_anomalies', False),
                include_seasonality=serializer.validated_data.get('include_seasonality', False)
            )
            
            return Response({
                'status': 'success',
                'data': trend_analysis
            })
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Trend analysis failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def user_behavior(self, request):
        """Analyze user behavior patterns and journeys."""
        serializer = UserBehaviorAnalyticsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Analyze user behavior using analytics service
            behavior_analysis = AnalyticsService.analyze_user_behavior(
                analysis_type=serializer.validated_data['analysis_type'],
                start_date=serializer.validated_data['start_date'],
                end_date=serializer.validated_data['end_date'],
                customer_segment=serializer.validated_data.get('customer_segment'),
                app_version=serializer.validated_data.get('app_version'),
                device_type=serializer.validated_data.get('device_type'),
                funnel_steps=serializer.validated_data.get('funnel_steps'),
                cohort_period=serializer.validated_data.get('cohort_period', 'week')
            )
            
            return Response({
                'status': 'success',
                'data': behavior_analysis
            })
            
        except Exception as e:
            logger.error(f"User behavior analysis failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'User behavior analysis failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def executive_summary(self, request):
        """Generate executive summary dashboard."""
        try:
            # Get query parameters
            period = request.query_params.get('period', '30d')
            include_forecasts = request.query_params.get('include_forecasts', 'false').lower() == 'true'
            
            # Generate executive summary
            executive_summary = ReportingService.generate_executive_summary(
                period=period,
                include_forecasts=include_forecasts
            )
            
            return Response({
                'status': 'success',
                'data': executive_summary
            })
            
        except Exception as e:
            logger.error(f"Executive summary generation failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Executive summary generation failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def data_export(self, request):
        """Export analytics data in various formats."""
        try:
            # Get query parameters
            export_type = request.query_params.get('export_type', 'customers')
            format_type = request.query_params.get('format', 'csv')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            # Generate data export
            export_data = ReportingService.export_data(
                export_type=export_type,
                format_type=format_type,
                date_from=date_from,
                date_to=date_to,
                user=request.user
            )
            
            # Log data export
            self.log_audit_event(
                action='data_exported',
                resource_type='DataExport',
                resource_id=None,
                user=request.user,
                details={
                    'export_type': export_type,
                    'format_type': format_type,
                    'date_range': f"{date_from} to {date_to}" if date_from and date_to else 'all',
                    'analyst_user': request.user.username
                }
            )
            
            if format_type in ['csv', 'xlsx', 'pdf']:
                # Return file download response
                response = Response(
                    export_data['file_content'],
                    content_type=export_data['content_type']
                )
                response['Content-Disposition'] = f'attachment; filename="{export_data["filename"]}"'
                return response
            else:
                # Return JSON data
                return Response({
                    'status': 'success',
                    'data': export_data
                })
                
        except Exception as e:
            logger.error(f"Data export failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Data export failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )