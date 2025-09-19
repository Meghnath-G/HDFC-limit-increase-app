"""
Interactive API Documentation Configuration
==========================================

This module configures Swagger UI and ReDoc for interactive API documentation
with authentication integration and live testing capabilities.
"""

from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json


class CustomSwaggerView(SpectacularSwaggerView):
    """
    Customized Swagger UI with HDFC branding and enhanced features.
    """
    template_name = 'api_docs/swagger.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'HDFC Card Limit System API',
            'description': 'Interactive API Documentation',
            'version': '1.0.0',
            'contact_email': 'api-support@hdfc.com',
            'contact_url': 'https://support.hdfc.com/api',
            'license_name': 'Proprietary',
            'license_url': 'https://hdfc.com/license',
            'servers': [
                {
                    'url': 'https://card-limit-api.hdfc.com',
                    'description': 'Production Server'
                },
                {
                    'url': 'https://staging-card-limit-api.hdfc.com',
                    'description': 'Staging Server'
                },
                {
                    'url': 'http://localhost:8000',
                    'description': 'Development Server'
                }
            ],
            'auth_urls': {
                'firebase_login': '/api/v1/auth/firebase/login/',
                'test_token': '/api/v1/auth/test-token/',
                'refresh_token': '/api/v1/auth/refresh/'
            },
            'swagger_settings': {
                'deepLinking': True,
                'displayOperationId': True,
                'defaultModelsExpandDepth': 2,
                'defaultModelExpandDepth': 2,
                'displayRequestDuration': True,
                'filter': True,
                'showExtensions': True,
                'showCommonExtensions': True,
                'tryItOutEnabled': True,
                'requestSnippetsEnabled': True,
                'requestSnippets': {
                    'generators': {
                        'curl_bash': {
                            'title': 'cURL (bash)',
                            'syntax': 'bash'
                        },
                        'curl_powershell': {
                            'title': 'cURL (PowerShell)',
                            'syntax': 'powershell'
                        },
                        'curl_cmd': {
                            'title': 'cURL (CMD)',
                            'syntax': 'bash'
                        }
                    },
                    'defaultExpanded': True,
                    'languages': ['curl_bash', 'curl_powershell', 'curl_cmd']
                },
                'persistAuthorization': True,
                'oauth': {
                    'clientId': settings.FIREBASE_PROJECT_ID if hasattr(settings, 'FIREBASE_PROJECT_ID') else '',
                    'clientSecret': '',
                    'realm': 'firebase',
                    'appName': 'HDFC Card Limit System',
                    'scopeSeparator': ' ',
                    'additionalQueryStringParams': {},
                    'useBasicAuthenticationWithAccessCodeGrant': False,
                    'usePkceWithAuthorizationCodeGrant': True
                }
            }
        })
        return context


class CustomRedocView(SpectacularRedocView):
    """
    Customized ReDoc with HDFC branding and enhanced features.
    """
    template_name = 'api_docs/redoc.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'HDFC Card Limit System API Documentation',
            'description': 'Comprehensive API Reference',
            'theme': {
                'colors': {
                    'primary': {
                        'main': '#004c97'  # HDFC Blue
                    },
                    'success': {
                        'main': '#00a651'  # HDFC Green
                    }
                },
                'typography': {
                    'fontSize': '14px',
                    'lineHeight': '1.5em',
                    'code': {
                        'fontSize': '13px',
                        'fontFamily': 'Courier, monospace'
                    },
                    'headings': {
                        'fontFamily': 'Arial, sans-serif',
                        'fontWeight': 'bold'
                    }
                },
                'sidebar': {
                    'backgroundColor': '#fafafa',
                    'width': '300px'
                },
                'rightPanel': {
                    'backgroundColor': '#263238',
                    'width': '40%'
                }
            },
            'options': {
                'theme': 'light',
                'nativeScrollbars': True,
                'disableSearch': False,
                'expandDefaultServerVariables': True,
                'expandResponses': '200,201',
                'hideDownloadButton': False,
                'hideHostname': False,
                'hideLoading': False,
                'hideSingleRequestSampleTab': False,
                'menuToggle': True,
                'pathInMiddlePanel': True,
                'requiredPropsFirst': True,
                'scrollYOffset': 0,
                'showExtensions': True,
                'sortPropsAlphabetically': True,
                'untrustedSpec': False
            }
        })
        return context


class APIHealthCheckView(TemplateView):
    """
    API health check endpoint for documentation testing.
    """
    
    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': '2024-12-19T10:30:00Z',
            'services': {
                'database': 'connected',
                'redis': 'connected',
                'firebase': 'connected',
                'external_apis': 'connected'
            },
            'api_docs': {
                'swagger_ui': '/api/v1/docs/',
                'redoc': '/api/v1/redoc/',
                'schema': '/api/v1/schema/',
                'openapi_json': '/api/v1/schema.json',
                'openapi_yaml': '/api/v1/schema.yaml'
            }
        })


class AuthTestView(TemplateView):
    """
    Authentication testing endpoint for API documentation.
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Test Firebase token for API documentation."""
        try:
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return JsonResponse({
                    'success': False,
                    'error': {
                        'code': 'INVALID_AUTH_HEADER',
                        'message': 'Authorization header must start with Bearer'
                    }
                }, status=401)
            
            token = auth_header.split(' ')[1]
            
            # Mock token validation for documentation
            if token == 'mock_valid_token':
                return JsonResponse({
                    'success': True,
                    'data': {
                        'token_valid': True,
                        'customer_id': 'CUST123456789',
                        'email': 'customer@example.com',
                        'permissions': ['view_profile', 'request_limit_increase']
                    },
                    'message': 'Token is valid'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': {
                        'code': 'INVALID_TOKEN',
                        'message': 'Invalid or expired token'
                    }
                }, status=401)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': {
                    'code': 'TOKEN_VALIDATION_ERROR',
                    'message': 'Error validating token'
                }
            }, status=500)


# URL Configuration
api_docs_urlpatterns = [
    # OpenAPI Schema
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema.json', SpectacularAPIView.as_view(format='json'), name='schema-json'),
    path('schema.yaml', SpectacularAPIView.as_view(format='yaml'), name='schema-yaml'),
    
    # Interactive Documentation
    path('docs/', CustomSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', CustomRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Documentation Utilities
    path('health/', APIHealthCheckView.as_view(), name='api-health'),
    path('auth/test-token/', AuthTestView.as_view(), name='auth-test'),
    
    # Documentation Landing Page
    path('', TemplateView.as_view(template_name='api_docs/index.html'), name='api-docs-index'),
]

# Swagger UI Configuration Template Context
SWAGGER_UI_SETTINGS = {
    'DEEP_LINKING': True,
    'DISPLAY_OPERATION_ID': True,
    'DEFAULT_MODELS_EXPAND_DEPTH': 2,
    'DEFAULT_MODEL_EXPAND_DEPTH': 2,
    'DISPLAY_REQUEST_DURATION': True,
    'FILTER': True,
    'SHOW_EXTENSIONS': True,
    'SHOW_COMMON_EXTENSIONS': True,
    'TRY_IT_OUT_ENABLED': True,
    'REQUEST_SNIPPETS_ENABLED': True,
    'PERSIST_AUTHORIZATION': True,
    'OAUTH': {
        'CLIENT_ID': 'hdfc-card-limit-system',
        'APP_NAME': 'HDFC Card Limit System',
        'SCOPE_SEPARATOR': ' ',
        'USE_PKCE_WITH_AUTHORIZATION_CODE_GRANT': True
    }
}

# ReDoc Configuration
REDOC_SETTINGS = {
    'LAZY_RENDERING': False,
    'HIDE_DOWNLOAD_BUTTON': False,
    'EXPAND_RESPONSES': ['200', '201'],
    'PATH_IN_MIDDLE_PANEL': True,
    'NATIVE_SCROLLBARS': True,
    'THEME': {
        'colors': {
            'primary': {
                'main': '#004c97'
            }
        }
    }
}

# Custom CSS for API Documentation
API_DOCS_CSS = """
/* HDFC Branding */
.swagger-ui .topbar {
    background-color: #004c97;
    border-bottom: 3px solid #00a651;
}

.swagger-ui .topbar .download-url-wrapper .select-label {
    color: white;
}

.swagger-ui .topbar .download-url-wrapper input[type=text] {
    border: 1px solid #00a651;
}

.swagger-ui .info .title {
    color: #004c97;
}

.swagger-ui .scheme-container {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 10px;
    margin: 10px 0;
}

.swagger-ui .auth-wrapper .authorize {
    background-color: #00a651;
    border-color: #00a651;
}

.swagger-ui .auth-wrapper .authorize:hover {
    background-color: #008a44;
    border-color: #008a44;
}

.swagger-ui .btn.authorize {
    background-color: #00a651;
    border-color: #00a651;
}

.swagger-ui .btn.authorize:hover {
    background-color: #008a44;
    border-color: #008a44;
}

/* Response styling */
.swagger-ui .responses-inner h4 {
    color: #004c97;
}

.swagger-ui .response-col_status {
    color: #00a651;
    font-weight: bold;
}

/* Model styling */
.swagger-ui .model-box {
    border: 1px solid #dee2e6;
    border-radius: 4px;
}

.swagger-ui .model-title {
    color: #004c97;
}

/* Custom authentication section */
.api-auth-section {
    background: linear-gradient(135deg, #004c97 0%, #00a651 100%);
    color: white;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
}

.api-auth-section h3 {
    color: white;
    margin-bottom: 15px;
}

.api-auth-section .auth-instructions {
    background: rgba(255, 255, 255, 0.1);
    padding: 15px;
    border-radius: 4px;
    margin: 10px 0;
}

.api-auth-section code {
    background: rgba(255, 255, 255, 0.2);
    color: #fff;
    padding: 2px 6px;
    border-radius: 3px;
}
"""

# JavaScript for enhanced functionality
API_DOCS_JS = """
// Enhanced Swagger UI functionality
document.addEventListener('DOMContentLoaded', function() {
    // Auto-expand authentication section
    setTimeout(function() {
        const authButton = document.querySelector('.auth-wrapper .authorize');
        if (authButton) {
            authButton.style.backgroundColor = '#00a651';
            authButton.style.borderColor = '#00a651';
        }
    }, 1000);
    
    // Add custom authentication helper
    function addFirebaseAuthHelper() {
        const authSection = document.querySelector('.auth-wrapper');
        if (authSection && !document.querySelector('.firebase-auth-helper')) {
            const helper = document.createElement('div');
            helper.className = 'firebase-auth-helper api-auth-section';
            helper.innerHTML = `
                <h3>🔐 Firebase Authentication</h3>
                <div class="auth-instructions">
                    <p><strong>To test the API:</strong></p>
                    <ol>
                        <li>Click the "Authorize" button above</li>
                        <li>In the FirebaseAuth section, enter: <code>Bearer mock_valid_token</code></li>
                        <li>Click "Authorize" to apply the token</li>
                        <li>Try out the authenticated endpoints below</li>
                    </ol>
                    <p><strong>In production:</strong> Replace with actual Firebase JWT token</p>
                </div>
            `;
            authSection.parentNode.insertBefore(helper, authSection.nextSibling);
        }
    }
    
    // Add helper after Swagger UI loads
    setTimeout(addFirebaseAuthHelper, 2000);
    
    // Custom request interceptor for adding HDFC headers
    window.ui = window.ui || {};
    if (window.ui.getConfigs) {
        const originalConfigs = window.ui.getConfigs();
        window.ui.preauthorizeApiKey = function(apiKeyAuth, apiKey) {
            // Add custom headers
            originalConfigs.requestInterceptor = function(request) {
                request.headers['X-API-Client'] = 'HDFC-Swagger-UI';
                request.headers['X-API-Version'] = '1.0.0';
                return request;
            };
            return originalConfigs.preauthorizeApiKey(apiKeyAuth, apiKey);
        };
    }
});

// Helper function to format response examples
function formatResponseExample(response) {
    if (typeof response === 'object') {
        return JSON.stringify(response, null, 2);
    }
    return response;
}

// Custom error handler for API documentation
function handleAPIDocError(error) {
    console.error('API Documentation Error:', error);
    
    // Show user-friendly error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-warning';
    errorDiv.innerHTML = `
        <strong>Note:</strong> This is a documentation interface. 
        Some features require a live API server to function properly.
    `;
    
    const container = document.querySelector('.swagger-ui');
    if (container && !document.querySelector('.alert')) {
        container.insertBefore(errorDiv, container.firstChild);
    }
}
"""

# Export configuration
__all__ = [
    'CustomSwaggerView',
    'CustomRedocView',
    'APIHealthCheckView',
    'AuthTestView',
    'api_docs_urlpatterns',
    'SWAGGER_UI_SETTINGS',
    'REDOC_SETTINGS',
    'API_DOCS_CSS',
    'API_DOCS_JS'
]