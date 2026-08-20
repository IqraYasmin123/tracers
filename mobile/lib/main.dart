import 'package:flutter/material.dart';
import 'api/client.dart';
import 'screens/app_shell.dart';
import 'screens/login_screen.dart';
import 'theme/theme.dart';

void main() {
  runApp(const TracerApp());
}

class TracerApp extends StatelessWidget {
  const TracerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TRACER',
      debugShowCheckedModeBanner: false,
      theme: buildTracerTheme(),
      home: const _Bootstrap(),
    );
  }
}

/// Waits for ApiClient.create() (reads the saved backend URL from SharedPreferences)
/// before showing the first real screen, so Settings' saved URL is respected from the
/// very first frame rather than briefly showing the hardcoded default.
class _Bootstrap extends StatefulWidget {
  const _Bootstrap();

  @override
  State<_Bootstrap> createState() => _BootstrapState();
}

class _BootstrapState extends State<_Bootstrap> {
  late Future<_BootstrapResult> _bootstrapFuture;

  @override
  void initState() {
    super.initState();
    _bootstrapFuture = _bootstrap();
  }

  Future<_BootstrapResult> _bootstrap() async {
    final api = await ApiClient.create();
    // Mirrors AuthContext.jsx's refreshUser(): a stored token isn't the same as a valid
    // session — it could be expired, or the account could have been deleted since. Only
    // start on the app shell if /auth/me actually confirms the session is still good.
    final user = await api.getCurrentUserOrNull();
    return _BootstrapResult(api: api, startAuthenticated: user != null);
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_BootstrapResult>(
      future: _bootstrapFuture,
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const Scaffold(body: Center(child: CircularProgressIndicator()));
        }
        final result = snapshot.data!;
        return Navigator(
          onGenerateRoute: (settings) {
            Widget page;
            switch (settings.name) {
              case '/dashboard':
                page = AppShell(api: result.api);
                break;
              case '/':
              default:
                page = LoginScreen(api: result.api);
            }
            return MaterialPageRoute(builder: (_) => page, settings: settings);
          },
          initialRoute: result.startAuthenticated ? '/dashboard' : '/',
        );
      },
    );
  }
}

class _BootstrapResult {
  final ApiClient api;
  final bool startAuthenticated;
  _BootstrapResult({required this.api, required this.startAuthenticated});
}
