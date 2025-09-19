// HDFC Card Limit System - API Configuration for Flutter
// Add this to your Flutter project in lib/services/api_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://localhost:8000/api';
  
  // Headers for all requests
  static const Map<String, String> headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  // Health check endpoint
  static Future<Map<String, dynamic>> checkHealth() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/health/'),
        headers: headers,
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Server health check failed');
      }
    } catch (e) {
      throw Exception('Failed to connect to server: $e');
    }
  }

  // Submit customer data
  static Future<Map<String, dynamic>> submitCustomerData({
    required String name,
    required String email,
    required String phone,
    required String customerId,
  }) async {
    try {
      final Map<String, dynamic> data = {
        'name': name,
        'email': email,
        'phone': phone,
        'customer_id': customerId,
      };

      final response = await http.post(
        Uri.parse('$baseUrl/customers/'),
        headers: headers,
        body: json.encode(data),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to submit customer data');
      }
    } catch (e) {
      throw Exception('Error submitting customer data: $e');
    }
  }

  // Submit limit request
  static Future<Map<String, dynamic>> submitLimitRequest({
    required String customerId,
    required String customerName,
    required String email,
    required String phone,
    required String requestType,
    required double currentLimit,
    required double requestedLimit,
    required String reason,
    String? incomeProof,
  }) async {
    try {
      final Map<String, dynamic> data = {
        'customer_id': customerId,
        'customer_name': customerName,
        'email': email,
        'phone': phone,
        'request_type': requestType,
        'current_limit': currentLimit,
        'requested_limit': requestedLimit,
        'reason': reason,
        'income_proof': incomeProof ?? '',
      };

      final response = await http.post(
        Uri.parse('$baseUrl/limit-requests/'),
        headers: headers,
        body: json.encode(data),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to submit limit request');
      }
    } catch (e) {
      throw Exception('Error submitting limit request: $e');
    }
  }

  // Get recent requests
  static Future<Map<String, dynamic>> getRecentRequests() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/limit-requests/recent/'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get recent requests');
      }
    } catch (e) {
      throw Exception('Error getting recent requests: $e');
    }
  }

  // Check request status
  static Future<Map<String, dynamic>> checkRequestStatus(String requestId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/limit-requests/$requestId/status/'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to check request status');
      }
    } catch (e) {
      throw Exception('Error checking request status: $e');
    }
  }
}

// Example usage in a Flutter widget:
/*
class LimitRequestForm extends StatefulWidget {
  @override
  _LimitRequestFormState createState() => _LimitRequestFormState();
}

class _LimitRequestFormState extends State<LimitRequestForm> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _customerIdController = TextEditingController();
  final _currentLimitController = TextEditingController();
  final _requestedLimitController = TextEditingController();
  final _reasonController = TextEditingController();

  Future<void> _submitRequest() async {
    if (_formKey.currentState!.validate()) {
      try {
        // First submit customer data
        await ApiService.submitCustomerData(
          name: _nameController.text,
          email: _emailController.text,
          phone: _phoneController.text,
          customerId: _customerIdController.text,
        );

        // Then submit limit request
        final result = await ApiService.submitLimitRequest(
          customerId: _customerIdController.text,
          customerName: _nameController.text,
          email: _emailController.text,
          phone: _phoneController.text,
          requestType: 'limit_increase',
          currentLimit: double.parse(_currentLimitController.text),
          requestedLimit: double.parse(_requestedLimitController.text),
          reason: _reasonController.text,
        );

        // Show success message
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Request submitted successfully! ID: ${result['data']['id']}'),
            backgroundColor: Colors.green,
          ),
        );

        // Clear form
        _formKey.currentState!.reset();
        
      } catch (e) {
        // Show error message
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('HDFC Card Limit Request'),
      ),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              TextFormField(
                controller: _nameController,
                decoration: InputDecoration(labelText: 'Full Name'),
                validator: (value) => value!.isEmpty ? 'Please enter your name' : null,
              ),
              TextFormField(
                controller: _emailController,
                decoration: InputDecoration(labelText: 'Email'),
                validator: (value) => value!.isEmpty ? 'Please enter your email' : null,
              ),
              TextFormField(
                controller: _phoneController,
                decoration: InputDecoration(labelText: 'Phone Number'),
                validator: (value) => value!.isEmpty ? 'Please enter your phone' : null,
              ),
              TextFormField(
                controller: _customerIdController,
                decoration: InputDecoration(labelText: 'Customer ID'),
                validator: (value) => value!.isEmpty ? 'Please enter customer ID' : null,
              ),
              TextFormField(
                controller: _currentLimitController,
                decoration: InputDecoration(labelText: 'Current Limit'),
                keyboardType: TextInputType.number,
                validator: (value) => value!.isEmpty ? 'Please enter current limit' : null,
              ),
              TextFormField(
                controller: _requestedLimitController,
                decoration: InputDecoration(labelText: 'Requested Limit'),
                keyboardType: TextInputType.number,
                validator: (value) => value!.isEmpty ? 'Please enter requested limit' : null,
              ),
              TextFormField(
                controller: _reasonController,
                decoration: InputDecoration(labelText: 'Reason for Increase'),
                maxLines: 3,
                validator: (value) => value!.isEmpty ? 'Please enter reason' : null,
              ),
              SizedBox(height: 20),
              ElevatedButton(
                onPressed: _submitRequest,
                child: Text('Submit Request'),
                style: ElevatedButton.styleFrom(
                  padding: EdgeInsets.symmetric(horizontal: 40, vertical: 15),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
*/