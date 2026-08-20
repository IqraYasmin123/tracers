import 'package:flutter/material.dart';
import '../api/client.dart';
import '../theme/theme.dart';

final _emailPattern = RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$');

class LoginScreen extends StatefulWidget {
  final ApiClient api;
  const LoginScreen({super.key, required this.api});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  String? _emailError;
  String? _passwordError;
  String? _loginError;
  bool _submitting = false;

  Future<void> _handleSubmit() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    setState(() {
      _emailError = email.isEmpty
          ? 'Enter your email.'
          : (!_emailPattern.hasMatch(email) ? 'Enter a valid email address.' : null);
      _passwordError = password.isEmpty
          ? 'Enter your password.'
          : (password.length < 8 ? 'Password must be at least 8 characters.' : null);
      _loginError = null;
    });

    if (_emailError != null || _passwordError != null) return;

    setState(() => _submitting = true);
    try {
      // Real authentication (Module 16): a real backend call, a real JWT stored via
      // ApiClient, not the placeholder that used to just navigate after a fake delay.
      await widget.api.login(email, password);
      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed('/dashboard');
    } catch (e) {
      if (!mounted) return;
      setState(() => _loginError = e is ApiException ? e.message : 'Could not sign in. Please try again.');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
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
                if (_loginError != null) ...[
                  const SizedBox(height: 12),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: TracerColors.verdictAdversarial.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(_loginError!, style: const TextStyle(color: TracerColors.verdictAdversarial)),
                  ),
                ],
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _submitting ? null : _handleSubmit,
                    child: Text(_submitting ? 'Signing in…' : 'Sign In'),
                  ),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Accounts are provisioned by an administrator — no public sign-up.',
                  style: TextStyle(color: TracerColors.muted, fontSize: 11),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
