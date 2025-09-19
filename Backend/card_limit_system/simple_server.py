#!/usr/bin/env python3
"""
Simple HTTP Server for HDFC Card Limit System
This server provides API endpoints without requiring cx_Oracle dependency
Data is stored in JSON files and can be manually inserted into Oracle
"""

import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import uuid

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class HDFCAPIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.data_dir = "api_data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        super().__init__(*args, **kwargs)

    def _set_cors_headers(self):
        """Set CORS headers for browser compatibility"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def _send_json_response(self, data, status_code=200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _save_data(self, filename, data):
        """Save data to JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        existing_data = []
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    existing_data = json.load(f)
            except:
                existing_data = []
        
        existing_data.append(data)
        
        with open(filepath, 'w') as f:
            json.dump(existing_data, f, indent=2)

    def _load_data(self, filename):
        """Load data from JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        try:
            if path == '/api/health/':
                self._send_json_response({
                    'status': 'healthy',
                    'message': 'HDFC Card Limit System API is running',
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0.0'
                })

            elif path == '/api/limit-requests/recent/':
                requests = self._load_data('limit_requests.json')
                # Return last 10 requests
                recent_requests = requests[-10:] if len(requests) > 10 else requests
                self._send_json_response({
                    'status': 'success',
                    'data': recent_requests,
                    'count': len(recent_requests)
                })

            elif path.startswith('/api/limit-requests/') and path.endswith('/status/'):
                # Extract request ID from path
                request_id = path.split('/')[-2]
                requests = self._load_data('limit_requests.json')
                
                request_data = None
                for req in requests:
                    if req.get('id') == request_id:
                        request_data = req
                        break
                
                if request_data:
                    self._send_json_response({
                        'status': 'success',
                        'data': {
                            'id': request_data['id'],
                            'status': request_data.get('status', 'pending'),
                            'last_updated': request_data.get('last_updated'),
                            'message': f"Request {request_id} is {request_data.get('status', 'pending')}"
                        }
                    })
                else:
                    self._send_json_response({
                        'status': 'error',
                        'message': 'Request not found'
                    }, 404)

            elif path == '/api/customers/':
                customers = self._load_data('customers.json')
                self._send_json_response({
                    'status': 'success',
                    'data': customers,
                    'count': len(customers)
                })

            else:
                self._send_json_response({
                    'status': 'error',
                    'message': 'Endpoint not found'
                }, 404)

        except Exception as e:
            print(f"Error in GET request: {e}")
            self._send_json_response({
                'status': 'error',
                'message': 'Internal server error'
            }, 500)

    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse JSON data
            try:
                data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                self._send_json_response({
                    'status': 'error',
                    'message': 'Invalid JSON data'
                }, 400)
                return

            if path == '/api/customers/':
                # Add customer data
                customer_data = {
                    'id': str(uuid.uuid4()),
                    'name': data.get('name'),
                    'email': data.get('email'),
                    'phone': data.get('phone'),
                    'customer_id': data.get('customer_id'),
                    'created_at': datetime.now().isoformat(),
                    'status': 'active'
                }
                
                self._save_data('customers.json', customer_data)
                
                # Generate Oracle INSERT statement
                oracle_insert = f"""
INSERT INTO customers (id, customer_id, name, email, phone, status, created_at) 
VALUES (
    '{customer_data['id']}',
    '{customer_data['customer_id']}',
    '{customer_data['name']}',
    '{customer_data['email']}',
    '{customer_data['phone']}',
    '{customer_data['status']}',
    TIMESTAMP '{customer_data['created_at']}'
);"""
                
                self._save_data('oracle_inserts.sql', {
                    'table': 'customers',
                    'sql': oracle_insert,
                    'timestamp': datetime.now().isoformat()
                })
                
                self._send_json_response({
                    'status': 'success',
                    'message': 'Customer data saved successfully',
                    'data': customer_data,
                    'oracle_insert': oracle_insert
                })

            elif path == '/api/limit-requests/':
                # Add limit request data
                request_data = {
                    'id': str(uuid.uuid4()),
                    'customer_id': data.get('customer_id'),
                    'customer_name': data.get('customer_name'),
                    'email': data.get('email'),
                    'phone': data.get('phone'),
                    'request_type': data.get('request_type', 'limit_increase'),
                    'current_limit': data.get('current_limit'),
                    'requested_limit': data.get('requested_limit'),
                    'reason': data.get('reason'),
                    'income_proof': data.get('income_proof'),
                    'status': 'pending',
                    'request_date': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
                
                self._save_data('limit_requests.json', request_data)
                
                # Generate Oracle INSERT statements
                customer_insert = f"""
INSERT INTO customers (id, customer_id, name, email, phone, status, created_at) 
VALUES (
    '{str(uuid.uuid4())}',
    '{request_data['customer_id']}',
    '{request_data['customer_name']}',
    '{request_data['email']}',
    '{request_data['phone']}',
    'active',
    TIMESTAMP '{request_data['request_date']}'
);"""

                request_insert = f"""
INSERT INTO limit_requests (id, customer_id, request_type, current_limit, requested_limit, reason, income_proof, status, request_date, last_updated) 
VALUES (
    '{request_data['id']}',
    '{request_data['customer_id']}',
    '{request_data['request_type']}',
    {request_data['current_limit']},
    {request_data['requested_limit']},
    '{request_data['reason']}',
    '{request_data.get('income_proof', '')}',
    '{request_data['status']}',
    TIMESTAMP '{request_data['request_date']}',
    TIMESTAMP '{request_data['last_updated']}'
);"""
                
                self._save_data('oracle_inserts.sql', {
                    'table': 'limit_requests',
                    'customer_sql': customer_insert,
                    'request_sql': request_insert,
                    'timestamp': datetime.now().isoformat()
                })
                
                self._send_json_response({
                    'status': 'success',
                    'message': 'Limit request submitted successfully',
                    'data': request_data,
                    'oracle_inserts': {
                        'customer': customer_insert,
                        'request': request_insert
                    }
                })

            else:
                self._send_json_response({
                    'status': 'error',
                    'message': 'Endpoint not found'
                }, 404)

        except Exception as e:
            print(f"Error in POST request: {e}")
            self._send_json_response({
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            }, 500)

    def log_message(self, format, *args):
        """Custom log message"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def run_server(port=8000):
    """Run the HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, HDFCAPIHandler)
    
    print(f"""
🚀 HDFC Card Limit System API Server Starting...

📍 Server Address: http://localhost:{port}
📋 API Endpoints:
   • Health Check: GET /api/health/
   • Submit Customer Data: POST /api/customers/
   • Submit Limit Request: POST /api/limit-requests/
   • Get Recent Requests: GET /api/limit-requests/recent/
   • Check Request Status: GET /api/limit-requests/{{id}}/status/

💾 Data Storage: JSON files in ./api_data/
🔗 Oracle Integration: SQL statements generated in ./api_data/oracle_inserts.sql

📱 Ready for Flutter App Connection!
🔍 Ready for Oracle SQL Developer Demo!

Press Ctrl+C to stop the server...
""")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server shutting down...")
        httpd.server_close()

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)