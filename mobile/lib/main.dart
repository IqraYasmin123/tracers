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
  late Future<ApiClient> _apiFuture;

  @override
  void initState() {
    super.initState();
    _apiFuture = ApiClient.create();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ApiClient>(
      future: _apiFuture,
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const Scaffold(body: Center(child: CircularProgressIndicator()));
        }
        final api = snapshot.data!;
        return Navigator(
          onGenerateRoute: (settings) {
            Widget page;
            switch (settings.name) {
              case '/dashboard':
                page = AppShell(api: api);
                break;
              case '/':
              default:
                page = const LoginScreen();
            }
            return MaterialPageRoute(builder: (_) => page, settings: settings);
          },
        );
      },
    );
  }
}
