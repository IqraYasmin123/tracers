import 'package:flutter/material.dart';
import '../api/client.dart';
import 'cases_screen.dart';
import 'dashboard_screen.dart';
import 'investigation_screen.dart';
import 'settings_screen.dart';

class AppShell extends StatefulWidget {
  final ApiClient api;
  const AppShell({super.key, required this.api});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _index = 0;
  late final List<Widget> _tabs;

  @override
  void initState() {
    super.initState();
    _tabs = [
      DashboardScreen(api: widget.api),
      InvestigationScreen(api: widget.api),
      CasesScreen(api: widget.api),
      SettingsScreen(api: widget.api),
    ];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _index, children: _tabs),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.grid_view_outlined), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.search), label: 'Investigate'),
          NavigationDestination(icon: Icon(Icons.folder_outlined), label: 'Cases'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), label: 'Settings'),
        ],
      ),
    );
  }
}
