import 'package:flutter/material.dart';
import '../theme/theme.dart';

final _emailPattern = RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$');

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  String? _emailError;
  String? _passwordError;
  bool _submitting = false;

  void _handleSubmit() {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    setState(() {
      _emailError = email.isEmpty
          ? 'Enter your email.'
          : (!_emailPattern.hasMatch(email) ? 'Enter a valid email address.' : null);
      _passwordError = password.isEmpty
          ? 'Enter your password.'
          : (password.length < 8 ? 'Password must be at least 8 characters.' : null);
    });

    if (_emailError != null || _passwordError != null) return;

    // Real authentication (JWT issued by the backend) arrives in Module 16. This validates
    // real input honestly and then proceeds — matching frontend/src/pages/Login.jsx's own
    // comment on why this isn't wired to a fake "always succeeds" backend call.
    setState(() => _submitting = true);
    Future.delayed(const Duration(milliseconds: 400), () {
      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed('/dashboard');
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 360),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'TRACER',
                  style: TextStyle(
                    color: TracerColors.cyan,
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1.5,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Digital forensics for Vision-Language Models',
                  style: TextStyle(color: TracerColors.muted, fontSize: 13),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),
                TextField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  decoration: InputDecoration(labelText: 'Email', errorText: _emailError),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: InputDecoration(labelText: 'Password', errorText: _passwordError),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _submitting ? null : _handleSubmit,
                    child: Text(_submitting ? 'Signing in…' : 'Sign In'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
